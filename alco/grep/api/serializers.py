# coding: utf-8

# $Id: $
from rest_framework.serializers import ModelSerializer

from alco.grep.api.fields import JSONSerializerField
from alco.grep.models import Log


class LogSerializer(ModelSerializer):
    class Meta:
        model = Log

    js = JSONSerializerField()