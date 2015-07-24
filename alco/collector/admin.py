# coding: utf-8

# $Id: $
from django.contrib import admin
from alco.collector.models import LoggerIndex, LoggerColumn


class LoggerIndexAdmin(admin.ModelAdmin):
    list_display = ('name', 'queue_name', 'routing_key')


class LoggerColumnAdmin(admin.ModelAdmin):
    list_display = ('name', 'index_name', 'filtered', 'display')

    def index_name(self, obj):
        return obj.index.name


admin.site.register(LoggerIndex, LoggerIndexAdmin)
admin.site.register(LoggerColumn, LoggerColumnAdmin)

