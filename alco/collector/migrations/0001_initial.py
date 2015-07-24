# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LoggerColumn',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=100)),
                ('filtered', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LoggerIndex',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=20)),
                ('intervals', models.IntegerField(default=30)),
                ('queue_name', models.CharField(default='logstash', max_length=30)),
                ('routing_key', models.CharField(default='logstash', max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name='loggercolumn',
            name='index',
            field=models.ForeignKey(to='collector.LoggerIndex'),
        ),
    ]
