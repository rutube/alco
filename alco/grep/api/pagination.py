# coding: utf-8

# $Id: $

from rest_framework.pagination import CursorPagination

from alco.collector.defaults import ALCO_SETTINGS


class CursorLogPaginator(CursorPagination):
    page_size = ALCO_SETTINGS['LOG_PAGE_SIZE']
    ordering = ('id',)
