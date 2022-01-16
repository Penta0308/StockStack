import json


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
            with open('settings.json', 'r', encoding='utf-8') as f:
                Settings._settings = json.load(f)

    @staticmethod
    def save():
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(Settings._settings, f)

    @staticmethod
    def get():
        if Settings._settings is None:
            Settings.load()
        return Settings._settings

    @staticmethod
    def get_secrets():
        with open('secrets.json', 'r', encoding='utf-8') as f:
            return json.load(f)
