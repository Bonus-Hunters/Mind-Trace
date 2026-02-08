from datetime import datetime
from typing import Optional, List
import core 
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import NoteRepository, ProjectRepository, DeveloperRepository
from core.database import tables_data
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from core.rag.models import LLM_MODEL, EMBED_MODEL
class DatabaseNoteManager:
    def __init__(self):
        """Initializes database connection and sets up the note repository."""
        db = PostgresDatabase()
        self.session_maker = db.get_session_maker()
        self.note_repo = NoteRepository(self.session_maker)

    async def _sync_to_rag(self, note_id: int, content: Optional[str], action: str):
        """Internal helper to synchronize database changes with the RAG vector store."""
        content_preview = str(content)[:15] if content else "None"
        print(f"[RAG SYNC] Action: {action.upper()} | ID: {note_id} | Content Preview: {content_preview}...")

    async def add_note(
        self,
        text: str,
        project_name: str,
        author: str,
        embedding: List[float],
        note_type: str = "general",
        tags: Optional[str] = None,
        function: Optional[str] = None,
    ) -> Optional[int]:
        """Creates a new note record and triggers a RAG sync."""
        try:
            new_note = tables_data.NoteCreate(
                project_name=project_name,
                author=author,
                note_text=text,
                embedding=embedding,
                type=note_type,
                tags=tags,
                function=function,
            )
            success = await self.note_repo.create(new_note)
            if success:
                # Retrieve the note to get the auto-generated database ID
                notes = await self.note_repo.get_all_by_author_name(author)
                if notes:
                    note_id = notes[-1].id
                    await self._sync_to_rag(note_id, text, "add")
                    print(f"Note Added (ID: {note_id})")
                    return note_id
            else:
                print("Error: Failed to create note in database.")
                return None
        except Exception as e:
            print(f"Error adding note: {e}")
            return None

    async def edit_note(self, note_id: int, new_text: str, new_embedding: List[float]) -> bool:
        """Updates an existing note's text and embedding, then syncs changes."""
        try:
            note = await self.note_repo.get_by_id(note_id)
            if note is None:
                print(f"Error: Note ID {note_id} not found.")
                return False

            success = await self.note_repo.update(
                note_id,
                {"note_text": new_text, "embedding": new_embedding}
            )
            if success:
                await self._sync_to_rag(note_id, new_text, "edit")
                print(f"Note Edited (ID: {note_id})")
                return True
            else:
                print(f"Error: Failed to update note ID {note_id}.")
                return False
        except Exception as e:
            print(f"Error editing note: {e}")
            return False

    async def delete_note(self, note_id: int) -> bool:
        """Removes a note from the database and triggers a deletion sync in RAG."""
        try:
            note = await self.note_repo.get_by_id(note_id)
            if note is None:
                print(f"Error: Note ID {note_id} not found.")
                return False

            success = await self.note_repo.delete(note_id)
            if success:
                await self._sync_to_rag(note_id, None, "delete")
                print(f"Note Deleted (ID: {note_id})")
                return True
            else:
                print(f"Error: Failed to delete note ID {note_id}.")
                return False
        except Exception as e:
            print(f"Error deleting note: {e}")
            return False

    async def list_notes(self, project_name: str):
        """Fetches and prints all notes associated with a specific project name."""
        try:
            notes = await self.note_repo.get_all_by_project_name(project_name)
            print(f"\n--- Notes for Project: {project_name} ---")
            if not notes:
                print("No notes found.")
            else:
                for n in notes:
                    print(f"ID: {n.id} | Author: {n.author} | Text: {n.note_text[:50]}...")
            print("-----------------------------\n")
            return notes
        except Exception as e:
            print(f"Error listing notes: {e}")
            return None

    async def get_note_by_id(self, note_id: int) -> Optional[tables_data.Note]:
        """Fetches a single note by its unique primary key."""
        try:
            return await self.note_repo.get_by_id(note_id)
        except Exception as e:
            print(f"Error retrieving note: {e}")
            return None

    async def get_notes_by_author(self, author: str) -> Optional[List[tables_data.Note]]:
        """Retrieves a list of all notes created by a specific author."""
        try:
            return await self.note_repo.get_all_by_author_name(author)
        except Exception as e:
            print(f"Error retrieving notes: {e}")
            return None

    async def get_notes_by_type(self, note_type: str) -> Optional[List[tables_data.Note]]:
        """Filters and retrieves notes based on the note_type category."""
        try:
            return await self.note_repo.get_all_by_note_type(note_type)
        except Exception as e:
            print(f"Error retrieving notes: {e}")
            return None

if __name__ == "__main__":
    import asyncio

    async def main():
        """Main entry point for testing manager logic."""
        db = PostgresDatabase()
        session_maker = db.get_session_maker()
        
        # Create project first
        new_project = tables_data.ProjectCreate(
            name="Test Project",
            description="Test Project",
            delivered=False,
        )
        project_repo = ProjectRepository(session_maker)
        project_success = await project_repo.create(new_project)
        if project_success:
            print("Project created successfully.")
        else:
            print("Project already exists or failed to create.")
        
        # Create developer (author) - must exist before creating notes
        new_developer = tables_data.DeveloperCreate(
            name="Test Author",
            role="Tester",
            skills=["testing", "development"],
        )
        developer_repo = DeveloperRepository(session_maker)
        dev_success = await developer_repo.create(new_developer)
        if dev_success:
            print("Developer created successfully.")
        else:
            print("Developer already exists or failed to create.")
        manager = DatabaseNoteManager()
        """
async def add_note(
        self,
        text: str,
        project_name: str,
        author: str,
        embedding: List[float],
        note_type: str = "general",
        tags: Optional[str] = None,
        function: Optional[str] = None,
    ) -> Optional[int]:
        """
        text = "This is a test note."
        embeddings = OllamaEmbeddings(model=EMBED_MODEL)
        embedding = embeddings.embed_query(text)
        print('EMBEDDING 1:',len(embedding))
        note = await manager.add_note(
            text="This is a test note.",
            project_name="Test Project",
            author="Test Author",
            embedding=embedding,
            note_type="test",
            tags="test",
            function="test",
        )
        print(note)
        text = "this is develop note"
        embedding = embeddings.embed_query(text)
        print('EMBEDDING 2:',len(embedding))

        note2 = await manager.add_note(
            text=text,
            project_name="Test Project",
            author="Test Author",
            embedding=embedding,
            note_type="test",
            tags="test",
            function="test",
        )
        print(note2)
        await manager.list_notes("Test Project")
        # await manager.delete_note(note)
        # await manager.list_notes("Test Project")

    asyncio.run(main())