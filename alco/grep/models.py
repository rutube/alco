# coding: utf-8

# $Id: $
from django.db import models
from jsonfield import JSONField

from sphinxsearch.models import SphinxModel


class Log(SphinxModel):
    class Meta:
        ordering = ('id',)
        db_table = 'logger'

    ts = models.IntegerField()
    host = models.CharField(max_length=60, db_column='js.host')
    logline = models.TextField()
    js = JSONField()
