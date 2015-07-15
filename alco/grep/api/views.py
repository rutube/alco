# coding: utf-8

# $Id: $
from rest_framework import filters as rf_filters
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from alco.grep.api import filters
from alco.grep.api.serializers import LogSerializer
from alco.grep.models import Log


class LogPaginator(PageNumberPagination):
    page_size = 10


class GrepView(ListAPIView):
    filter_backends = (rf_filters.DjangoFilterBackend,
                       filters.SphinxSearchFilter,
                       filters.JSONFieldFilter)
    filter_class = filters.TimestampFilter
    search_fields = ('logline',)
    json_fields = ('js.levelname', 'js.sid', 'js.project', 'js.application',
                   'js.task_name', 'js.task_id')
    queryset = Log.objects.all()
    serializer_class = LogSerializer

    pagination_class = LogPaginator
