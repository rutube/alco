# coding: utf-8

# $Id: $

from django.conf import settings

__all__ = ['ALCO_SETTINGS']

# default settings for alco package
ALCO_SETTINGS = {
    # log messaging server
    'RABBITMQ': {
        'host': '127.0.0.1',
        'userid': 'guest',
        'password': 'guest',
        'virtual_host': '/'
    },

    # redis for generating primary key sequences
    'REDIS': {
        'host': '127.0.0.1',
        'db': 0
    },
    # url for fetching sphinx.conf dynamically
    'SPHINX_CONF_URL': 'http://127.0.0.1:8000/',
    # name of django.db.connection for SphinxSearch
    'SPHINX_DATABASE_NAME': 'sphinx',
    # number of results in log view API
    'LOG_PAGE_SIZE': 100
}

# Allow to override some settings from project django conf.

_custom = getattr(settings, 'ALCO_SETTINGS', {})
for k, v in _custom.items():
    ALCO_SETTINGS[k] = v
