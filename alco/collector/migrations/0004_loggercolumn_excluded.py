# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0003_loggercolumn_context'),
    ]

    operations = [
        migrations.AddField(
            model_name='loggercolumn',
            name='excluded',
            field=models.BooleanField(default=False),
        ),
    ]
