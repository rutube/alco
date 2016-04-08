# coding: utf-8

# $Id: $


from django.conf.urls import url

from alco.grep.views import GrepView, ShortcutView, IndexListView

urlpatterns = [
    url(r'^(?P<name>[\w]+)/$', GrepView.as_view(), name='grep_view'),
    url(r'^shortcut/(?P<name>[\w]+)/(?P<default_value>.+)/$',
        ShortcutView.as_view(), name="shortcut_view"),
    url(r'^shortcut/(?P<name>[\w]+)/$',
        ShortcutView.as_view(), name="shortcut_view"),
    url(r'^$', IndexListView.as_view(), name="index_list_view")
]
