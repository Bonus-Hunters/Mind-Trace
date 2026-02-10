import pprint
import asyncio, warnings
from datetime import datetime
from core.config_loader import ConfigLoader, DatabaseConfigLoader
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import (
    ProjectRepository,
    EmployeesRepository,
    CategoryMapRepository,
    NoteRepository,
    TaskRepository,
    MeetingRepository,
    MeetingChunkRepository,
)
from core.database.tables_data import (
    Project,
    Meeting,
    MeetingChunk,
    Employees,
    CategoryMap,
    Note,
    Task,
)
from utils.constants import EMBEDDING_SIZE
from utils.enums import (
    CategoryType,
    NoteType,
    DeveloperRole,
    TaskSourceType,
    TaskStatus,
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

print("--- Repositories Created ---")

print(" --- starting to test project repo")
embedding = [0.0] * 1536

task1 = {
    "project_name": "Test Project2",  # Must exist in 'projects' table
    "assignee_name": "hossam",  # Must exist in 'developers' table
    "description": "Refactor the vector search logic to support cosine similarity and increase top_k results to 10.",
    "status": "in_progress",  # Options: todo, in_progress, done
    "source_type": "meeting",  # Origin of the task
}
task2 = {
    "project_name": "Test Project2",
    "assignee_name": "mahmoud",  # Must exist in 'developers' table
    "description": "Refactor the vector search logic to support cosine similarity and increase top_k results to 10.",
    "status": "complited ",  # Options: todo, in_progress, done
    "source_type": "note",  # Origin of the task
}


# try:
#     project_data = Project(project_data)
# except Exception as e:
#     print(f"--- Error creating Project instance: {e} ---")


async def test2():
    await task_repo.create(Task(**task1))
    await task_repo.create(Task(**task2))


async def test():
    obj1 = await task_repo.delete(1)
    return obj1


# asyncio.run(test())

asyncio.run(test2())

# for p in proj:
#     print(p.project_name)
# pprint.pprint(proj)

# if proj is None:
#     print(" --- project not found --- ")
# else:
#     print(" --- project found --- ")
# asyncio.run(test())


print(" --- project repo working fine")
