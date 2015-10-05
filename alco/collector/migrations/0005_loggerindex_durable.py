# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0004_loggercolumn_excluded'),
    ]

    operations = [
        migrations.AddField(
            model_name='loggerindex',
            name='durable',
            field=models.BooleanField(default=False),
        ),
    ]
