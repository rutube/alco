# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grep', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shortcut',
            name='default_field',
            field=models.ForeignKey(blank=True, to='collector.LoggerColumn', null=True),
        ),
    ]
