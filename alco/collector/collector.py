# coding: utf-8

# $Id: $


import time
import json
import sys
from collections import defaultdict
from random import randint
from logging import getLogger

import dateutil.parser
from django.core.signals import request_started, request_finished
from django.db import connections, DatabaseError
from django.utils import six
import redis
from amqp import Connection
from pyrabbit.api import Client

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

    def cancel(self):
        self.cancelled = True

    def connect(self):
        rabbitmq = ALCO_SETTINGS['RABBITMQ']
        self.amqp = Connection(**rabbitmq)
        self.redis = redis.Redis(**ALCO_SETTINGS['REDIS'])
        self.conn = connections[ALCO_SETTINGS['SPHINX_DATABASE_NAME']]
        hostname = '%s:%s' % (rabbitmq['host'],
                              ALCO_SETTINGS['RABBITMQ_API_PORT'])
        self.rabbit = Client(hostname, rabbitmq['userid'], rabbitmq['password'])
        self.vhost = rabbitmq['virtual_host']

    def __call__(self):
        try:
            self.logger.debug("Connecting to RabbitMQ")
            self.connect()
            self.declare_queue()
            self.cleanup_bindings()
            channel = self.amqp.channel()
            channel.basic_consume(self.index.queue_name,
                                  callback=self.process_message, no_ack=True)
            start = time.time()
            self.logger.debug("Start processing messages")
            while not self.cancelled:
                channel.wait()
                if time.time() - start > 1:
                    self.push_messages()
                    start = time.time()
        except KeyboardInterrupt:
            self.logger.warning("Got SIGINT, exit(0)")
            self.amqp.close()
            sys.exit(0)

    def process_message(self, msg):
        js = msg.body.decode("utf-8")
        data = json.loads(js)
        ts = data.pop('@timestamp')
        data.pop("@version")
        msg = data.pop('message')
        seq = data.pop('seq', 0)
        dt = dateutil.parser.parse(ts)
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
        finally:
            request_finished.send(None)

    def _push_messages(self):
        messages, self.messages = self.messages, []
        if not messages:
            return
        self.logger.info("Saving %s events" % len(messages))
        columns = defaultdict(set)
        suffix = self.current_date.strftime("%Y%m%d")
        name = "%s_%s" % (self.index.name, suffix)
        query = "REPLACE INTO %s (id, js, logline) VALUES " % name
        rows = []
        args = []
        # all defined columns
        all_columns = list(self.index.loggercolumn_set.all())
        indexed_columns = [c for c in all_columns if not c.excluded]
        filtered_columns = [c for c in indexed_columns if c.filtered]

        indexed = [c.name for c in indexed_columns]
        filtered = [c.name for c in filtered_columns]
        seen = set()
        pkeys = self.get_primary_keys(messages)
        for pk, data in zip(pkeys, messages):
            # saving seen columns to LoggerColumn model, collecting unique
            # values for caching in redis
            self.process_js_columns(data, columns, indexed, seen)
            data['js'] = json.dumps(data['data'])
            rows.append("(%s, %s, %s)")
            args.extend((pk, data['js'],
                         data['message']))
        query += ','.join(rows)

        self.logger.debug("Check for new columns")

        new_values = seen - set(indexed)

        self.logger.debug("Saving values for filtered columns")
        for column in filtered:
            values = columns.get(column)
            if not values:
                continue
            key = keys.KEY_COLUMN_VALUES.format(index=self.index.name,
                                                column=column)
            self.redis.sadd(key, *values)

        for column in new_values:
            self.logger.debug("Register column %s" % column)
            self.index.loggercolumn_set.create(name=column)

        self.logger.debug("Inserting logs to searchd")
        for _ in 1, 2, 3:
            try:
                c = self.conn.cursor()
                c.execute(query, args)
                self.logger.debug("%s rows inserted" % c.rowcount)
                c.close()
            except DatabaseError:
                self.logger.exception("Can't insert values to index")
            else:
                break

    @staticmethod
    def process_js_columns(data, columns, indexed, seen):
        for key, value in data['data'].items():
            if key in ('pk', 'id', 'ts', 'ms', 'seq'):
                # reserved by Django and ALCO
                data['data'].pop(key)
                continue
            # save seen columns set
            seen.add(key)
            if key not in indexed:
                # discard fields excluded from indexing
                data['data'].pop(key)
                continue
            # save column values set
            if not isinstance(value, (bool, int, float, six.text_type)):
                continue
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
