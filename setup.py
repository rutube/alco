from setuptools import setup

setup(
    name='alco',
    version='0.0.3',
    packages=['alco',
              'alco.grep',
              'alco.grep.api',
              'alco.collector',
              'alco.collector.api',
              'alco.collector.management',
              'alco.collector.management.commands'
    ],
    url='https://github.com/tumb1er/alco',
    include_package_data=True,
    package_data={
        'alco': ['alco/templates/'],
    },
    install_requires=[
        'Django>=1.8',
        'djangorestframework>=3.1',
        'dateutils',
        'django-filter',
        'jsonfield',
        'python-daemon',
        'redis',
        # 'django_sphinxsearch',
    ],
    license='Beer license',
    author='tumbler',
    author_email='zimbler@gmail.com',
    description='Autonomous Log Collector and Observer'
)
