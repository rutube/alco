# coding: utf-8

# $Id: $
from logging import getLogger

import redis
import time
from django.core.management import BaseCommand

from alco.collector import keys
from alco.collector.defaults import ALCO_SETTINGS
from alco.collector.models import LoggerIndex
from alco.grep.models import create_index_model


class Command(BaseCommand):
    """ Cleanup values for filtered columns from redis no more present in index.
    """
    logger = getLogger('alco.collector.cleanup_redis')
    redis = redis.Redis(**ALCO_SETTINGS['REDIS'])

    def handle(self, *args, **options):
        for index in LoggerIndex.objects.all():
            self.cleanup_index(index)

    def cleanup_column(self, Log, column, ts):
        self.logger.debug("Cleanup column %s@%s" %
                          (column.name, column.index.name))

        key = keys.KEY_COLUMN_VALUES.format(index=column.index.name,
                                            column=column.name)

        n = self.redis.zremrangebyscore(key, '-inf', ts)
        self.logger.debug("removed %s values" % n)

    def cleanup_index(self, index):
        self.logger.debug("Cleanup index %s" % index.name)
        Log = create_index_model(index)
        for column in index.loggercolumn_set.filter(filtered=True):
            first_day = index.index_dates[0]
            ts = time.mktime(first_day.timetuple())

            self.cleanup_column(Log, column, ts)
