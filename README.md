ALCO - Autonomous Log Collector and Observer
============================================

[![PyPI version](https://badge.fury.io/py/alco.svg)](http://badge.fury.io/py/alco)


What's the problem
------------------

There is a widely used stack of technologies for parsing, collecting and
analysing logs - [ELK Stack](https://www.elastic.co/products).
It has very functional web interface, search cluster and a log transformation tool. Very cool, but:

* It's Java with well-known requirements for memory and CPUs
* It's ElasticSearch with it's requirements for disk space
* It's Logstash which suddenly stops processing logs in some conditions.
* It's Kibana with very cool RICH interface which looses on all counts to `grep` and `less` in a task of log reading and searching.

Introducing ALCO
----------------

ALCO is a simple ELK analog which primary aim is to provide a online replacement for `grep` and `less`. Main features are:

* Django application for incident analysis in distributed systems
* schemeless full-text index with filtering and searching
* configurable log collection and rotation from RabbitMQ messaging server
* not a all-purpose monster

Technology stack
----------------

Let's trace log message path from some distributed system to ALCO web interface.

1. Python-based project calls `logger.debug()` method with text 'hello world'
2. At startup time [Logcollect](https://github.com/rutube/logcollect/) library automatically configures python logging (or even [Django](https://github.com/django/django/) and [Celery](https://github.com/celery/celery) one's) to send log messages to RabbitMQ server in JSON format readable both with ELK and ALCO projects.
3. ALCO log collector binds a queue to RabbitMQ exchange and processes messages in a batch.
4. It uses Redis to collect unique values for filterable fields and SphinxSearch to store messages in a realtime index.
5. When a message is inserted to sphinxsearch, it contains indexed `message` field, timestamp information and schemeless JSON field named `js` with all log record attributes sent by python log.
6. Django-based web interface provides API and client-side app for searching collected logs online.

Requirements
------------

* Python 2.7 or 3.3+
* [Logcollect](https://github.com/rutube/logcollect/) for python projects which logs are collected
* [RabbitMQ](https://www.rabbitmq.com/) server for distributed log collection
* [SphinxSearch](http://sphinxsearch.com/) server 2.3 or later for log storage
* [Redis](http://redis.io/) for SphinxSearch docid management and field values storage
* [django-sphinxsearch](https://github.com/rutube/django_sphinxsearch) as a database backend for `Django>=1.8` (will be available from PyPI)

Setup
-----

1. You need to configure logcollect in analyzed projects (see [README](https://github.com/rutube/logcollect#tips-for-configuration)). If RabbitMQ admin interface shows non-zero message flow in `logstash` exchange - "It works" :-)

2. Install alco and it's requirements from PyPi

    ```sh
    pip install alco
    ```

3. Next, create django project, add `sphinxsearch` database connection and configure `settings.py` to enable alco applications

    ```python
    # For SphinxRouter
    SPHINX_DATABASE_NAME = 'sphinx'
    
    DATABASES[SPHINX_DATABASE_NAME] = {
          'ENGINE': 'sphinxsearch.backend.sphinx',
          'HOST': '127.0.0.1',
          'PORT': 9306,
      }
    }
    
    # Auto routing log models to SphinxSearch database
    DATABASE_ROUTERS = (
      'sphinxsearch.routers.SphinxRouter',
    )
    
    INSTALLED_APPS += [
    'rest_framework', # for API to work
    'alco.collector',
    'alco.grep'
    ]
    
    ROOT_URLCONF = 'alco.urls'
    ```

4. Configure ALCO resources in `settings.py`:

    ```python
    ALCO_SETTINGS = {
      # log messaging server
      'RABBITMQ': {
          'host': '127.0.0.1',
          'userid': 'guest',
          'password': 'guest',
          'virtual_host': '/'
      },
    
      # redis server
      'REDIS': {
          'host': '127.0.0.1',
          'db': 0
      },
      # url for fetching sphinx.conf dynamically
      'SPHINX_CONF_URL': 'http://127.0.0.1:8000/collector/sphinx.conf',
      # name of django.db.connection for SphinxSearch
      'SPHINX_DATABASE_NAME': 'sphinx',
      # number of results in log view API
      'LOG_PAGE_SIZE': 100
    }
    
    # override defaults for sphinx.conf template
    ALCO_SPHINX_CONF = {
      # local index definition defaults override 
      'index': {
        'min_word_len': 8
      },
      # searchd section defaults override
      'searchd': {
        'dist_threads': 8
      }
    }
    
    ```

5. Run `syncdb` or better `migrate` management command to create database tables.

6. Run webserver and create a LoggerIndex from [django admin](http://127.0.0.1:8000/admin/collector/loggerindex/).

7. Created directories for sphinxsearch:

    ```
    /var/log/sphinx/
    /var/run/sphinx/
    /data/sphinx/
    ```

8. Next, configure sphinxsearch to use generated config:

    ```sh
    
    searchd -c sphinx_conf.py
    ```
    
    `sphinx_conf.py` is a simple script that imports `alco.sphinx_conf` module which fetches generated `sphinx.conf` from alco http api and created directories for SphinxSearch indices:
    
    ```python
    #!/data/alco/virtualenv/bin/python
    
    # coding: utf-8
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    
    from alco import sphinx_conf
    ```

9. Run log collectors:

    ```sh
    python manage.py start_collectors --no-daemon
    ```
    
    If it shows number of collected messages periodically - then log collecting is set up correctly.

10. Configure system services to start subsystems automatically:

    * nginx or apache http server
    * django uwsgi backend
    * alco collectors (`start_collectors` management command)
    * sphinxsearch, redis, default database for Django

11. Open `http://127.0.0.1:8000/grep/<logger_name>/` to read and search logs online.

Virtualenv
----------

We successfully configured SphinxSearch to use python from `virtualenv`, adding some environment variables to start script (i.e. FreeBSD rc.d script):

```sh

sphinxsearch_prestart ()
{
    # nobody user has no HOME
    export PYTHON_EGG_CACHE=/tmp/.python-eggs
    # python path for virtualenv interpreter should be redeclared
    export PYTHONPATH=${venv_path}/lib/python3.4/:${venv_path}/lib/python3.4/site-packages/
    . "${virtualenv_path}/bin/activate" || err 1 "Virtualenv is not found"
    echo "Virtualenv ${virtualenv_path} activated: `which python`"

}

```

In this case _shebang_ for `sphinx_conf.py` must point virtualenv's python interpreter.

Production usage
----------------

For now ALCO stack is tested in preproduction environment in our company and is actively developed. There are no reasons to say that it's not ready for production usage.
