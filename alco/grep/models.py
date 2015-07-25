# coding: utf-8

# $Id: $
import time
from datetime import datetime
from django.db import models
from jsonfield import JSONField

from sphinxsearch.models import SphinxModel, SphinxDateTimeField
from alco.collector.models import LoggerIndex


class LogBase(SphinxModel):
    class Meta:
        abstract = True
        ordering = ('ts', 'seq')
        db_table = 'logger'

    ts = SphinxDateTimeField()
    ms = models.IntegerField()
    seq = models.BigIntegerField()
    logline = models.TextField()
    js = JSONField()

    @property
    def datetime(self):
        return self.ts.replace(microsecond=self.ms)

    @property
    def timestamp(self):
        return time.mktime(self.datetime.timetuple())

def create_char_field(c):
    return models.CharField(max_length=255, db_column='js.%s' % c)


def create_index_model(index):
    model_name = "%sLog" % index.name.title()
    class Meta:
        db_table = index.name

    columns = index.loggercolumn_set.values_list('name', flat=True)

    fields = {c: create_char_field(c) for c in columns}
    fields.update({'Meta': Meta, '__module__': __name__})
    Log = type(model_name, (LogBase,), fields)
    return Log
