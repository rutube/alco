# coding: utf-8

# $Id: $
from pprint import pformat

from django import template
import math
from django.template import Node
import re
from django.utils.encoding import force_text
from django.utils.functional import allow_lazy
import six

register = template.Library()


@register.inclusion_tag('grep/tags/filter_item.html')
def filter_item(heading_id, collapse_id, field, title, items):
    return locals()


@register.inclusion_tag('grep/tags/columns_item.html')
def columns_item(heading_id, collapse_id, field, title, items):
    return locals()


@register.inclusion_tag('grep/tags/dates_item.html')
def dates_item(heading_id, collapse_id, field, title, items):
    return locals()


def strip_lines_between_tags(value):
    """Returns the given HTML with spaces between tags removed."""
    return re.sub(r'>\s+<([^/])', '><\\1', force_text(value))
strip_lines_between_tags = allow_lazy(strip_lines_between_tags, six.text_type)


class LinelessNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return strip_lines_between_tags(self.nodelist.render(context).strip())



@register.tag
def lineless(parser, token):
    nodelist = parser.parse(('endlineless',))
    parser.delete_first_token()
    return LinelessNode(nodelist)
