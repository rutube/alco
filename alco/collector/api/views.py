# coding: utf-8

# $Id: $
from rest_framework.generics import ListAPIView

from alco.collector.api.serializers import LoggerIndexSerializer
from alco.collector.models import LoggerIndex


class LoggerIndexView(ListAPIView):
    queryset = LoggerIndex.objects.all()
    serializer_class = LoggerIndexSerializer
