# coding: utf-8

from collections import OrderedDict

from django.utils import six
from rest_framework.filters import BaseFilterBackend
from rest_framework.settings import api_settings
# noinspection PyPackageRequirements
from sphinxsearch.utils import sphinx_escape


class SphinxSearchFilter(BaseFilterBackend):
    # The URL query parameter used for the search.
    search_param = api_settings.SEARCH_PARAM

    def get_search_terms(self, request, escape=True):
        """
        Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited.
        """
        params = request.query_params.get(self.search_param, '')
        if not params or params == " ":
            return []
        if escape:
            return list(map(sphinx_escape, params.replace(',', ' ').split()))
        return params.replace(',', ' ').split()

    @staticmethod
    def construct_search(field_name):
        return '@%s ("%%s")' % field_name

    def filter_queryset(self, request, queryset, view):
        search_fields = getattr(view, 'search_fields', None)

        if not search_fields:
            return queryset

        search_terms = self.get_search_terms(request)
        if not search_terms:
            return queryset

        orm_lookups = [self.construct_search(six.text_type(search_field))
                       for search_field in search_fields]

        search_query = ' & '.join(search_terms)
        match_expression = '|'.join(lookup % search_query
                                    for lookup in orm_lookups)
        queryset = queryset.match(match_expression)
        select = dict(logline_snippet="SNIPPET(logline, %s, 'limit=1000000')")
        params = [' '.join(self.get_search_terms(request, escape=False))]
        return queryset.extra(select=select, select_params=params)
        # FIXME: return qs.options(before_match='<ins>', after_match='</ins>')


class JSONFieldFilter(BaseFilterBackend):

    @staticmethod
    def get_json_fields(request, view):
        json_fields = getattr(view, 'get_json_fields', None)
        if callable(json_fields):
            json_fields = json_fields(request)
        else:
            json_fields = getattr(view, 'json_fields', None)
        return json_fields

    def filter_queryset(self, request, queryset, view):
        json_fields = self.get_json_fields(request, view)
        if not json_fields:
            return queryset
        lookups = self.get_lookups(json_fields, request)
        all_values = set()
        for key, value in lookups.items():
            if not isinstance(value, (list, tuple)):
                value = [value]
            all_values.update(value)

        extra_lookups = OrderedDict()
        extra_params = []
        extra_where = []
        for lookup, values in lookups.items():
            field = lookup.split('__')[0]
            numeric = []
            for v in values:
                try:
                    numeric.append(int(v))
                except ValueError:
                    continue
            stub = ', '.join(['%s'] * len(values))
            extra_lookups['__%s_str' % lookup] = 'IN(js.%s, %s)' % (field, stub)
            extra_params.extend(values)
            if numeric:
                stub = ', '.join(['%s'] * len(numeric))
                extra_lookups['__%s_int' % lookup] = 'IN(js.%s, %s)' % (field,
                                                                        stub)
                extra_params.extend(numeric)
                extra_where.append('(__%s_str = 1 OR __%s_int = 1)'
                                   % (lookup, lookup))
            else:
                extra_where.append('__%s_str = 1' % lookup)
        queryset = queryset.extra(select=extra_lookups,
                                  select_params=extra_params,
                                  where=extra_where,
                                  params=[])
        return queryset

    @staticmethod
    def get_lookups(json_fields, request):
        lookups = {}
        for key in json_fields:
            value = request.query_params.get(key + '__in')
            if value is None:
                value = request.query_params.get(key)
                if value is None:
                    continue
            lookups[key + '__in'] = value.split(',')

        return lookups
