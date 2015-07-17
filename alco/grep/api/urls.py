# coding: utf-8

# $Id: $



from django.conf.urls import url

from alco.grep.api.views import GrepView

urlpatterns = [
    url(r'^(?P<logger>[\w]+)/', GrepView.as_view()),
]