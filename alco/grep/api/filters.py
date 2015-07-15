# coding: utf-8

# $Id: $
from django.utils import six
import django_filters
from rest_framework.filters import BaseFilterBackend
from rest_framework.settings import api_settings

from alco.grep.models import Log
from sphinxsearch.utils import sphinx_escape


class TimestampFilter(django_filters.FilterSet):
    start_ts = django_filters.NumberFilter(name="ts", lookup_type='gte')
    end_ts = django_filters.NumberFilter(name="ts", lookup_type='lte')

    class Meta:
        model = Log
        fields = ['ts', 'host']


class SphinxSearchFilter(BaseFilterBackend):
    # The URL query parameter used for the search.
    search_param = api_settings.SEARCH_PARAM

    def get_search_terms(self, request):
        """
        Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited.
        """
        params = request.query_params.get(self.search_param, '')
        if not params:
            return []
        return map(sphinx_escape, params.replace(',', ' ').split())

    def construct_search(self, field_name):
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
        return queryset


class JSONFieldFilter(BaseFilterBackend):

    def get_json_fields(self, request, view):
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

        where = ["%s = %%s" % key for key in lookups.keys()]
        queryset = queryset.extra(where=where, params=list(lookups.values()))
        return queryset

    def get_lookups(self, json_fields, request):
        lookups = {}
        for key in json_fields:
            value = request.query_params.get(key)
            if value is None:
                continue
            lookups[key] = value

        return lookups
