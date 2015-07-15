# coding: utf-8

# $Id: $



from django.conf.urls import url

from alco.grep.api.views import GrepView

urlpatterns = [
    url(r'^grep/', GrepView.as_view()),
]