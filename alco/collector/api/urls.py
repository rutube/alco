# coding: utf-8

# $Id: $


from django.conf.urls import url
from alco.collector.api.views import LoggerIndexView

urlpatterns = [
    url(r'^indices/', LoggerIndexView.as_view()),
]