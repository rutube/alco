from setuptools import setup

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

setup(
    name='alco',
    version='2.5.2',
    long_description=read_md('README.md'),
    packages=['alco',
              'alco.grep',
              'alco.grep.api',
              'alco.grep.migrations',
              'alco.grep.templatetags',
              'alco.collector',
              'alco.collector.api',
              'alco.collector.management',
              'alco.collector.management.commands',
              'alco.collector.migrations',
    ],
    url='https://github.com/rutube/alco',
    include_package_data=True,
    package_data={
        'alco': [
            'alco/collector/templates/',
            'alco/grep/templates/',
            'alco/grep/static/',
        ],
    },
    install_requires=[
        'Django>=1.8',
        'djangorestframework>=3.1',
        'dateutils',
        'django-filter>=0.10.0',
        'django-mass-edit',
        'jsonfield',
        'python-daemon',
        'redis',
        'pyrabbit',
        'django_sphinxsearch',
        'ujson',
        'librabbitmq',
        'logutils',
    ],
    license='Beerware',
    author='tumbler',
    author_email='zimbler@gmail.com',
    description='Autonomous Log Collector and Observer'
)
