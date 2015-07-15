#!/usr/bin/env python
# coding: utf-8

import sys
import os

settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'settings')
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
r = urlopen(SPHINX_CONFIG_URL)
print(r.read().decode('utf-8'))
