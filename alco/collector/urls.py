# coding: utf-8

# $Id: $



from django.conf.urls import url

from alco.collector.views import LoggerIndexView

urlpatterns = [
    url(r'^sphinx\.conf', LoggerIndexView.as_view()),
]