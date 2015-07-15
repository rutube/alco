# coding: utf-8

# $Id: $

# coding: utf-8

# $Id: server.py 2553 2014-06-19 12:37:13Z stikhonov $
import os
import signal
import asyncio

from dvasya.server import ChildProcess, Supervisor, Worker

from alco.collector.collector import Collector


class CollectorChildProcess(ChildProcess):

    def before_loop(self):
        super().before_loop()
        self.loop.add_signal_handler(signal.SIGHUP, self.reload_config)
        self.logger.debug("Test logging")

    def start(self):
        """ Запускает полезную нагрузку worker-процесса."""
        # В отличие от базового класса, не запускает socket-server.
        # Вместо этого запускает цикл сбора данных.
        self.loop = loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def stop():
            self.loop.stop()
            os._exit(0)

        loop.add_signal_handler(signal.SIGINT, stop)

        self.before_loop()

        self.start_collector()

        asyncio.get_event_loop().run_forever()
        os._exit(0)

    def start_collector(self):
        """ Инициирует циклы опроса серверов. """
        Collector.launch(self.loop)

    def reload_config(self, *args, **kwargs):
        pass


class CollectorWorker(Worker):
    child_process_class = CollectorChildProcess


class CollectorSupervisor(Supervisor):
    """ Супервизор для процессов сбора логов

    В отличие от dvasya.server.Supervisor не слушает никаких портов.
    """
    worker_class = CollectorWorker

    def open_socket(self):
        """ Убирает базовый метод открытия сокета."""
        return None

    def prefork(self):
        super().prefork()
        self.init_subscribers()

    def init_subscribers(self):
        self.loop.add_signal_handler(signal.SIGHUP, self.reload_config)

    def reload_config(self):
        self.logger.debug("Forced reloading config")
        for worker in self.workers:
            self.logger.debug("KILL %s %s" % (worker.pid, signal.SIGHUP))
            os.kill(worker.pid, signal.SIGHUP)


