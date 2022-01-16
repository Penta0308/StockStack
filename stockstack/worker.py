import multiprocessing
import psycopg


class WorkerProcess:
    def __init__(self, dbinfo: dict):
        self.q = multiprocessing.Queue()
        self.p = multiprocessing.Process(target=Worker._workerstart, args=(dbinfo, self.q), daemon=True)

    def queue(self, task):
        self.q.put(task)

    def start(self):
        self.p.start()

    def kill(self):
        self.p.kill()

    def close(self):
        self.p.close()




class Worker:
    @staticmethod
    def _workerstart(dbinfo: dict, q: multiprocessing.Queue):
        worker = Worker(psycopg.connect(**dbinfo), q)

    def __init__(self, dbconn, q):
        self.__dbconn = dbconn
        self.q = q
