import asyncio
import glob
import json
import os
from datetime import datetime

from core.database import tables_data
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import (
    CompanyRepository,
    EmployeesRepository,
    NoteRepository,
    ProjectRepository,
)
from core.rag.models import EMBED_MODEL
from langchain_ollama import OllamaEmbeddings
from utils.constants import EMBEDDING_SIZE

FOLDER_PATH = "./dataset/mind-trace-notes"
COMPANY_DOMAIN = "gmail.com"
CREATED_DATE = datetime(2025, 9, 20)
DUMMY_PASSWORD = "changeme"


def email_for(author: str) -> str:
    return f"{author.strip().lower()}@gmail.com"


async def main():
    db = PostgresDatabase()
    sm = db.get_session_maker()
    company_repo = CompanyRepository(sm)
    project_repo = ProjectRepository(sm)
    employee_repo = EmployeesRepository(sm)
    note_repo = NoteRepository(sm)
    embedder = OllamaEmbeddings(model=EMBED_MODEL)

    # --- ensure the gmail.com company exists ---
    company = await company_repo.get_by_domain(COMPANY_DOMAIN)
    if company is None:
        company_id = await company_repo.create(
            tables_data.Company(name=COMPANY_DOMAIN, domain=COMPANY_DOMAIN)
        )
        print(f"Created company '{COMPANY_DOMAIN}' (id={company_id})")
    else:
        company_id = company.id
        print(f"Using existing company '{COMPANY_DOMAIN}' (id={company_id})")

    seen_projects = set()
    seen_authors = {}  # author -> email

    async def ensure_project(project_name: str):
        if project_name in seen_projects:
            return
        existing = await project_repo.get_by_name(project_name)
        if existing is None:
            await project_repo.create(
                tables_data.Project(
                    name=project_name,
                    description=None,
                    delivered=False,
                    created_at=CREATED_DATE,
                    company_id=company_id,
                )
            )
            print(f"Created project '{project_name}'")
        seen_projects.add(project_name)

    async def ensure_employee(author: str) -> str:
        if author in seen_authors:
            return seen_authors[author]
        email = email_for(author)
        existing = await employee_repo.get_by_email(email)
        if existing is None:
            await employee_repo.create(
                tables_data.Employees(
                    name=author,
                    email=email,
                    password=DUMMY_PASSWORD,
                    role=None,
                    skills=[],
                    voice_print=[0.0] * EMBEDDING_SIZE,
                    company_id=company_id,
                )
            )
            print(f"Created employee '{author}' ({email})")
        seen_authors[author] = email
        return email

    files = glob.glob(os.path.join(FOLDER_PATH, "*.json"))
    if not files:
        print(f"No JSON files found in {FOLDER_PATH}")
        return

    created = 0
    failed = 0
    for path in files:
        print(f"\n--- Processing {os.path.basename(path)} ---")
        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for rec in records:
            try:
                await ensure_project(rec["project_name"])
                author_email = await ensure_employee(rec["author"])

                function = rec.get("function")
                if function in (None, "null"):
                    function = None

                tags = rec.get("tags")
                if isinstance(tags, list):
                    tags = ", ".join(tags)

                embedding = embedder.embed_query(rec["note_text"])

                note = tables_data.Note(
                    note_text=rec["note_text"],
                    project_name=rec["project_name"],
                    type=rec["type"],
                    tags=tags,
                    function=function,
                    file_name=rec.get("file_name"),
                    module=rec.get("module"),
                    line_number=None,
                    title=None,
                    embedding=embedding,
                    meta={},
                    author=author_email,
                    date=CREATED_DATE,
                    company_id=company_id,
                )

                note_id = await note_repo.create(note)
                if note_id:
                    created += 1
                    print(f"  + Note created (id={note_id})")
                else:
                    failed += 1
                    print(f"  ! Note creation failed (author={author_email})")
            except Exception as e:
                failed += 1
                print(f"  ! Error ingesting note: {e}")

    print(
        f"\n=== Done: {len(files)} file(s), {created} note(s) created, {failed} failed ==="
    )


if __name__ == "__main__":
    asyncio.run(main())
