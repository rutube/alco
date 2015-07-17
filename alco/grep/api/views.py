# coding: utf-8

# $Id: $
from django.utils.functional import cached_property
import django_filters
from rest_framework import filters as rf_filters
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from alco.collector.models import LoggerIndex

from alco.grep.api import filters
from alco.grep.models import create_index_model
from alco.grep.api.serializers import LogBaseSerializer


class LogPaginator(PageNumberPagination):
    page_size = 20


class GrepView(ListAPIView):
    filter_backends = (rf_filters.DjangoFilterBackend,
                       filters.SphinxSearchFilter,
                       filters.JSONFieldFilter)
    search_fields = ('logline',)
    json_fields = ('js.levelname', 'js.sid', 'js.project', 'js.application',
                   'js.task_name', 'js.task_id')

    pagination_class = LogPaginator

    @property
    def filter_class(self):
        class TimestampFilter(django_filters.FilterSet):
            start_ts = django_filters.NumberFilter(name="ts", lookup_type='gte')
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
        return self.log_model.objects.all()




