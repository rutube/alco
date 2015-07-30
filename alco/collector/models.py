# coding: utf-8

# $Id: $
import datetime
from dateutil import rrule
from django.db import models


class LoggerIndex(models.Model):

    name = models.CharField(max_length=20)
    intervals = models.IntegerField(default=30)
    queue_name = models.CharField(max_length=30, default='logstash')
    routing_key = models.CharField(max_length=30, default='logstash')

    @property
    def index_names(self):
        return [d.strftime("%Y%m%d") for d in self.index_dates]

    @property
    def index_dates(self):
        today = datetime.date.today()
        midnight = today + datetime.timedelta(days=1)
        start = midnight - datetime.timedelta(days=self.intervals)
        dates = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=midnight)
        return list(dates)

    @property
    def field_names(self):
        return list(self.loggercolumn_set.values_list('name', flat=True))

    @property
    def filtered_fields(self):
        return list(self.loggercolumn_set.filter(
            filtered=True).values_list('name', flat=True))

    def __str__(self):
        return self.name


class LoggerColumn(models.Model):

    index = models.ForeignKey(LoggerIndex)
    name = models.CharField(max_length=100)
    filtered = models.BooleanField(default=False)
    display = models.BooleanField(default=True)
    context = models.BooleanField(default=False)

    def __str__(self):
        return '%s(%s)' % (self.name, self.index)