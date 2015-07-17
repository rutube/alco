# coding: utf-8

# $Id: $
from django.conf import settings
from django.views.generic import DetailView
import redis

from alco.collector import keys
from alco.collector.models import LoggerIndex

client = redis.Redis(settings.REDIS_HOST, db=settings.REDIS_DB)

class GrepView(DetailView):
    model = LoggerIndex
    slug_field = 'name'
    slug_url_kwarg = 'name'

    def get_context_data(self, **kwargs):
        cd = super(GrepView, self).get_context_data(**kwargs)
        return cd
