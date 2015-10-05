# coding: utf-8

# $Id: $
from django.utils.timezone import now, localtime

from django.views.generic import ListView
from django.conf import settings
from alco.collector.defaults import SPHINX_CONFIG

from alco.collector.models import LoggerIndex


class LoggerIndexView(ListView):
    model = LoggerIndex
    content_type = 'text/plain'
    template_name = 'collector/sphinx.conf'

    def get_context_data(self, **kwargs):
        cd = super(LoggerIndexView, self).get_context_data(**kwargs)
        cd['settings'] = settings
        cd['config'] = SPHINX_CONFIG
        cd['now'] = localtime(now()).strftime('%Y-%m-%d %H:%M:%S')
        return cd