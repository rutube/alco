# coding: utf-8

# $Id: $


from django.views.generic import ListView

from alco.collector.models import LoggerIndex


class LoggerIndexView(ListView):
    model = LoggerIndex
    content_type = 'text/plain'
    template_name = 'collector/sphinx.conf'
