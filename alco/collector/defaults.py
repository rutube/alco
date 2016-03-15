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
        'virtual_host': '/',
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
    'LOG_PAGE_SIZE': 100,
    'RABBITMQ_API_PORT': 55672
}

# Allow to override some settings from project django conf.

_custom = getattr(settings, 'ALCO_SETTINGS', {})
for k, v in _custom.items():
    ALCO_SETTINGS[k] = v

SPHINX_CONFIG = {
    'index': {
        'morphology': 'none',
        'min_word_len': 4,
    },
    'searchd': {
        'listen': '9306:mysql41',
        'log': '/var/log/sphinxsearch/searchd.log',
        'query_log': '/var/log/sphinxsearch/query.log',
        'read_timeout': 5,
        'client_timeout': 300,
        'max_children': 30,
        'dist_threads': 4,
        'ondisk_attrs_default': 'pool',
        'persistent_connections_limit': 30,
        'pid_file': '/var/run/sphinxsearch/searchd.pid',
        'seamless_rotate': 1,
        'preopen_indexes': 1,
        'unlink_old': 1,
        'binlog_path': '',  # disable logging
    }
}

# Allow to override sphinx.conf variables from project django conf.

_custom = getattr(settings, 'ALCO_SPHINX_CONF', {})
for section in SPHINX_CONFIG.keys():
    for k, v in _custom.get(section, {}).items():
        SPHINX_CONFIG[section][k] = v