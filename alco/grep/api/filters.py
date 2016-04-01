# coding: utf-8

from collections import OrderedDict

from rest_framework.filters import BaseFilterBackend
from rest_framework.settings import api_settings
# noinspection PyPackageRequirements
from sphinxsearch.utils import sphinx_escape


class SphinxSearchFilter(BaseFilterBackend):
    # The URL query parameter used for the search.
    search_param = api_settings.SEARCH_PARAM

    @staticmethod
    def get_search_fields(request, view):
        search_fields = getattr(view, 'get_search_fields', None)
        if callable(search_fields):
            search_fields = search_fields(request)
        else:
            search_fields = getattr(view, 'search_fields', None)
        return search_fields

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
    def get_match_terms(request, search_fields):
        result = {}
        for key in search_fields:
            value = request.query_params.get(key + '__in')
            if value is None:
                value = request.query_params.get(key)
                if value is None:
                    continue
            result[key] = value.split(',')
        return result

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(request, view)
        search_terms = self.get_search_terms(request)
        if search_terms:
            queryset = queryset.match(logline='"%s"' % ' '.join(search_terms))

        match_terms = self.get_match_terms(request, search_fields)
        for field, values in match_terms.items():
            if len(values) == 1:
                queryset = queryset.filter(**{field: values[0]})
            else:
                values = '|'.join('"%s"' % sphinx_escape(v) for v in values)
                queryset = queryset.match(**{"%s" % field: values})

        select = dict(logline_snippet="SNIPPET(logline, %s, 'limit=1000000')")
        params = [' '.join(self.get_search_terms(request, escape=False))]
        return queryset.extra(select=select, select_params=params)


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
