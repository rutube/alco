# coding: utf-8

# $Id: $
from pprint import pformat

from django import template
import math

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
