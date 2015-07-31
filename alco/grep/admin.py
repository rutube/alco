# coding: utf-8

# $Id: $


from django.contrib import admin
from alco.grep.models import Shortcut


class ShortcutAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


admin.site.register(Shortcut, ShortcutAdmin)

