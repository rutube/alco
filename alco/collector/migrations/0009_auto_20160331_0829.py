# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-31 08:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0008_loggercolumn_indexed'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='loggercolumn',
            unique_together=set([('index', 'name')]),
        ),
    ]
