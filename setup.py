from distutils.core import setup

setup(
    name='alco',
    version='0.0.1',
    packages=['alco', 'alco.grep', 'alco.grep.api', 'alco.collector',
              'alco.collector.management', 'alco.collector.management.commands',
              'alco.collector.templatetags'],
    url='https://github.com/tumb1er/alco',
    license='Beer license',
    author='tumbler',
    author_email='zimbler@gmail.com',
    description='Autonomous Log Collector and Observer'
)
