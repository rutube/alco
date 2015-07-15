# coding: utf-8

# $Id: $


import dateutil.parser
import time
import json
from django.db import connections
import redis
from amqp import Connection
from django.conf import settings
import sys


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
        self.amqp = Connection(settings.RABBITMQ_HOST)
        self.redis = redis.Redis(settings.REDIS_HOST, db=settings.REDIS_DB)
        self.conn = connections[settings.SPHINX_DATABASE_NAME]

    def __call__(self, *args, **kwargs):
        try:
            self.connect()
            self.declare_queue()
            channel = self.amqp.channel()
            channel.basic_consume("logstash", callback=self.process_message, no_ack=True)
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
        dt = dateutil.parser.parse(ts)
        result = {
            'ts': time.mktime(dt.timetuple()),
            'message': msg,
            'js': json.dumps(data)
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
        channel.exchange_declare(exchange=self.exchange, type='fanout',
                                 durable=True, auto_delete=False)
        channel.queue_declare(self.index.queue_name, durable=True,
                              auto_delete=False)
        channel.queue_bind(self.index.queue_name,
                           exchange=self.exchange,
                           routing_key=self.index.routing_key)

    def push_messages(self):
        messages, self.messages = self.messages, []
        if not messages:
            return
        max_pk = self.redis.incrby("logstash_id", len(messages))
        min_pk = max_pk - len(messages)

        suffix = self.current_date.strftime("%Y%m%d")
        name = "%s_%s" % (self.index.name, suffix)
        query = "REPLACE INTO %s (id, ts, js, logline) VALUES " % name
        rows = []
        args = []
        for pk, data in zip(range(min_pk, max_pk), messages):
            rows.append("(%s, %s, %s, %s)")
            args.extend((pk, data['ts'], data['js'], data['message']))
        query += ','.join(rows)

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




