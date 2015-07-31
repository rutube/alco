# coding: utf-8

# $Id: $
from copy import copy
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib import parse
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, RedirectView
from django.views.generic.detail import SingleObjectMixin
import redis

from alco.collector import keys
from alco.collector.defaults import ALCO_SETTINGS
from alco.collector.models import LoggerIndex
from alco.grep.models import Shortcut

client = redis.Redis(**ALCO_SETTINGS['REDIS'])


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


class ShortcutView(SingleObjectMixin, RedirectView):
    model = Shortcut
    permanent = False

    slug_url_kwarg = 'name'
    slug_field = 'name'

    def get_redirect_url(self, *args, **kwargs):
        obj = self.get_object()
        url = parse.urlparse(obj.url)
        query_params = copy(self.request.GET)
        lookup = self.kwargs.get('default_value')
        if lookup and obj.default_field:
            query_params[obj.default_field.name] = lookup

        query_params.update(**dict(parse.parse_qsl(url.query)))

        url = reverse('grep_view', kwargs={'name': obj.index.name})
        url = parse.urlparse(url)
        parts = list(url)
        parts[4] = parse.urlencode(query_params)
        return parse.urlunparse(parts)
