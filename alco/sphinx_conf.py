#!/usr/bin/env python
# coding: utf-8

import sys
import os
import json

settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'settings')
settings_module = settings_module.replace('.', '/')
settings_file = settings_module + '.py'
settings_path = os.path.join(os.getcwd(), settings_file)

if sys.version_info[0] > 2:
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
    for dt in idx['index_names']:
        path = os.path.join("/data/sphinx/", name, dt)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError:
                pass

print(config)

