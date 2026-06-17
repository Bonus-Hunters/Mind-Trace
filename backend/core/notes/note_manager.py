from typing import List, Optional

from core.database import tables_data
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import NoteRepository
from core.database.tables_data import Note, NoteCreate
from core.rag.models import EMBED_MODEL
from langchain_ollama import OllamaEmbeddings


class DatabaseNoteManager:
    def __init__(self):
        """Initializes database connection and sets up the note repository."""
        db = PostgresDatabase()
        self.session_maker = db.get_session_maker()
        self.note_repo = NoteRepository(self.session_maker)

    async def _sync_to_rag(self, note_id: int, content: Optional[str], action: str):
        """Internal helper to synchronize database changes with the RAG vector store."""
        content_preview = str(content)[:15] if content else "None"
        print(
            f"[RAG SYNC] Action: {action.upper()} | ID: {note_id} | Content Preview: {content_preview}..."
        )

    async def add_note(
        self, note_data: NoteCreate, author: str, company_id: int
    ) -> Optional[int]:
        """Creates a new note record and triggers a RAG sync."""
        try:
            embeddings = OllamaEmbeddings(model=EMBED_MODEL)
            # Build enriched text for embedding only (store raw separately)
            text = note_data.note_text
            embedding = embeddings.embed_query(text)

            new_note = note_data.model_dump()
            new_note["embedding"] = embedding
            new_note["author"] = author
            new_note["company_id"] = company_id

            note_id = await self.note_repo.create(Note(**new_note))

            if note_id:
                await self._sync_to_rag(note_id, text, "add")
                print(f"Note Added (ID: {note_id})")
                return note_id
            else:
                print("Error: Failed to create note in database.")
                return None
        except Exception as e:
            print(f"Error adding note: {e}")
            return None

    async def edit_note(self, note_id: int, new_text: str) -> bool:
        """Updates an existing note's text and embedding, then syncs changes."""
        try:
            note = await self.note_repo.get_by_id(note_id)
            if note is None:
                print(f"Error: Note ID {note_id} not found.")
                return False
            embeddings = OllamaEmbeddings(model=EMBED_MODEL)
            new_embedding = embeddings.embed_query(new_text)
            # TODO: check other update func using NoteUpdate pydantic model
            success = await self.note_repo.update(
                note_id, {"note_text": new_text, "embedding": new_embedding}
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
        # TODO: can be refined a bit, note repo already has a delete func handles checking for note
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
                    print(
                        f"ID: {n.id} | Author: {n.author} | Text: {n.note_text[:50]}..."
                    )
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

    async def get_notes_by_author(
        self, author: str
    ) -> Optional[List[tables_data.Note]]:
        """Retrieves a list of all notes created by a specific author."""
        try:
            return await self.note_repo.get_all_by_author_name(author)
        except Exception as e:
            print(f"Error retrieving notes: {e}")
            return None

    async def get_notes_by_type(
        self, note_type: str
    ) -> Optional[List[tables_data.Note]]:
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

        manager = DatabaseNoteManager()
        embeddings = OllamaEmbeddings(model=EMBED_MODEL)
        """
        async def edit_note(self, note_id: int,
          new_text: str,
            new_embedding: List[float]) -> bool:

        """
        text = "This is a test note but we modified it a bit again fr fr."
        note = await manager.edit_note(1, text)
        print(note)
        await manager.list_notes("Test Project")

        # note2 = await manager.delete_note(2)
        # print(note2)
        # await manager.list_notes("Test Project")

    asyncio.run(main())
