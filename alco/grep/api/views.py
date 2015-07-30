# coding: utf-8

# $Id: $
from django.utils.functional import cached_property
import django_filters
from rest_framework import filters as rf_filters
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from alco.collector.defaults import ALCO_SETTINGS
from alco.collector.models import LoggerIndex

from alco.grep.api import filters
from alco.grep.models import create_index_model
from alco.grep.api.serializers import LogBaseSerializer


class LogPaginator(PageNumberPagination):
    page_size = ALCO_SETTINGS['LOG_PAGE_SIZE']


class GrepView(ListAPIView):
    filter_backends = (rf_filters.DjangoFilterBackend,
                       filters.SphinxSearchFilter,
                       filters.JSONFieldFilter)
    search_fields = ('logline',)

    pagination_class = LogPaginator

    @property
    def filter_class(self):
        class TimestampFilter(django_filters.FilterSet):
            start_ts = django_filters.DateTimeFilter(name="ts", lookup_type='gte')
            end_ts = django_filters.NumberFilter(name="ts", lookup_type='lte')

            class Meta:
                model = self.log_model
                fields = ['ts'] + self.index.field_names

        return TimestampFilter

    @cached_property
    def index(self):
        return LoggerIndex.objects.get(name=self.kwargs['logger'])

    @cached_property
    def log_model(self):
        return create_index_model(self.index)

    def get_serializer_class(self):
        class Meta:
            model = self.log_model

        serializer_class = type('LogSerializer', (LogBaseSerializer,),
                                {'Meta': Meta})
        return serializer_class

    def get_queryset(self):
        return self.log_model.objects.order_by('ts', 'ms', 'seq')

    def get_json_fields(self, request):
        fields = self.index.filtered_fields
        result = []
        for key, value in request.GET.items():
            field = key.split('__')[0]
            if field in fields:
                result.append(field)
        return result




