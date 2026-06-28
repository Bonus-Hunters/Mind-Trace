from abc import ABC
from contextlib import asynccontextmanager
from sqlalchemy import select, update
from typing import Any, Type, TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from core.database.models import Base
from sqlalchemy.exc import SQLAlchemyError
import core.database.tables_data as tables_data
import core.database.models as models

"""
    - Should pass in any reposity the session maker from PostgresDatabase
    - Before passing data make sure to pass as dict and key names match the name in tables_data.py 
        - then pass object to funcs as an instance of  tables_data classes 
        - example:
            data = {
                "name": "Project Alpha", ... other fields
            }
            project_data = tables_data.Project(**data)
            project_repo.create(project_data)
            
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

    async def generic_update(self, id: int, data: Any, model_class: Type[T]) -> bool:
        async with self._get_session() as session:
            stmt = select(model_class).where(model_class.id == id)
            result = await session.execute(stmt)
            db_item = result.scalars().first()

            if not db_item:
                return False

            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_item, key, value)

            await session.commit()
            return True


class CompanyRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Company, session_maker)

    async def get_by_id(self, company_id: int) -> Optional[tables_data.Company]:
        async with self._get_session() as session:
            stmt = select(models.Company).where(models.Company.id == company_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_domain(self, domain: str) -> Optional[tables_data.Company]:
        async with self._get_session() as session:
            stmt = select(models.Company).where(models.Company.domain == domain)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[tables_data.Company]:
        async with self._get_session() as session:
            stmt = select(models.Company).where(models.Company.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[tables_data.Company]:
        async with self._get_session() as session:
            stmt = select(models.Company)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def create(self, data: tables_data.Company) -> bool:
        async with self._get_session() as session:
            try:
                new_company = models.Company(**data.model_dump())
                session.add(new_company)
                await session.commit()
                await session.refresh(new_company)
                return new_company.id
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"--- Error creating company: {e} ---")
                return False

    # companis table cannot be altered

    async def delete(self, company_id: int) -> bool:
        async with self._get_session() as session:
            company = await self.get_by_id(company_id)
            if not company:
                print(
                    f"--- Error deleting company: Company with id {company_id} does not exist ---"
                )
                return False
            await session.delete(company)
            await session.commit()
            return True


class ProjectRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Project, session_maker)

    async def get_by_name(self, name: str) -> Optional[tables_data.Project]:
        async with self._get_session() as session:
            stmt = select(models.Project).where(models.Project.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_id(self, id: int) -> Optional[tables_data.Project]:
        async with self._get_session() as session:
            stmt = select(models.Project).where(models.Project.id == id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all_by_company(
        self, company_id: int
    ) -> List[tables_data.Project]:
        async with self._get_session() as session:
            stmt = select(models.Project).where(
                models.Project.company_id == company_id
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def create(self, data: tables_data.Project) -> bool:
        async with self._get_session() as session:
            try:
                company_repo = CompanyRepository(self._session_maker)
                company = await company_repo.get_by_id(data.company_id)
                del company_repo
                if company is None:
                    print(
                        f"--- Error creating project: Company with id {data.company_id} does not exist ---"
                    )
                    return False
                new_project = models.Project(**data.model_dump())
                session.add(new_project)
                await session.commit()
                await session.refresh(new_project)
                return new_project.id
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"--- Error creating project: {e} ---")
                return False

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

    # should pass id of the desired project to update
    async def update(self, id: int, data: tables_data.ProjectUpdate) -> bool:
        async with self._get_session() as session:
            project = await session.scalar(
                select(models.Project).where(models.Project.id == id)
            )

            if not project:
                print(
                    f"--- Error updating project: Project with id {id} does not exist ---"
                )
                return False

            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(project, key, value)

            await session.commit()
            return True


class CategoryMapRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.CategoryMap, session_maker)

    async def create(self, data: tables_data.CategoryMap) -> bool:
        async with self._get_session() as session:
            try:
                company_repo = CompanyRepository(self._session_maker)
                company = await company_repo.get_by_id(data.company_id)
                del company_repo
                if company is None:
                    print(
                        f"--- Error creating category map: Company with id {data.company_id} does not exist ---"
                    )
                    return False
                project_repo = ProjectRepository(self._session_maker)
                project = await project_repo.get_by_name(data.project_name)
                del project_repo
                if project is None:
                    print(
                        f"--- Error creating category map: Project {data.project_name} does not exist ---"
                    )
                    return False
                new_category_map = models.CategoryMap(**data.model_dump())
                session.add(new_category_map)
                await session.commit()
                await session.refresh(new_category_map)
                return new_category_map.id
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

    async def get_type(self, feature_name: str, project_name: str) -> Optional[str]:
        res = await self._get_obj(feature_name, project_name)
        return res.type if res else None

    async def get_by_feature_project_name(
        self, feature_name: str, project_name: str
    ) -> Optional[tables_data.CategoryMap]:
        res = await self._get_obj(feature_name, project_name)
        return res if res else None

    async def update(
        self, feature_name: str, project_name: str, data: tables_data.CategoryMapUpdate
    ) -> bool:
        async with self._get_session() as session:
            obj = await self._get_obj(feature_name, project_name)
            if not obj:
                print(
                    f"--- Error updating category map: Category map {feature_name} in project {project_name} does not exist ---"
                )
                return False
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(obj, key, value)
            await session.commit()
            return True

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


class EmployeesRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Employees, session_maker)

    async def create(self, data: tables_data.Employees) -> bool:
        async with self._get_session() as session:
            try:
                company_repo = CompanyRepository(self._session_maker)
                company = await company_repo.get_by_id(data.company_id)
                del company_repo
                if company is None:
                    print(
                        f"--- Error creating employee: Company with id {data.company_id} does not exist ---"
                    )
                    return False
                new_developer = models.Employee(**data.model_dump())
                session.add(new_developer)
                await session.commit()
                await session.refresh(new_developer)
                return new_developer.id
            except SQLAlchemyError as e:
                print(f"--- Error creating developer: {e} ---")
                await session.rollback()
                return False

    async def _get_obj(self, name: str) -> Optional[tables_data.Employees]:
        async with self._get_session() as session:
            stmt = select(models.Employee).where(models.Employee.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[tables_data.Employees]:
        async with self._get_session() as session:
            res = await self._get_obj(name)
            return res if res else None

    async def get_by_email(self, email: str) -> Optional[tables_data.Employees]:
        async with self._get_session() as session:
            stmt = select(models.Employee).where(models.Employee.email == email)
            result = await session.execute(stmt)
            obj = result.scalars().first()
            return obj if obj else None

    async def get_by_role(self, role: str) -> Optional[List[tables_data.Employees]]:
        async with self._get_session() as session:
            stmt = select(models.Employee).where(models.Employee.role == role)
            result = await session.execute(stmt)
            return result.scalars().all()

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

    async def update(self, name: str, data: tables_data.EmployeeUpdate) -> bool:
        async with self._get_session() as session:
            employee = await self._get_obj(name)

            if not employee:
                print(
                    f"--- Error updating employee: Employee name {name} does not exist ---"
                )
                return False

            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(employee, key, value)

            await session.commit()
            return True

    async def get_all(self, company_id: int):
        async with self._get_session() as session:
            stmt = select(models.Employee).where(
                models.Employee.company_id == company_id
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_all_embeddings(self, company_id: int):
        async with self._get_session() as session:
            results = await self.get_all(company_id)
            return [{i.name: i.voice_print} for i in results]


class MeetingRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.Meeting, session_maker)

    async def create(self, data: tables_data.Meeting):
        async with self._get_session() as session:
            try:
                company_repo = CompanyRepository(self._session_maker)
                company = await company_repo.get_by_id(data.company_id)
                del company_repo
                if company is None:
                    print(
                        f"--- Error creating meeting: Company with id {data.company_id} does not exist ---"
                    )
                    return False
                project_repo = ProjectRepository(self._session_maker)
                project = await project_repo.get_by_name(name=data.project_name)
                del project_repo
                if project is None:
                    print(
                        f"--- Error creating meeting: Project {data.project_name} does not exist ---"
                    )
                    return False
                new_meeting = models.Meeting(**data.model_dump())
                session.add(new_meeting)
                await session.commit()
                await session.refresh(new_meeting)
                return new_meeting.id

            except SQLAlchemyError as e:
                print(f"--- Error creating meeting: {e} ---")
                await session.rollback()
                return False

    async def get_by_id(self, meeting_id: int) -> Optional[tables_data.Meeting]:
        async with self._get_session() as session:
            stmt = select(models.Meeting).where(models.Meeting.id == meeting_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    # returns list because titles may not be unique
    async def get_by_title(self, title: str) -> Optional[List[tables_data.Meeting]]:
        async with self._get_session() as session:
            stmt = select(models.Meeting).where(models.Meeting.title == title)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update(self, meeting_id: int, data: tables_data.MeetingUpdate) -> bool:
        async with self._get_session() as session:
            meeting = await session.scalar(
                select(models.Meeting).where(models.Meeting.id == meeting_id)
            )
            if not meeting:
                print(
                    f"--- Error updating meeting: Meeting ID {meeting_id} does not exist ---"
                )
                return False
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(meeting, key, value)
            await session.commit()
            return True

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

    async def get_all_chunks(
        self, meeting_id: int
    ) -> Optional[List[tables_data.MeetingChunk]]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(
                models.MeetingChunk.meeting_id == meeting_id
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    # eager-loads chunks so they stay accessible after the session closes
    # (relies on expire_on_commit=False set in PostgresDatabase)
    async def get_all(self) -> List[models.Meeting]:
        async with self._get_session() as session:
            stmt = select(models.Meeting).options(
                selectinload(models.Meeting.chunks)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    # same as get_all but scoped to a single company (eager-loads chunks)
    async def get_all_by_company(self, company_id: int) -> List[models.Meeting]:
        async with self._get_session() as session:
            stmt = (
                select(models.Meeting)
                .where(models.Meeting.company_id == company_id)
                .options(selectinload(models.Meeting.chunks))
            )
            result = await session.execute(stmt)
            return result.scalars().all()


class MeetingChunkRepository(BaseRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__(tables_data.MeetingChunk, session_maker)

    async def create(self, data: tables_data.MeetingChunk):
        async with self._get_session() as session:
            try:
                meeting_repo = MeetingRepository(self._session_maker)
                meeting = await meeting_repo.get_by_id(data.meeting_id)
                del meeting_repo
                if meeting is None:
                    print(
                        f"--- Error creating meeting chunk: Meeting {data.meeting_id} does not exist ---"
                    )
                    return False
                new_meeting_chunk = models.MeetingChunk(**data.model_dump())
                session.add(new_meeting_chunk)
                await session.commit()
                await session.refresh(new_meeting_chunk)
                return new_meeting_chunk.id
            except SQLAlchemyError as e:
                print(f"--- Error creating meeting chunk: {e} ---")
                await session.rollback()
                return False

    async def get_by_id(
        self, meeting_chunk_id: int
    ) -> Optional[tables_data.MeetingChunk]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(
                models.MeetingChunk.id == meeting_chunk_id
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_meeting_id(self, chunk_id: int) -> Optional[int]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(models.MeetingChunk.id == chunk_id)
            result = await session.execute(stmt)
            chunk = result.scalars().first()
            return chunk.meeting_id if chunk else None

    async def get_chunk_embedding(self, chunk_id: int) -> Optional[List[float]]:
        async with self._get_session() as session:
            stmt = select(models.MeetingChunk).where(models.MeetingChunk.id == chunk_id)
            result = await session.execute(stmt)
            chunk = result.scalars().first()
            return chunk.embedding if chunk else None

    async def update(
        self, meeting_chunk_id: int, data: tables_data.MeetingChunkUpdate
    ) -> bool:
        async with self._get_session() as session:
            chunk = await session.scalar(
                select(models.MeetingChunk).where(
                    models.MeetingChunk.id == meeting_chunk_id
                )
            )
            if not chunk:
                print(
                    f"--- Error updating meeting chunk: Meeting Chunk ID {meeting_chunk_id} does not exist ---"
                )
                return False
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(chunk, key, value)
            await session.commit()
            return True

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

    async def create(self, data: tables_data.Note) -> bool:
        async with self._get_session() as session:
            try:
                company_repo = CompanyRepository(self._session_maker)
                company = await company_repo.get_by_id(data.company_id)
                del company_repo
                if company is None:
                    print(
                        f"--- Error creating note: Company with id {data.company_id} does not exist ---"
                    )
                proj_repo = ProjectRepository(self._session_maker)
                project = await proj_repo.get_by_name(data.project_name)
                if project is None:
                    print(
                        f"--- Error creating note: Project {data.project_name} does not exist ---"
                    )
                del proj_repo
                dev_repo = EmployeesRepository(self._session_maker)
                developer = await dev_repo.get_by_email(data.author)
                if developer is None:
                    print(
                        f"--- Error creating note: Developer {data.author} does not exist ---"
                    )
                if company is None or project is None or developer is None:
                    return False

                new_note = models.Note(**data.model_dump())
                session.add(new_note)
                await session.commit()
                await session.refresh(new_note)
                return new_note.id
            except SQLAlchemyError as e:
                print(f"--- Error creating note: {e} ---")
                await session.rollback()
                return False
                # working

    async def update(self, note_id: int, data: dict) -> bool:
        async with self._get_session() as session:
            try:
                stmt = (
                    update(models.Note).where(models.Note.id == note_id).values(**data)
                )
                await session.execute(stmt)
                await session.commit()
                return True
            except SQLAlchemyError as e:
                print(f"--- Error updating note: {e} ---")
                await session.rollback()
                return False

    async def get_by_id(self, note_id: int) -> Optional[tables_data.Note]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.id == note_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_note_embedding(self, note_id: int) -> Optional[List[float]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.id == note_id)
            result = await session.execute(stmt)
            note = result.scalars().first()
            return note.embedding if note else None

    async def get_all_by_note_type(
        self, note_type: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.type == note_type)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_all_by_author_name(
        self, author: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.author == author)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_all_by_project_name(
        self, project_name: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.project_name == project_name)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_all_by_function_name(
        self, function_name: str
    ) -> Optional[List[tables_data.Note]]:
        async with self._get_session() as session:
            stmt = select(models.Note).where(models.Note.function == function_name)
            result = await session.execute(stmt)
            return result.scalars().all()

    # async def update(self, note_id: int, data: tables_data.NoteUpdate) -> bool:
    #     async with self._get_session() as session:
    #         note = await session.scalar(
    #             select(models.Note).where(models.Note.id == note_id)
    #         )
    #         if not note:
    #             print(f"--- Error updating note: Note ID {note_id} does not exist ---")
    #             return False
    #         for key, value in data.model_dump(exclude_unset=True).items():
    #             setattr(note, key, value)
    #         await session.commit()
    #         return True

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

    async def create(self, data: tables_data.Task) -> bool:
        async with self._get_session() as session:
            try:
                company_repo = CompanyRepository(self._session_maker)
                company = await company_repo.get_by_id(data.company_id)
                del company_repo
                if company is None:
                    print(
                        f"--- Error creating task: Company with id {data.company_id} does not exist ---"
                    )
                proj_repo = ProjectRepository(self._session_maker)
                project = await proj_repo.get_by_name(data.project_name)
                del proj_repo
                if project is None:
                    print(
                        f"--- Error creating task: Project {data.project_name} does not exist ---"
                    )
                developer = EmployeesRepository(self._session_maker)
                developer = await developer.get_by_name(data.assignee_name)
                if developer is None:
                    print(
                        f"--- Error creating task: Developer {data.assignee_name} does not exist ---"
                    )
                if company is None or project is None or developer is None:
                    return False
                new_task = models.Task(**data.model_dump())
                session.add(new_task)
                await session.commit()
                await session.refresh(new_task)
                return new_task.id
            except SQLAlchemyError as e:
                print(f"--- Error creating task: {e} ---")
                await session.rollback()
                return False

    async def get_by_id(self, task_id: int) -> Optional[tables_data.Task]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(models.Task.id == task_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_status(self, status: str) -> Optional[List[tables_data.Task]]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(models.Task.status == status)
            result = await session.execute(stmt)
            return result.scalars().all()

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

    async def get_all_by_developer(
        self, assignee_name: str
    ) -> Optional[List[tables_data.Task]]:
        async with self._get_session() as session:
            stmt = select(models.Task).where(models.Task.assignee_name == assignee_name)
            result = await session.execute(stmt)
            return result.scalars().all()

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

    async def update(self, task_id: int, data: tables_data.TaskUpdate) -> bool:
        async with self._get_session() as session:
            task = await session.scalar(
                select(models.Task).where(models.Task.id == task_id)
            )
            if not task:
                print(f"--- Error updating task: Task ID {task_id} does not exist ---")
                return False
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(task, key, value)
            await session.commit()
            return True

    async def delete(self, task_id: int) -> bool:
        async with self._get_session() as session:
            obj = await self.get_by_id(task_id)
            if obj is None:
                print(f"--- Error deleting task: Task ID {task_id} does not exist ---")
                return False
            await session.delete(obj)
            await session.commit()
            return True
