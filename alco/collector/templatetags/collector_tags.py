# coding: utf-8

# $Id: $
import datetime
from django import template
from dateutil import rrule

register = template.Library()


@register.filter
def index_dates(index):
    today = datetime.date.today()

    midnight = today + datetime.timedelta(days=1)

    start = midnight - datetime.timedelta(days=index.intervals)
    print(start)
    dates = list(rrule.rrule(
        rrule.DAILY,
        dtstart=start,
        until=midnight))
    return dates

