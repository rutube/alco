# coding: utf-8

# $Id: $
from django.db import models


class LoggerIndex(models.Model):

    DAILY = 0
    rotate_choices = (
        (DAILY, 'daily'),
    )

    name = models.CharField(max_length=20)
    rotate = models.SmallIntegerField(default=0, choices=rotate_choices)
    intervals = models.IntegerField(default=30)
    queue_name = models.CharField(max_length=30, default='logstash')
    routing_key = models.CharField(max_length=30, default='logstash')