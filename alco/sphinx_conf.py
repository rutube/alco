#!/usr/bin/env python
# coding: utf-8
import re

import sys
import os
import json
import shutil

settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'settings')
settings_module = settings_module.replace('.', '/')
settings_file = settings_module + '.py'
settings_path = os.path.join(os.getcwd(), settings_file)

if sys.version_info[0] > 2:
    # noinspection PyUnresolvedReferences
    from urllib.request import urlopen
    with open(settings_path, 'rb') as f:
        exec(compile(f.read(), settings_file, "exec"))
else:
    # noinspection PyUnresolvedReferences
    from urllib2 import urlopen
    # noinspection PyUnresolvedReferences
    execfile(settings_path)

# noinspection PyUnresolvedReferences
ALCO_HOST = ALCO_SETTINGS['SPHINX_CONF_URL']

r = urlopen(os.path.join(ALCO_HOST, 'collector/sphinx.conf'))
config = r.read().decode('utf-8')

r = urlopen(os.path.join(ALCO_HOST, 'api/collector/indices/?format=json'))
indices = json.loads(r.read().decode('utf-8'))
for idx in indices:
    name = idx['name']
    to_delete = []
    for dt in idx['index_names']:
        # create dir for new indices
        path = os.path.join("/data/sphinx/", name, dt)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError:
                pass

    # collect all old index dirs for logger
    local_dir = os.path.join("/data/sphinx", name)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    for dt in os.listdir(local_dir):
        if not re.match(r'^[\d]{8}$', dt):
            continue
        if dt not in idx['index_names']:
            to_delete.append(dt)

    # remove all old index dirs except one latedt
    for dt in sorted(to_delete)[:-1]:
        shutil.rmtree(os.path.join(local_dir, dt), ignore_errors=True)

print(config)
