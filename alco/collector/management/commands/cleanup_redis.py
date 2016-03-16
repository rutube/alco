# coding: utf-8

# $Id: $
from logging import getLogger

import redis
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

    def cleanup_column(self, Log, column):
        self.logger.debug("Cleanup column %s@%s" %
                          (column.name, column.index.name))

        key = keys.KEY_COLUMN_VALUES.format(index=column.index.name,
                                            column=column.name)

        cached = self.redis.smembers(key)

        existing = list(
            Log.objects.values_list(column.name, flat=True).group_by(
                column.name).options(max_matches=10000)[:10000])

        self.logger.debug("existing: %s, cached: %s" %
                          (len(existing), len(cached)))

        to_remove = set(map(str, cached)) - set(map(str, existing))
        if to_remove:
            self.logger.debug("Removing %s from %s" % (to_remove, column.name))
            self.redis.srem(key, *to_remove)

    def cleanup_index(self, index):
        self.logger.debug("Cleanup index %s" % index.name)
        Log = create_index_model(index)
        for column in index.loggercolumn_set.filter(filtered=True):
            self.cleanup_column(Log, column)
