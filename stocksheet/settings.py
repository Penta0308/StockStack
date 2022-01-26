import json

SPECIAL_WORDS = [
    "stsk_"
]


class Settings:
    _settings = None
    _globalr = None

    @staticmethod
    def maincontext_put(globalr):
        Settings._globalr = globalr

    @staticmethod
    def maincontext_get():
        return Settings._globalr

    @staticmethod
    def load():
        if Settings._settings is None:
            with open('config/settings.json', 'r', encoding='utf-8') as f:
                Settings._settings = json.load(f)

    @staticmethod
    def get():
        if Settings._settings is None:
            Settings.load()
        return Settings._settings
