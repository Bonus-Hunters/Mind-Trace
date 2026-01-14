import os, logging
from dotenv import load_dotenv


class DatabaseConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    # load variables from .env file only once
    def _load_config(self):
        env_file = f"docker/postgres/postgres.env"

        if os.path.exists(env_file):
            load_dotenv(dotenv_path=env_file)
        else:
            print(f"--- Warning [config_loader.py]: {env_file} not found ---")

    def get(self, key, default=None):
        return getattr(self, key.lower(), os.getenv(key, default))


class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    # load variables from .env file only once
    def _load_config(self):
        load_dotenv()

    def get(self, key, default=None):
        return getattr(self, key.lower(), os.getenv(key, default))
