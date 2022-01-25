import typing

from stockstack.worker.workerprocess import WorkerProcess


class WorkerManager:
    def __init__(self, dbinfo: dict):
        self._dbinfo = dbinfo
        self._workerlut = dict()

    def workers_get(self, marketident: typing.Hashable):
        return self._workerlut.get(marketident)

    def workers_create(self, marketident: typing.Hashable):
        if self.workers_get(marketident) is not None:
            raise AttributeError('Market already exists')
        workerprocess = WorkerProcess(self._dbinfo)
        workerprocess.start()
        self._workerlut[marketident] = workerprocess
        return workerprocess
