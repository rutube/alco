# coding: utf-8

# $Id: $


import time
import json
import sys

import dateutil.parser
from django.core.signals import request_started, request_finished
from django.db import connections
from django.utils import six
import redis
from amqp import Connection
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

    def cancel(self):
        self.cancelled = True

    def connect(self):
        self.amqp = Connection(**ALCO_SETTINGS['RABBITMQ'])
        self.redis = redis.Redis(**ALCO_SETTINGS['REDIS'])
        self.conn = connections[ALCO_SETTINGS['SPHINX_DATABASE_NAME']]

    def __call__(self, *args, **kwargs):
        try:
            self.connect()
            self.declare_queue()
            channel = self.amqp.channel()
            channel.basic_consume(self.index.queue_name,
                                  callback=self.process_message, no_ack=True)
            start = time.time()
            while not self.cancelled:
                channel.wait()
                if time.time() - start > 1:
                    self.push_messages()
                    start = time.time()
        except KeyboardInterrupt:
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
            'js': json.dumps(data),
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
        channel.exchange_declare(exchange=self.exchange, type='topic',
                                 durable=True, auto_delete=False)
        channel.queue_declare(self.index.queue_name, durable=True,
                              auto_delete=False)
        channel.queue_bind(self.index.queue_name,
                           exchange=self.exchange,
                           routing_key=self.index.routing_key)

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
        key = keys.KEY_SEQUENCE.format(index=self.index.name)
        max_pk = self.redis.incrby(key, len(messages))
        min_pk = max_pk - len(messages)

        columns = dict()

        suffix = self.current_date.strftime("%Y%m%d")
        name = "%s_%s" % (self.index.name, suffix)
        query = "REPLACE INTO %s (id, ts, ms, seq, js, logline) VALUES " % name
        rows = []
        args = []
        for pk, data in zip(range(min_pk, max_pk), messages):
            # saving seen columns to LoggerColumn model, collecting unique
            # values for caching in redis
            for key, value in data['data'].items():
                columns.setdefault(key, set())
                if not isinstance(value, (bool, int, float, six.text_type)):
                    continue
                columns[key].add(value)

            rows.append("(%s, %s, %s, %s, %s, %s)")
            args.extend((pk, data['ts'], data['ms'], data['seq'], data['js'],
                         data['message']))
        query += ','.join(rows)

        existing = self.index.loggercolumn_set.all()
        filtered = filter(lambda c: c.filtered, existing)

        existing = [c.name for c in existing]
        filtered = [c.name for c in filtered]
        new_values = set(columns.keys()) - set(existing)

        for column in filtered:
            values = columns.get(column)
            if not values:
                continue
            key = keys.KEY_COLUMN_VALUES.format(index=self.index.name,
                                                column=column)
            self.redis.sadd(key, *values)

        for column in new_values:
            self.index.loggercolumn_set.create(name=column)

        for _ in range(3):
            try:
                c = self.conn.cursor()
                c.execute(query, args)
                print(c.rowcount)
                c.close()
            except Exception as e:
                pass
            else:
                break




