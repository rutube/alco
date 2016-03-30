# coding: utf-8

# $Id: $
from django.contrib import admin
from alco.collector.models import LoggerIndex, LoggerColumn


class LoggerIndexAdmin(admin.ModelAdmin):
    massadmin_exclude = ('name',)
    list_display = ('name', 'queue_name', 'routing_key')


class LoggerColumnAdmin(admin.ModelAdmin):
    massadmin_exclude = ('index', 'name',)
    list_display = ('name', 'index_name', 'filtered', 'display', 'context',
                    'excluded', 'indexed')
    list_filter = ('index',)

    def index_name(self, obj):
        return obj.index.name


admin.site.register(LoggerIndex, LoggerIndexAdmin)
admin.site.register(LoggerColumn, LoggerColumnAdmin)

