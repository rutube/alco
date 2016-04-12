# coding: utf-8

# $Id: $
import time
from datetime import datetime
from django.db import models
from jsonfield import JSONField

from sphinxsearch.models import SphinxModel, SphinxField
from alco.collector.models import LoggerIndex, LoggerColumn


class Shortcut(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    description = models.CharField(max_length=255, blank=True, default='')
    url = models.CharField(max_length=255)
    index = models.ForeignKey(LoggerIndex)
    default_field = models.ForeignKey(LoggerColumn, blank=True, null=True)

    def __str__(self):
        return self.name


class LogBase(SphinxModel):
    class Meta:
        abstract = True
        ordering = ('pk',)
        db_table = 'logger'

    logline = models.TextField()
    js = JSONField()

    @property
    def ts(self):
        return self.pk / (10**9)

    @property
    def ms(self):
        return (self.pk / 1000) % 10**6

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timestamp)

    @property
    def timestamp(self):
        return (self.pk / 1000) / 1000000.0


def create_char_field(c):
    return models.CharField(max_length=255, db_column='js.%s' % c)


def create_sphinx_field(c):
    return SphinxField(max_length=255, db_column=c)


def create_index_model(index, distr=None):
    model_name = str("%sLog" % index.name.title())
    if distr:
        table = str('%s_%s_distr' % (index.name, distr))
    else:
        table = str(index.name)

    class Meta:
        db_table = table

    fields = {}

    for column in index.loggercolumn_set.all():
        if column.indexed:
            fields[column.name] = create_sphinx_field(column.name)
        else:
            fields[column.name] = create_char_field(column.name)

    fields.update({'Meta': Meta, '__module__': __name__})

    Log = type(model_name, (LogBase,), fields)
    return Log


