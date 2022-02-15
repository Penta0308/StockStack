import json
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from stockstack.world.market import Market


class Settings:
    _settings = None

    logger = None
    markets: Dict[str, "Market"] = dict()

    @staticmethod
    def load():
        if Settings._settings is None:
            with open("config/settings.json", "r", encoding="utf-8") as f:
                Settings._settings = json.load(f)

    @staticmethod
    def get():
        if Settings._settings is None:
            Settings.load()
        return Settings._settings
