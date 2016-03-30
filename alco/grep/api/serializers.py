# coding: utf-8

# $Id: $
from copy import copy
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from sphinxsearch.models import SphinxDateTimeField
from rest_framework.fields import DateTimeField

from alco.grep.api.fields import JSONSerializerField


mapping = copy(ModelSerializer.serializer_field_mapping)
mapping[SphinxDateTimeField] = DateTimeField


class LogBaseSerializer(ModelSerializer):

    js = JSONSerializerField()
    datetime = serializers.SerializerMethodField()
    logline_snippet = serializers.SerializerMethodField()
    
    serializer_field_mapping = mapping

    def get_datetime(self, obj):
        return obj.datetime.isoformat()

    def get_logline_snippet(self, obj):
        return getattr(obj, 'logline_snippet', None)
