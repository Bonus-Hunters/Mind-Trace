from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from core.config_loader import DatabaseConfigLoader


class PostgresDatabase:

    def __init__(self):
        configer = DatabaseConfigLoader()
        if configer is None:
            raise Exception("DatabaseConfigLoader is not initialized")
        DATABASE_URL = configer.get("DATABASE_URL")
        self.username = configer.get("POSTGRES_USER")
        self.password = configer.get("POSTGRES_PASSWORD")
        self.port = configer.get("POSTGRPGPORTES_PORT")
        self.database_name = configer.get("POSTGRES_DB")
        self.host = "localhost"
        self.engine = create_async_engine(DATABASE_URL)
        self._session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    def get_engine(self):
        return self.engine

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        return self._session_maker
