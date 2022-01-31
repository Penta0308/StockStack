import json

class Settings:
    _settings = None
    templateenv = None

    maincontext = None

    logger = None

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
