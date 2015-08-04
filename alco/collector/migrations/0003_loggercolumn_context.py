# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0002_loggercolumn_display'),
    ]

    operations = [
        migrations.AddField(
            model_name='loggercolumn',
            name='context',
            field=models.BooleanField(default=False),
        ),
    ]
