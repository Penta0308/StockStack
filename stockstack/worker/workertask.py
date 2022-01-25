import enum


class TASK_ID(enum.Enum):
    MARKET_OPEN = enum.auto()
    MARKET_CLOSE = enum.auto()


class WorkerTask:
    pass
