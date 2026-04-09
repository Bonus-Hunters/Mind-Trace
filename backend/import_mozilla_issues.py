# run mozilla_core_ds.ipynb first to construct the needed json file

import os, json, asyncio, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from utils.constants import EMBEDDING_SIZE
import core.database.tables_data as tables_data
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import (
    NoteRepository,
    CompanyRepository,
    ProjectRepository,
    EmployeesRepository,
)
from langchain_ollama import OllamaEmbeddings
from core.rag.models import EMBED_MODEL


async def import_data():
    file_path = os.path.join(
        os.path.dirname(__file__), "dataset", "mozilla_issues.json"
    )

    with open(file_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    db = PostgresDatabase()
    session_maker = db.get_session_maker()

    company_repo = CompanyRepository(session_maker)
    proj_repo = ProjectRepository(session_maker)
    dev_repo = EmployeesRepository(session_maker)
    note_repo = NoteRepository(session_maker)

    # ensure company exists
    company_id = 1
    company = await company_repo.get_by_id(company_id)
    if not company:
        created_id = await company_repo.create(
            tables_data.Company(name="Mozilla", domain="mozilla.org")
        )
        if created_id:
            company_id = created_id

    # ensure project exists
    project_name = "Mozilla Issues"
    project = await proj_repo.get_by_name(project_name)
    if not project:
        print(f"--- Creating project '{project_name}' for company_id {company_id} ---")
        await proj_repo.create(
            tables_data.Project(name=project_name, company_id=company_id)
        )

    print(f"Importing {len(issues)} issues...")
    for index, issue in enumerate(issues):
        author_val = issue.get("author")
        if not author_val or author_val == "Author not found":
            author_val = "unknown@mozilla.org"

        # The author field on Note actually maps to the email in EmployeesRepository check
        author_email = author_val

        # 3. Ensure Employee (author) exists
        developer = await dev_repo.get_by_email(author_email)
        if not developer:
            await dev_repo.create(
                tables_data.Employees(
                    name=author_val,
                    email=author_email,
                    password="password",
                    role="developer",
                    voice_print=[0.0] * EMBEDDING_SIZE,
                    company_id=company_id,
                )
            )

        tags = issue.get("tags", [])
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

        # Ensure we have date
        created_at = issue.get("created_at")
        if not created_at:
            created_at = datetime.utcnow()
        embeder = OllamaEmbeddings(model=EMBED_MODEL)
        embedding = embeder.embed_query(issue.get("description", ""))

        note = tables_data.Note(
            note_text=issue.get("description", ""),
            project_name=project_name,
            type="issue",
            tags=tags_str,
            module=issue.get("module", ""),
            author=author_email,
            company_id=company_id,
            embedding=embedding,
            date=created_at if isinstance(created_at, datetime) else datetime.utcnow(),
        )

        success = await note_repo.create(note)
        if index % 50 == 0:
            print(f"Processed {index} issues...")

    print("Import completed gracefully.")
    del db
    del company_repo
    del proj_repo
    del dev_repo
    del note_repo


if __name__ == "__main__":
    asyncio.run(import_data())
