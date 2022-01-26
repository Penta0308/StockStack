import multiprocessing

from stocksheet.worker.workerclass import WorkerClass
from stocksheet.worker.workertask import WorkerTask


class WorkerProcess:
    def __init__(self, dbinfo: dict):
        self.q = multiprocessing.Queue()
        # noinspection PyProtectedMember
        self.p = multiprocessing.Process(target=WorkerClass._workerstart, args=(dbinfo, self.q), daemon=True)

    def queue(self, task: WorkerTask):
        self.q.put(task)

    def start(self):
        self.p.start()

    def kill(self):
        self.p.kill()

    def close(self):
        self.p.close()
