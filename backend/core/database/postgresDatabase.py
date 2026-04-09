from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from core.config_loader import DatabaseConfigLoader


class PostgresDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._init()
            cls._instance = instance
        return cls._instance

    def _init(self):
        config = DatabaseConfigLoader()
        if config is None:
            raise Exception(
                "DatabaseConfigLoader instance is None [postgresDatabase.py]"
            )
        self.DATABASE_URL = config.get("DATABASE_URL")
        self.username = config.get("POSTGRES_USER")
        self.password = config.get("POSTGRES_PASSWORD")
        self.port = config.get("PGPORT")
        self.database_name = config.get("POSTGRES_DB")
        self.host = "localhost"

        self._engine = create_async_engine(self.DATABASE_URL)
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    def get_engine(self):
        return self._engine

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        return self._session_maker
