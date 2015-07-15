# coding: utf-8

# $Id: $


from django.conf.urls import url

from alco.grep.views import GrepView

urlpatterns = [
    url(r'^(?P<name>[\w]+)/', GrepView.as_view()),
]
