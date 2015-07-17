# coding: utf-8

# $Id: $
from pprint import pformat

from django import template
import math

register = template.Library()


@register.inclusion_tag('grep/tags/accordion_item.html')
def accordion_item(heading_id, collapse_id, field, title, items):
    return locals()
