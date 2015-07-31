# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0003_loggercolumn_context'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shortcut',
            fields=[
                ('name', models.CharField(max_length=30, serialize=False, primary_key=True)),
                ('description', models.CharField(blank=True, max_length=255, default='')),
                ('url', models.CharField(max_length=255)),
                ('default_field', models.ForeignKey(to='collector.LoggerColumn', null=True)),
                ('index', models.ForeignKey(to='collector.LoggerIndex')),
            ],
        ),
    ]
