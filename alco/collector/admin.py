# coding: utf-8

# $Id: $
from django.contrib import admin
from alco.collector.models import LoggerIndex


class LoggerIndexAdmin(admin.ModelAdmin):
    list_display = ('name', 'queue_name', 'routing_key')


admin.site.register(LoggerIndex, LoggerIndexAdmin)

