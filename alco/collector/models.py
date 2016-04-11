# coding: utf-8

# $Id: $
import datetime
from dateutil import rrule
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import localtime, now


class LoggerIndex(models.Model):

    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=20)
    intervals = models.IntegerField(default=30)
    queue_name = models.CharField(max_length=30, default='logstash')
    routing_key = models.TextField(default='logstash')
    durable = models.BooleanField(default=False, blank=True)
    num_processes = models.IntegerField(default=1)

    @property
    def index_names(self):
        return [d.strftime("%Y%m%d") for d in self.index_dates]

    @property
    def index_dates(self):
        today = localtime(now()).date()
        midnight = today + datetime.timedelta(days=1)
        start = midnight - datetime.timedelta(days=self.intervals)
        dates = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=midnight)
        return list(dates)

    @cached_property
    def field_names(self):
        return list(self.loggercolumn_set.values_list('name', flat=True))

    @cached_property
    def filtered_fields(self):
        return list(self.loggercolumn_set.filter(
            filtered=True).values_list('name', flat=True))

    @cached_property
    def visible_fields(self):
        return list(self.loggercolumn_set.filter(
            display=True).values_list('name', flat=True))

    @cached_property
    def indexed_fields(self):
        return list(self.loggercolumn_set.filter(
            indexed=True).values_list('name', flat=True))

    def __str__(self):
        return self.name


class LoggerColumn(models.Model):
    class Meta:
        unique_together = ('index', 'name')
        ordering = ('name',)

    index = models.ForeignKey(LoggerIndex)
    name = models.CharField(max_length=100)
    filtered = models.BooleanField(default=False)
    display = models.BooleanField(default=True)
    excluded = models.BooleanField(default=False)
    context = models.BooleanField(default=False)
    indexed = models.BooleanField(default=False)

    def __str__(self):
        return '%s(%s)' % (self.name, self.index)