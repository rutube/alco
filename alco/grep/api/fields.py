# coding: utf-8

# $Id: $
import ujson as json
import six
from rest_framework import serializers


def dump_obj(value):
    if type(value) not in (bool, int, float, six.text_type):
        return json.dumps(value)
    return value


class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return {k: dump_obj(v) for k, v in value.items()}
        # return value

