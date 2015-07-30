# coding: utf-8

# $Id: $
from collections import OrderedDict

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page, \
    InvalidPage
from django.utils import six
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from alco.collector.defaults import ALCO_SETTINGS


class FeedPage(Page):
    """ Endless feed page.

     Next page is determined by expression len(object_list) > per_page.
     `object_list` contains per_page + 1 object to detect whether next page is
     present.
     """

    @property
    def object_list(self):
        """ Returns page object list without after-end indication element."""
        try:
            return self.__object_list[:self.paginator.per_page]
        except TypeError:
            return list()

    @object_list.setter
    def object_list(self, value):
        self.__object_list = value

    def __init__(self, object_list, number, paginator):
        self.__object_list = None
        super(FeedPage, self).__init__(object_list, number, paginator)

    def __repr__(self):
        return '<Page %s of Unknown>' % (self.number,)

    def has_next(self):
        try:
            return len(self.__object_list) > self.paginator.per_page
        except TypeError:
            return False

    def end_index(self):
        raise NotImplementedError("feed doesn't support count")


class FeedPaginator(Paginator):
    """ Endless feed Django paginator."""

    def _get_num_pages(self):
        """ Needs count."""
        raise NotImplementedError()

    def _get_page_range(self):
        """ Needs count."""
        raise NotImplementedError()

    def _get_count(self):
        """ For endless feed count is not needed."""
        raise NotImplementedError()

    def validate_number(self, number):
        """ Validates the given 1-based page number. """
        try:
            number = int(number)
        except ValueError:
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        return number

    count = property(_get_count)

    def page(self, number):
        """ Returns a Page object for the given 1-based page number. """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        # top + 1 object is needed for FeedPage to detect next page presence.
        if self.object_list is not None:
            return FeedPage(self.object_list[bottom: top + 1], number, self)
        return FeedPage(None, number, self)


class LogPaginator(PageNumberPagination):
    """ DjangoRestFramework endless paginator."""

    page_size = ALCO_SETTINGS['LOG_PAGE_SIZE']

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        self._handle_backwards_compat(view)

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = FeedPaginator(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=six.text_type(exc)
            )
            raise NotFound(msg)

        if self.page.has_next() > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))
