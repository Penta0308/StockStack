import multiprocessing
import psycopg

from stocksheet.settings import Settings


class WorkerClass:
    @staticmethod
    def _workerstart(dbinfo: dict, q: multiprocessing.Queue):
        worker = WorkerClass(psycopg.connect(**dbinfo), q)
        worker.run()

    def __init__(self, dbconn: psycopg.connection, q: multiprocessing.Queue):
        self.__dbconn = dbconn
        self.q = q
        self._logger = Settings.get_logger()

    def run(self):
        run = True
        while run:
            task = self.q.get()
            self._logger.debug(task)
