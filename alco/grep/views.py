# coding: utf-8

# $Id: $
from copy import copy
from datetime import datetime, timedelta
import time

from django.http import HttpResponseRedirect
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib import parse
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, RedirectView, ListView
from django.views.generic.detail import SingleObjectMixin
import redis

from alco.collector import keys
from alco.collector.defaults import ALCO_SETTINGS
from alco.collector.models import LoggerIndex
from alco.grep.models import Shortcut, create_index_model

client = redis.Redis(**ALCO_SETTINGS['REDIS'])


class GrepView(DetailView):
    model = LoggerIndex
    slug_field = 'name'
    slug_url_kwarg = 'name'
    template_name = 'grep/log_view.html'

    def get(self, request, *args, **kwargs):
        if not request.GET.get('start_ts'):
            url = parse.urlparse(request.path)
            query_string = dict(parse.parse_qsl(request.META['QUERY_STRING']))
            start_ts = datetime.now().replace(microsecond=0) - timedelta(minutes=5)
            query_string['start_ts'] = start_ts.isoformat(sep=' ')
            query = parse.urlencode(query_string).replace('+', '%20')
            url = url._replace(query=query)
            return HttpResponseRedirect(parse.urlunparse(url))
        return super(GrepView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        cd = super(GrepView, self).get_context_data(**kwargs)
        obj = self.get_object(self.get_queryset())
        filters = []
        columns = []
        context_columns = []
        ts = time.mktime(obj.index_dates[0].timetuple())
        for f in obj.loggercolumn_set.order_by('name'):
            if f.display:
                columns.append(f)
            if f.context:
                context_columns.append(f)
            if f.filtered:
                filters.append({
                    'title': f.name.title(),
                    'field': f.name,
                    'heading_id': 'heading-%s' % f.name,
                    'collapse_id': 'collapse-%s' % f.name,
                    'items': self.get_field_values(obj, f.name, ts)
                })
        cd['filters'] = filters
        cd['columns'] = columns
        cd['context_columns'] = context_columns
        cd['filtered_columns'] = list(set(columns) | set(context_columns))
        cd['column_names'] = [c.name for c in columns]
        return cd

    @staticmethod
    def get_field_values(index, column, ts):
        key = keys.KEY_COLUMN_VALUES.format(index=index.name, column=column)
        return sorted(client.zrangebyscore(key, ts, '+inf'))


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


class IndexListView(ListView):
    model = LoggerIndex

    template_name = 'grep/loggerindex_list.html'

    def get_context_data(self, **kwargs):
        cd = super(IndexListView, self).get_context_data(**kwargs)
        ts = datetime.now().replace(microsecond=0) - timedelta(minutes=5)
        distr = ts.strftime('%Y%m%d')
        for index in cd['object_list']:
            log_model = create_index_model(index, distr=distr)
            start_id = int(time.mktime(ts.timetuple()) * 1000000000)
            index.last_count = log_model.objects.filter(id__gt=start_id).count()
        return cd

