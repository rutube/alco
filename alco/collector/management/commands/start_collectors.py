# coding: utf-8

# $Id: $
import os
import signal
from logging import getLogger
from multiprocessing import Process, Queue
from time import sleep

from daemon import DaemonContext
from daemon.pidfile import TimeoutPIDLockFile
from django.core.management import BaseCommand
from logutils.queue import QueueListener

from alco.collector.collector import Collector
from alco.collector.models import LoggerIndex

logger = getLogger('alco.collector')


def file_handles(logger):
    """ Get a list of filehandle numbers from logger
        to be handed to DaemonContext.files_preserve
    """
    handles = []
    for handler in logger.handlers:
        try:
            handles.append(handler.stream.fileno())
        except AttributeError:
            pass
    if logger.parent:
        handles += file_handles(logger.parent)
    return handles


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout=stdout, stderr=stderr,
                                      no_color=no_color)
        self.processes = {}
        self.started = False
        self.logging_queue = self.logging_listener = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-daemon', action='store_false', dest='daemon',
            default=True, help="Don't daemonize process")
        parser.add_argument(
            '--pidfile', action='store', dest='pidfile',
            default="collector.pid", help="pidfile location")
        parser.add_argument(
            '--index', action='store', dest='index',
            default=None, help='index id'
        )

    def handle(self, *args, **options):
        if options['index']:
            index = LoggerIndex.objects.get(id=int(options['index']))
            c = Collector(index)
            c()
            return

        if not options['daemon']:
            return self.start_worker_pool()

        path = os.path.join(os.getcwd(), options['pidfile'])
        pidfile = TimeoutPIDLockFile(path)
        log_files = file_handles(logger)
        context = DaemonContext(pidfile=pidfile, files_preserve=log_files)

        with context:
            logger.info("daemonized")
            self.start_worker_pool()

    def start_worker_pool(self):
        self.start_mp_logging()
        indices = list(LoggerIndex.objects.all())
        logger.info("Starting worker pool with %s indexers" % len(indices))
        n = 0
        self.started = True
        for index in indices:
            for i in range(index.num_processes):
                c = Collector(index)
                p = Process(target=c)
                p.start()
                logger.info("Indexer for %s#%s started pid=%s" %
                            (index.name, i, p.pid))
                self.processes[n] = (p, index)
                n += 1
        signal.signal(signal.SIGINT, self.handle_sigint)

        while len(self.processes) > 0:
            if not self.started:
                logger.info("Stopping indexers")
                for n in self.processes:
                    (p, index) = self.processes[n]
                    os.kill(p.pid, signal.SIGTERM)
            sleep(0.5)
            for n in list(self.processes):
                (p, index) = self.processes[n]
                if p.exitcode is None:
                    if not p.is_alive() and self.started:
                        logger.debug("Indexer with pid %s not finished "
                                     "and not running" % p.pid)
                        # Not finished and not running
                        os.kill(p.pid, signal.SIGKILL)
                        c = Collector(index)
                        p = Process(target=c)
                        p.start()
                        logger.warning("Indexer for %s restarted pid=%s"
                                       % (index.name, p.pid))
                        self.processes[n] = (p, index)
                elif p.exitcode != 0 and self.started:
                    logger.warning('Process %s exited with an error '
                                   'or terminated' % p.pid)
                    c = Collector(index)
                    p = Process(target=c)
                    p.start()
                    self.processes[n] = (p, index)
                elif p.exitcode != 0:
                    logger.warning("Process %s exited with return code %s while"
                                   " terminating" % (p.pid, p.exitcode))
                    p.join()
                    del self.processes[n]
                else:
                    logger.debug('Process %s exited correctly' % p.pid)
                    p.join()
                    del self.processes[n]

        self.stop_mp_logging()

    def handle_sigint(self, sig_num, frame):
        logger.info("Got signal %s, stopping" % sig_num)
        self.started = False

    def start_mp_logging(self):
        logger.debug("Start listening child logs")
        self.logging_queue = Queue()
        handlers = logger.handlers
        self.logging_listener = QueueListener(self.logging_queue, *handlers)
        self.logging_listener.start()

    def stop_mp_logging(self):
        logger.debug("Stop listening child logs")
        self.logging_listener.stop()

