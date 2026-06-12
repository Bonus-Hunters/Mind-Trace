import os
from pathlib import Path

from dotenv import load_dotenv


class DatabaseConfigLoader:
    _instance = None
    current_dir = Path(__file__).resolve().parent.parent

    def __new__(cls):
        if cls._instance is None:
            instance = super(DatabaseConfigLoader, cls).__new__(cls)
            instance._load_config()
            cls._instance = instance
        return cls._instance

    # load variables from .env file only once
    def _load_config(self):
        env_file = self.current_dir / "docker" / "postgres" / "postgres.env"

        if os.path.exists(env_file):
            load_dotenv(dotenv_path=env_file)
        else:
            print(f"--- Warning [config_loader.py]: {env_file} not found ---")

    def get(self, key, default=None):
        return getattr(self, key.lower(), os.getenv(key, default))


class ConfigLoader:
    _instance = None
    current_dir = Path(__file__).resolve().parent.parent

    def __new__(cls):
        if cls._instance is None:
            instance = super(ConfigLoader, cls).__new__(cls)
            instance._load_config()
            cls._instance = instance
        return cls._instance

    # load variables from .env file only once
    def _load_config(self):
        env_file = self.current_dir / ".env"
        if os.path.exists(env_file):
            load_dotenv(dotenv_path=env_file)
        else:
            print(f"--- Warning [config_loader.py]: {env_file} not found ---")

    def get(self, key, default=None):
        return getattr(self, key.lower(), os.getenv(key, default))
