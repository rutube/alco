# coding: utf-8

# $Id: $
from django.views.generic import DetailView
from alco.collector.models import LoggerIndex


class GrepView(DetailView):
    model = LoggerIndex
    slug_field = 'name'
    slug_url_kwarg = 'name'
