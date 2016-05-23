# coding: utf-8

# $Id: $
import os
import signal
import socket
import sys
import time
import ujson as json
from collections import defaultdict
from datetime import datetime
from logging import getLogger
from random import randint
from threading import Thread

import redis
from django.conf import settings
from django.core.signals import request_started, request_finished
from django.db import connections, DatabaseError, ProgrammingError, close_old_connections
from django.utils import six
from librabbitmq import Connection
from pyrabbit.api import Client

# noinspection PyUnresolvedReferences
from six.moves import queue

from alco.collector.defaults import ALCO_SETTINGS
from alco.collector import keys


class Collector(object):

    def __init__(self, index):
        self.index = index
        self.cancelled = False
        self.transport = self.protocol = None
        self.messages = []
        self.block_size = 1000
        self.exchange = "logstash"
        self.current_date = None
        self.logger = getLogger('alco.collector.%s' % self.index.name)
        self.amqp = self.redis = self.conn = self.vhost = self.rabbit = None
        self.insert_thread = None
        self.query_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.result_queue.put(None)
        self.query = self.values_stub = None
        self.existing = self.included = self.indexed = self.filtered = None

    def cancel(self):
        self.cancelled = True

    def inserter_loop(self):
        self.conn = connections[ALCO_SETTINGS['SPHINX_DATABASE_NAME']]
        while not self.cancelled:
            try:
                query, args = self.query_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue
            result = self.insert_data(query, args)
            self.result_queue.put(result)

    def connect(self):
        connections['default'].close()
        rabbitmq = ALCO_SETTINGS['RABBITMQ']
        self.amqp = Connection(**rabbitmq)
        self.redis = redis.Redis(**ALCO_SETTINGS['REDIS'])
        self.insert_thread = Thread(target=self.inserter_loop)
        self.insert_thread.start()
        hostname = '%s:%s' % (rabbitmq['host'],
                              ALCO_SETTINGS['RABBITMQ_API_PORT'])
        self.rabbit = Client(hostname, rabbitmq['userid'], rabbitmq['password'])
        self.vhost = rabbitmq['virtual_host']

    # noinspection PyUnusedLocal
    def process_sigint(self, signum, frame):
        self.logger.info("Got signal %s" % signum)
        self.cancel()
        self.logger.info("Futures cancelled, wait for thread")
        self.insert_thread.join()
        self.logger.info("Thread done")

    def __call__(self):
        signal.signal(signal.SIGINT, self.process_sigint)
        signal.signal(signal.SIGTERM, self.process_sigint)

        try:
            self.logger.debug("Connecting to RabbitMQ")
            self.connect()
            self.declare_queue()
            self.cleanup_bindings()
            channel = self.amqp.channel()
            channel.basic_qos(0, 1000, False)
            channel.basic_consume(self.index.queue_name,
                                  callback=self.process_message, no_ack=True)
            start = time.time()
            self.logger.debug("Start processing messages")
            while not self.cancelled:
                try:
                    self.amqp.drain_events(timeout=1)
                except (socket.timeout, OSError):
                    pass
                if time.time() - start > 1:
                    self.push_messages()
                    start = time.time()
        except KeyboardInterrupt:
            self.logger.warning("Got SIGINT, exit(0)")
        finally:
            self.amqp.close()
            sys.exit(0)

    def process_message(self, msg):
        data = json.loads(six.binary_type(msg.body))
        ts = data.pop('@timestamp')
        data.pop("@version")
        msg = data.pop('message')
        seq = data.pop('seq', 0)
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
        result = {
            'ts': time.mktime(dt.timetuple()),
            'ms': dt.microsecond,
            'seq': seq,
            'message': msg,
            'data': data
        }
        self.messages.append(result)
        d = dt.date()
        if not self.current_date:
            self.current_date = d
        if d != self.current_date:
            self.current_date = d
            self.push_messages()
        if len(self.messages) >= self.block_size:
            self.push_messages()

    def declare_queue(self):
        channel = self.amqp.channel()
        """:type channel: amqp.channel.Channel"""
        durable = self.index.durable
        channel.exchange_declare(exchange=self.exchange, type='topic',
                                 durable=durable, auto_delete=False)
        channel.queue_declare(self.index.queue_name, durable=durable,
                              auto_delete=False)
        for rk in self.get_routing_keys():
            channel.queue_bind(self.index.queue_name, exchange=self.exchange,
                               routing_key=rk)

    def get_routing_keys(self):
        return map(lambda x: x.strip(), self.index.routing_key.split(','))

    def cleanup_bindings(self):
        self.logger.debug("Checking bindings")
        queue = self.index.queue_name
        exchange = self.exchange
        bindings = self.rabbit.get_queue_bindings(self.vhost, queue)
        bindings = [b for b in bindings if b['source'] == exchange]
        allowed = self.get_routing_keys()
        q = six.moves.urllib.parse.quote
        for b in bindings:
            rk = b['routing_key']
            if rk in allowed:
                continue
            self.logger.debug("Unbind %s with RK=%s" % (queue, rk))
            self.rabbit.delete_binding(self.vhost, exchange, q(queue), q(rk))

    def push_messages(self):
        try:
            request_started.send(None, environ=None)
            self._push_messages()
        except Exception as e:
            self.logger.exception(e)
            raise
        finally:
            request_finished.send(None)

    def _push_messages(self):
        messages, self.messages = self.messages, []
        if not messages:
            return
        message_count = len(messages)
        self.logger.info("Saving %s events" % message_count)
        columns = defaultdict(set)
        suffix = self.current_date.strftime("%Y%m%d")
        name = "%s_%s" % (self.index.name, suffix)
        args = []
        self.load_index_columns()
        self.prepare_query(name)

        pkeys = self.get_primary_keys(messages)
        seen = set()

        for pk, data in zip(pkeys, messages):
            # saving seen columns to LoggerColumn model, collecting unique
            # values for caching in redis

            js = data['data']
            self.process_js_columns(js, columns, self.included, seen)
            js_str = json.dumps(js)
            values = tuple(js.get(c) or '' for c in self.indexed)
            args.extend((pk, js_str, data['message']) + values)

        query = self.query + ','.join([self.values_stub] * message_count)

        self.save_column_values(columns)

        self.save_new_columns(seen)
        if self.result_queue.empty():
            self.logger.debug("Insert still running, waiting")
            while not self.cancelled:
                try:
                    self.result_queue.get(block=True, timeout=1)
                except queue.Empty:
                    continue

        self.query_queue.put((query, args))

    def insert_data(self, query, args):
        self.logger.debug("Inserting logs to searchd")
        result = None
        for _ in 1, 2, 3:
            try:
                c = self.conn.cursor()
                result = c.execute(query, args)
                self.logger.debug("%s rows inserted" % c.rowcount)
                c.close()
            except ProgrammingError:
                self.logger.exception(
                    "Can't insert values to index: %s" % query)
            except DatabaseError as e:
                self.logger.exception("Sphinx connection error: %s" % e)
                try:
                    close_old_connections()
                except Exception as e:
                    self.logger.exception("Can't reconnect: %s" % e)
                    os.kill(os.getpid(), signal.SIGKILL)
            except Exception:
                self.logger.exception("Unhandled error in insert_data")
            else:
                return result
        self.logger.error("Can't insert data in 3 tries, exit process")
        os.kill(os.getpid(), signal.SIGKILL)

    def save_new_columns(self, seen):
        self.logger.debug("Check for new columns")
        for column in seen - set(self.existing):
            self.logger.debug("Register column %s" % column)
            self.index.loggercolumn_set.create(name=column)

    def save_column_values(self, columns):
        self.logger.debug("Saving values for filtered columns")
        ts = time.time()
        for column in self.filtered:
            values = columns.get(column)
            if not values:
                continue
            key = keys.KEY_COLUMN_VALUES.format(index=self.index.name,
                                                column=column)
            values = {v: ts for v in values}
            self.redis.zadd(key, **values)

    def prepare_query(self, name):
        if self.indexed:
            self.query = "REPLACE INTO %s (id, js, logline, %s) VALUES " % (
                name, ', '.join(self.indexed))
        else:
            self.query = "REPLACE INTO %s (id, js, logline) VALUES " % name

        sql_col_count = len(self.indexed) + 3  # + jd, js, logline
        self.values_stub = "(%s)" % ", ".join(["%s"] * sql_col_count)

    def load_index_columns(self):
        # all defined columns
        all_columns = list(self.index.loggercolumn_set.all())
        included_columns = [c for c in all_columns if not c.excluded]
        filtered_columns = [c for c in included_columns if c.filtered]
        indexed_columns = [c for c in included_columns if c.indexed]
        self.existing = [c.name for c in all_columns]
        self.included = [c.name for c in included_columns]
        self.filtered = [c.name for c in filtered_columns]
        self.indexed = [c.name for c in indexed_columns]

    @staticmethod
    def process_js_columns(js, columns, included, seen):
        for key, value in list(js.items()):
            if key in ('pk', 'id', 'ts', 'ms', 'seq', 'model'):
                # escape fields reserved by Django and ALCO
                js['%s_x' % key] = js.pop(key)
                key = '%s_x' % key
            # save seen columns set
            if key not in seen:
                seen.add(key)
            if key not in included:
                # discard fields excluded from indexing
                js.pop(key)
                continue
            # save column values set
            if type(value) not in (bool, int, float, six.text_type):
                continue
            if value not in columns[key]:
                columns[key].add(value)

    def get_primary_keys(self, messages):
        """ Generate PK sequence for a list of messages."""
        pkeys = []
        pk = None
        for msg in messages:
            # pk is [timestamp][microseconds][randint] in 10based integer
            pk = int((msg['ts'] * 10**6 + msg['ms']) * 1000) + randint(0, 1000)
            pkeys.append(pk)
        self.logger.debug("first pk is %s" % pk)
        return pkeys
