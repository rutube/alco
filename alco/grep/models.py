# coding: utf-8

# $Id: $
import time
from datetime import datetime
from django.db import models
from jsonfield import JSONField

from sphinxsearch.models import SphinxModel


class Log(SphinxModel):
    class Meta:
        ordering = ('id',)
        db_table = 'logger'

    ts = models.IntegerField()
    ms = models.IntegerField()
    seq = models.BigIntegerField()
    host = models.CharField(max_length=60, db_column='js.host')
    logline = models.TextField()
    js = JSONField()

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.ts).replace(microsecond=self.ms)

    @property
    def timestamp(self):
        return time.mktime(self.datetime.timetuple())
