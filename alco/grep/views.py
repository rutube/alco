# coding: utf-8

# $Id: $
from collections import OrderedDict
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
    template_name = 'grep/log_view.html'

    def get_context_data(self, **kwargs):
        cd = super(GrepView, self).get_context_data(**kwargs)
        obj = self.get_object(self.get_queryset())
        filters = []
        columns = []
        for f in obj.loggercolumn_set.order_by('name'):
            if f.display:
                columns.append(f)
            if f.filtered:
                filters.append({
                    'title': f.name.title(),
                    'field': f.name,
                    'heading_id': 'heading-%s' % f.name,
                    'collapse_id': 'collapse-%s' % f.name,
                    'items': self.get_field_values(obj.name, f.name)
                })
        cd['filters'] = filters
        cd['columns'] = columns
        cd['column_names'] = [c.name for c in columns]
        return cd

    @staticmethod
    def get_field_values(index, column):
        key = keys.KEY_COLUMN_VALUES.format(index=index, column=column)
        return sorted(client.smembers(key))