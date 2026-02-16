import pprint
import asyncio, warnings
from datetime import datetime
from backend.core.config_loader import ConfigLoader, DatabaseConfigLoader
from backend.core.database.postgresDatabase import PostgresDatabase
from backend.core.database.repos import (
    ProjectRepository,
    EmployeesRepository,
    CategoryMapRepository,
    NoteRepository,
    TaskRepository,
    MeetingRepository,
    MeetingChunkRepository,
)
from backend.core.database.tables_data import (
    Project,
    Meeting,
    MeetingChunk,
    Employees,
    CategoryMap,
    Note,
    Task,
)


warnings.filterwarnings("ignore")
database = PostgresDatabase()
if database is None:
    print("--- Error [main.py]: PostgresDatabase instance is None ---")
async_session_maker = database.get_session_maker()

print("--- Initializing Repositories ---")
project_repo = ProjectRepository(async_session_maker)
developer_repo = EmployeesRepository(async_session_maker)
category_map_repo = CategoryMapRepository(async_session_maker)
note_repo = NoteRepository(async_session_maker)
task_repo = TaskRepository(async_session_maker)
meeting_repo = MeetingRepository(async_session_maker)
meeting_chunk_repo = MeetingChunkRepository(async_session_maker)

meeting_data = {
    "title": "Projeaaaaickoff",
    "date": "2024-10-01",
    "language": "en",
    "duration_sec": 3600,
    "project_name": "Test Project2",
    "meta": {"location": "Zoom", "organizer": "Alice"},
}

print("--- Repositories Created ---")

print(" --- starting to test project repo")
embedding = [0.0] * 1536


# try:
#     project_data = Project(project_data)
# except Exception as e:
#     print(f"--- Error creating Project instance: {e} ---")


# tmp = Task(**task1)

# print(tmp)
# print("------------[]")
# print(tmp.description)


async def test2():
    return await meeting_repo.create(Meeting(**meeting_data))


# async def test():
#     obj1 = await task_repo.delete(1)
#     return obj1


# # asyncio.run(test())

id = asyncio.run(test2())
print(f"Created meeting with ID: {id}")
# for p in proj:
#     print(p.project_name)
# pprint.pprint(proj)

# if proj is None:
#     print(" --- project not found --- ")
# else:
#     print(" --- project found --- ")
# asyncio.run(test())


print(" --- project repo working fine")
