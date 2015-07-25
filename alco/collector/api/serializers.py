# coding: utf-8

# $Id: $
from rest_framework import fields
from rest_framework.fields import ListField
from rest_framework.serializers import ModelSerializer
from alco.collector.models import LoggerIndex


class LoggerIndexSerializer(ModelSerializer):
    class Meta:
        model = LoggerIndex

    index_names = ListField()