from typing import Dict

import numpy as np

from . import dummy


class BRAINS:
    BRAINS_NAME: Dict[str, "Brain"] = dict()

    @staticmethod
    def register(btype: str):
        def decorator(brain: Brain):
            BRAINS.brain_register(btype, brain)
            return brain

        return decorator

    @staticmethod
    def brain_register(btype: str, brain) -> None:
        if BRAINS.BRAINS_NAME.get(btype) is not None:
            raise KeyError("Conflicting Brain Name")
        BRAINS.BRAINS_NAME[btype] = brain

    @staticmethod
    def brain_lookup(btype: str):
        return BRAINS.BRAINS_NAME[btype]
