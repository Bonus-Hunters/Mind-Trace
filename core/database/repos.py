from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from unicodedata import name
import uuid
from sqlalchemy import extract, select, update, delete
from typing import Any, Type, TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from core.database.models import Base
from sqlalchemy.exc import SQLAlchemyError
from core.database.postgresDatabase import PostgresDatabase
import core.database.tables_data as tables_data
import core.database.models as models

"""
    - Should pass in any reposity the session maker from PostgresDatabase
    - Before passing data make sure to pass as dict and key names match the name in tables_data.py 
    - As for embedding features, pass as List[float] -> embed it beforehand
    - emedding size is saved in utils/constants.py as EMBEDDING_SIZE
    - gonnna handle update function later 
"""


# generic type for models to shorten code
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T], ABC):

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


class ProjectRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Project, session_maker)

    # wokring
    async def get_by_name(self, name: str) -> Optional[tables_data.Project]:
        async with self._get_session() as session:
            stmt = select(models.Project).where(models.Project.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    # wokring
    async def create(self, data: tables_data.Project) -> bool:
        async with self._get_session() as session:
            try:
                new_project = models.Project(**data.model_dump())
                session.add(new_project)
                await session.commit()
                return True
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"--- Error creating project: {e} ---")
                return False

    # wokring
    async def delete_by_name(self, name: str) -> bool:
        async with self._get_session() as session:
            project = await session.scalar(
                select(models.Project).where(models.Project.name == name)
            )

            if not project:
                return False

            await session.delete(project)
            await session.commit()
            return True


class CategoryMapRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.CategoryMap, session_maker)

    # working
    async def create(self, data: tables_data.CategoryMap) -> bool:
        async with self._get_session() as session:
            try:
                project = ProjectRepository.get_by_name(data.project_name)
                if project is None:
                    print(
                        f"--- Error creating category map: Project {data.project_name} does not exist ---"
                    )
                    return False
                new_category_map = models.CategoryMap(**data.model_dump())
                session.add(new_category_map)
                await session.commit()
                return True
            except SQLAlchemyError as e:
                print(f"--- Error creating category map: {e} ---")
                await session.rollback()
                return False

    async def _get_obj(
        self, feature_name: str, project_name: str
    ) -> Optional[tables_data.CategoryMap]:
        async with self._get_session() as session:
            stmt = select(models.CategoryMap).where(
                models.CategoryMap.name == feature_name,
                models.CategoryMap.project_name == project_name,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    # wokring
    async def get_type(self, feature_name: str, project_name: str) -> Optional[str]:
        res = await self._get_obj(feature_name, project_name)
        return res.type if res else None

    async def get_by_feature_project_name(
        self, feature_name: str, project_name: str
    ) -> Optional[tables_data.CategoryMap]:
        res = await self._get_obj(feature_name, project_name)
        return res if res else None

    # working
    async def delete(self, feature_name: str, project_name: str) -> bool:
        async with self._get_session() as session:
            res = await self._get_obj(feature_name, project_name)

            if not res:
                print(
                    f"--- Error deleting category map: Category map {feature_name} in project {project_name} does not exist ---"
                )
                return False

            await session.delete(res)
            await session.commit()
            return True


class DeveloperRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Developer, session_maker)

    # working
    async def create(self, data: tables_data.Developer) -> bool:
        async with self._get_session() as session:
            try:
                new_developer = models.Developer(**data.model_dump())
                session.add(new_developer)
                await session.commit()
                return True
            except SQLAlchemyError as e:
                print(f"--- Error creating developer: {e} ---")
                await session.rollback()
                return False

    async def _get_obj(self, name: str) -> Optional[tables_data.Developer]:
        async with self._get_session() as session:
            stmt = select(models.Developer).where(models.Developer.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    # working
    async def get_by_name(self, name: str) -> Optional[tables_data.Developer]:
        async with self._get_session() as session:
            res = await self._get_obj(name)
            return res if res else None

    # working
    async def get_by_role(self, role: str) -> Optional[List[tables_data.Developer]]:
        async with self._get_session() as session:
            stmt = select(models.Developer).where(models.Developer.role == role)
            result = await session.execute(stmt)
            return result.scalars().all()

    # working
    async def delete(self, name: str) -> bool:
        async with self._get_session() as session:
            res = await self._get_obj(name)
            if not res:
                print(
                    f"--- Error deleting developer: Developer name {name} does not exist ---"
                )
                return False

            await session.delete(res)
            await session.commit()
            return True


class MeetingRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Meeting, session_maker)

    # workind
    async def create(self, data: tables_data.Meeting):
        async with self._get_session() as session:
            try:
                project_repo = ProjectRepository(self._session_maker)
                project = await project_repo.get_by_name(name=data.project_name)
                if project is None:
                    print(
                        f"--- Error creating meeting: Project {data.project_name} does not exist ---"
                    )
                    return False
                new_meeting = models.Meeting(**data.model_dump())
                session.add(new_meeting)
                await session.commit()
            except SQLAlchemyError as e:
                print(f"--- Error creating meeting: {e} ---")
                await session.rollback()
                return False
            return True

    # wokring
    async def get_by_id(self, meeting_id: int) -> Optional[tables_data.Meeting]:
        async with self._get_session() as session:
            stmt = select(models.Meeting).where(models.Meeting.id == meeting_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    # working
    # returns list because titles may not be unique
    async def get_by_title(self, title: str) -> Optional[List[tables_data.Meeting]]:
        async with self._get_session() as session:
            stmt = select(models.Meeting).where(models.Meeting.title == title)
            result = await session.execute(stmt)
            return result.scalars().all()

    # working
    async def delete(self, meeting_id: int) -> bool:
        async with self._get_session() as session:
            obj = await self.get_by_id(meeting_id)
            if obj is None:
                print(
                    f"--- Error deleting meeting: Meeting ID {meeting_id} does not exist ---"
                )
                return False
            await session.delete(obj)
            await session.commit()
            return True

    """
        check if there are not chunks found after function call with 
            if no return_value:
            -> no chunks found
    """

    # working
    async def get_all_chunks(
        self, meeting_id: int
    ) -> Optional[List[tables_data.MeetingChunk]]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(
                models.MeetingChunk.meeting_id == meeting_id
            )
            result = await session.execute(stmt)
            return result.scalars().all()


class MeetingChunkRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.MeetingChunk, session_maker)

    # working
    async def create(self, data: tables_data.MeetingChunk):
        async with self._get_session() as session:
            try:
                meeting_repo = MeetingRepository(self._session_maker)
                meeting = await meeting_repo.get_by_id(data.meeting_id)
                if meeting is None:
                    print(
                        f"--- Error creating meeting chunk: Meeting {data.meeting_id} does not exist ---"
                    )
                    return False
                new_meeting_chunk = models.MeetingChunk(**data.model_dump())
                session.add(new_meeting_chunk)
                await session.commit()
            except SQLAlchemyError as e:
                print(f"--- Error creating meeting chunk: {e} ---")
                await session.rollback()
                return False
            return True

    # working
    async def get_by_id(
        self, meeting_chunk_id: int
    ) -> Optional[tables_data.MeetingChunk]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(
                models.MeetingChunk.id == meeting_chunk_id
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    # working
    async def get_meeting_id(self, chunk_id: int) -> Optional[int]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(models.MeetingChunk.id == chunk_id)
            result = await session.execute(stmt)
            chunk = result.scalars().first()
            return chunk.meeting_id if chunk else None

    # working
    async def get_chunk_embedding(self, chunk_id: int) -> Optional[List[float]]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(models.MeetingChunk.id == chunk_id)
            result = await session.execute(stmt)
            chunk = result.scalars().first()
            return chunk.embedding if chunk else None

    # working
    async def delete(self, meeting_chunk_id: int) -> bool:
        async with self._get_session() as session:
            obj = await self.get_by_id(meeting_chunk_id)
            if obj is None:
                print(
                    f"--- Error deleting meeting chunk: Meeting Chunk ID {meeting_chunk_id} does not exist ---"
                )
                return False
            await session.delete(obj)
            await session.commit()
            return True


class NoteRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Note, session_maker)

    # working
    async def create(self, data: tables_data.Note) -> bool:
        async with self._get_session() as session:
            try:
                proj_repo = ProjectRepository(self._session_maker)
                project = await proj_repo.get_by_name(data.project_name)
                if project is None:
                    print(
                        f"--- Error creating note: Project {data.project_name} does not exist ---"
                    )
                dev_repo = DeveloperRepository(self._session_maker)
                developer = await dev_repo.get_by_name(data.author)
                if developer is None:
                    print(
                        f"--- Error creating note: Developer {data.author} does not exist ---"
                    )
                if project is None or developer is None:
                    return False

                new_note = models.Note(**data.model_dump())
                session.add(new_note)
                await session.commit()
                return True
            except SQLAlchemyError as e:
                print(f"--- Error creating note: {e} ---")
                await session.rollback()
                return False

    # wokring
    async def get_by_id(self, note_id: int) -> Optional[tables_data.Note]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.id == note_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    # wokring
    async def get_note_embedding(self, note_id: int) -> Optional[List[float]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.id == note_id)
            result = await session.execute(stmt)
            note = result.scalars().first()
            return note.embedding if note else None

    # wokring
    async def get_all_by_note_type(
        self, note_type: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.type == note_type)
            result = await session.execute(stmt)
            return result.scalars().all()

    # wokring
    async def get_all_by_author_name(
        self, author: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.author == author)
            result = await session.execute(stmt)
            return result.scalars().all()

    # wokring
    async def get_all_by_project_name(
        self, project_name: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.project_name == project_name)
            result = await session.execute(stmt)
            return result.scalars().all()

    # wokring
    async def get_all_by_function_name(
        self, function_name: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.function == function_name)
            result = await session.execute(stmt)
            return result.scalars().all()

    # working
    async def delete(self, note_id: int) -> bool:
        async with self._get_session() as session:
            obj = await self.get_by_id(note_id)
            if obj is None:
                print(f"--- Error deleting note: Note ID {note_id} does not exist ---")
                return False
            await session.delete(obj)
            await session.commit()
            return True


class TaskRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Task, session_maker)

    # working
    async def create(self, data: tables_data.Task) -> bool:
        async with self._get_session() as session:
            try:
                proj_repo = ProjectRepository(self._session_maker)
                project = await proj_repo.get_by_name(data.project_name)
                if project is None:
                    print(
                        f"--- Error creating task: Project {data.project_name} does not exist ---"
                    )
                developer = DeveloperRepository(self._session_maker)
                developer = await developer.get_by_name(data.assignee_name)
                if developer is None:
                    print(
                        f"--- Error creating task: Developer {data.assignee_name} does not exist ---"
                    )
                if project is None or developer is None:
                    return False
                new_task = models.Task(**data.model_dump())
                session.add(new_task)
                await session.commit()
                return True
            except SQLAlchemyError as e:
                print(f"--- Error creating task: {e} ---")
                await session.rollback()
                return False

    # working
    async def get_by_id(self, task_id: int) -> Optional[tables_data.Task]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(models.Task.id == task_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    # working
    async def get_by_status(self, status: str) -> Optional[List[tables_data.Task]]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(models.Task.status == status)
            result = await session.execute(stmt)
            return result.scalars().all()

    # working
    async def get_by_status_in_project(
        self, status: str, project_name: str
    ) -> Optional[List[tables_data.Task]]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(
                models.Task.status == status,
                models.Task.project_name == project_name,
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    # working
    async def get_all_by_developer(
        self, assignee_name: str
    ) -> Optional[List[tables_data.Task]]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(models.Task.assignee_name == assignee_name)
            result = await session.execute(stmt)
            return result.scalars().all()

    # working
    async def get_by_developer_in_project(
        self, assignee_name: str, project_name: str
    ) -> Optional[List[tables_data.Task]]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(
                models.Task.assignee_name == assignee_name,
                models.Task.project_name == project_name,
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    # working
    async def delete(self, task_id: int) -> bool:
        async with self._get_session() as session:
            obj = await self.get_by_id(task_id)
            if obj is None:
                print(f"--- Error deleting task: Task ID {task_id} does not exist ---")
                return False
            await session.delete(obj)
            await session.commit()
            return True
