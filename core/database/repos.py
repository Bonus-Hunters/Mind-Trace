from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from unicodedata import name
from sqlalchemy import extract, select, update, delete
from typing import Any, Type, TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from database.models import Base, Project
from postgresDatabase import PostgresDatabase
import tables_data


"""
    - Should pass in any reposity the session maker from PostgresDatabase
    - Before passing data make sure to pass as dict and key names match the name in tables_data.py 
    - As for embedding features, pass as List[float] -> embed it beforehand
"""


# generic type for models to shorten code
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):

    def __init__(self, model: Type[T], session_maker: async_sessionmaker[AsyncSession]):
        self.model = model
        self._session_maker = session_maker

    @asynccontextmanager
    async def _get_session(self):
        session = self._session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def _flush(self):
        await self._session_maker().flush()

    # should pass which col -> from tables_data models [one col only]
    async def get_by_unique_feature(
        self, id: Any, id_col: str | int
    ) -> Optional[List[T]] | Optional[T]:
        async with self._get_session() as session:
            stmt = select(self.model).where(self.model.id_col == id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def create(self, data: T) -> T:
        async with self._get_session() as session:
            new_project = Project(**data.model_dump())
            session.add(new_project)
            return new_project

    async def get_all(
        self, offset, skip: int = 0, limit: int = 100, **filters
    ) -> List[T]:
        async with self._get_session() as session:
            stmt = select(self.model).filter_by(**filters)
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)

            result = await session.execute(stmt)
            return result.scalars().all()


class ProjectRepository(BaseRepository):
    def __init__(self, db: PostgresDatabase):
        super().__init__(db)

    # async def update_by_name(
    #     self, name: str, **updates
    # ) -> Optional[tables_data.Project]:
    #     async with self._get_session() as session:
    #         stmt = (
    #             update(tables_data.Project)
    #             .where(tables_data.Project.name == name)
    #             .values(**updates)
    #             .returning(tables_data.Project)
    #         )
    #         result = await session.execute(stmt)
    #         self._flush()
    #         return result.scalars().first()

    async def get_by_name(self, name: str) -> tables_data.Project | None:
        async with self._get_session() as session:
            stmt = select(tables_data.Project).where(tables_data.Project.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def delete_by_name(self, name: str) -> bool:
        async with self._get_session() as session:
            stmt = delete(tables_data.Project).where(tables_data.Project.name == name)
            result = await session.execute(stmt)
            return result.rowcount > 0


class CategoryMapRepository(BaseRepository):
    def __init__(self, db: PostgresDatabase):
        super().__init__(db)

    async def get_type(
        self, feature_name: str, project_name: str
    ) -> Optional[tables_data.CategoryMap]:
        async with self._get_session() as session:
            stmt = select(tables_data.CategoryMap).where(
                tables_data.CategoryMap.name == feature_name,
                tables_data.CategoryMap.project_name == project_name,
            )
            result = await session.execute(stmt)
            return result.scalars().first()


class DeveloperRepository(BaseRepository):
    def __init__(self, db: PostgresDatabase):
        super().__init__(db)

    async def get_by_name(self, name: str) -> Optional[tables_data.Developer]:
        async with self._get_session() as session:
            stmt = select(tables_data.Developer).where(
                tables_data.Developer.name == name
            )
            result = await session.execute(stmt)
            return result.scalars().first()


class MeetingRepository(BaseRepository):
    def __init__(self, db: PostgresDatabase):
        super().__init__(db)


class MeetingChunkRepository(BaseRepository):
    def __init__(self, db: PostgresDatabase):
        super().__init__(db)


class NoteRepository(BaseRepository):
    def __init__(self, db: PostgresDatabase):
        super().__init__(db)


class TaskRepository(BaseRepository):
    def __init__(self, db: PostgresDatabase):
        super().__init__(db)
