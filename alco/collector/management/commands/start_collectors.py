# coding: utf-8

# $Id: $
import os
from time import sleep
from daemon import DaemonContext
from daemon.pidfile import TimeoutPIDLockFile

from django.core.management import BaseCommand
from django.utils.log import getLogger
from multiprocessing import Process
import signal
from alco.collector.collector import Collector
from alco.collector.models import LoggerIndex

logger = getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout=None, stderr=None, no_color=False)
        self.processes = {}
        self.started = False

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-daemon', action='store_false', dest='daemon',
            default=True, help="Don't daemonize process")
        parser.add_argument(
            '--pidfile', action='store', dest='pidfile',
            default="collector.pid", help="pidfile location")

    def handle(self, *args, **options):
        if not options['daemon']:
            return self.start_worker_pool()

        path = os.path.join(os.getcwd(), options['pidfile'])
        pidfile = TimeoutPIDLockFile(path)

        with DaemonContext(pidfile=pidfile):
            logger.info("daemonized")
            self.start_worker_pool()

    def start_worker_pool(self):
        indices = list(LoggerIndex.objects.all())
        n = 0
        for index in indices:
            c = Collector(index)
            p = Process(target=c)
            p.start()
            self.processes[n] = (p, index)
            n += 1
        self.started = True
        signal.signal(signal.SIGINT, self.handle_sigint)

        while len(self.processes) > 0:
            if not self.started:
                for n in self.processes:
                    (p, index) = self.processes[n]
                    os.kill(p.pid, signal.SIGTERM)
            sleep(0.5)
            for n in list(self.processes):
                (p, index) = self.processes[n]
                if p.exitcode is None:
                    if not p.is_alive() and self.started:
                        # Not finished and not running
                        os.kill(p.pid, signal.SIGKILL)
                        c = Collector(index)
                        p = Process(target=c)
                        p.start()
                        self.processes[n] = (p, index)
                elif p.exitcode < 0 and self.started:
                    print('Process Ended with an error or a terminate', index)
                    c = Collector(index)
                    p = Process(target=c)
                    p.start()
                    self.processes[n] = (p, index)
                else:
                    print(index, 'finished')
                    p.join()
                    del self.processes[n]

    def handle_sigint(self, sig_num, frame):
        self.started = False

