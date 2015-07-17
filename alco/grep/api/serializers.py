# coding: utf-8

# $Id: $
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from alco.grep.api.fields import JSONSerializerField


class LogBaseSerializer(ModelSerializer):

    js = JSONSerializerField()
    datetime = serializers.SerializerMethodField()

    def get_datetime(self, obj):
        return obj.datetime.isoformat()