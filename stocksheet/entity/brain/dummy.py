from stocksheet.entity.brain import Brain, BRAINS


@BRAINS.register("dummy")
class BrainDummy(Brain):
    pass
