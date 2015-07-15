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
    def index_dates(self):
        today = datetime.date.today()

        midnight = today + datetime.timedelta(days=1)

        start = midnight - datetime.timedelta(days=self.intervals)
        dates = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=midnight)
        return [d.strftime("%Y%m%d") for d in dates]
