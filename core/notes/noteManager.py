from datetime import datetime
from typing import Optional, List
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import NoteRepository
from core.database import tables_data


class DatabaseNoteManager:
    def __init__(self):
        """Initialize the note manager with database connection."""
        db = PostgresDatabase()
        self.session_maker = db.get_session_maker()
        self.note_repo = NoteRepository(self.session_maker)

    # --- HELPER FUNCTIONS FOR RAG SYNC ---
    async def _sync_to_rag(self, note_id: int, content: Optional[str], action: str):
        """
        Placeholder: logic to send data to your Vector DB (RAG).
        """
        content_preview = str(content)[:15] if content else "None"
        print(f"   [RAG SYNC] Action: {action.upper()} | ID: {note_id} | Content Preview: {content_preview}...")

    # --- MAIN FUNCTIONS ---

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
        """Add a new note to the database."""
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
                # Get the created note to retrieve its ID
                notes = await self.note_repo.get_all_by_author_name(author)
                if notes:
                    note_id = notes[-1].id  # Get the last added note's ID
                    await self._sync_to_rag(note_id, text, "add")
                    print(f"✅ Note Added (ID: {note_id})")
                    return note_id
            else:
                print("❌ Error: Failed to create note in database.")
                return None
        except Exception as e:
            print(f"❌ Error adding note: {e}")
            return None

    async def edit_note(self, note_id: int, new_text: str, new_embedding: List[float]) -> bool:
        """Edit an existing note in the database."""
        try:
            note = await self.note_repo.get_by_id(note_id)
            if note is None:
                print(f"❌ Error: Note ID {note_id} not found.")
                return False

            # Update note using the repository's update method
            # Note: You may need to implement an update method in NoteRepository if it doesn't exist
            success = await self.note_repo.update(
                note_id,
                {"note_text": new_text, "embedding": new_embedding}
            )
            if success:
                await self._sync_to_rag(note_id, new_text, "edit")
                print(f"✏️  Note Edited (ID: {note_id})")
                return True
            else:
                print(f"❌ Error: Failed to update note ID {note_id}.")
                return False
        except Exception as e:
            print(f"❌ Error editing note: {e}")
            return False

    async def delete_note(self, note_id: int) -> bool:
        """Delete a note from the database."""
        try:
            note = await self.note_repo.get_by_id(note_id)
            if note is None:
                print(f"❌ Error: Note ID {note_id} not found.")
                return False

            success = await self.note_repo.delete(note_id)
            if success:
                await self._sync_to_rag(note_id, None, "delete")
                print(f"🗑️  Note Deleted (ID: {note_id})")
                return True
            else:
                print(f"❌ Error: Failed to delete note ID {note_id}.")
                return False
        except Exception as e:
            print(f"❌ Error deleting note: {e}")
            return False

    async def list_notes(self, project_name: str):
        """Retrieve and display all notes for a project."""
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
            print(f"❌ Error listing notes: {e}")
            return None

    async def get_note_by_id(self, note_id: int) -> Optional[tables_data.Note]:
        """Retrieve a single note by ID."""
        try:
            return await self.note_repo.get_by_id(note_id)
        except Exception as e:
            print(f"❌ Error retrieving note: {e}")
            return None

    async def get_notes_by_author(self, author: str) -> Optional[List[tables_data.Note]]:
        """Retrieve all notes by a specific author."""
        try:
            return await self.note_repo.get_all_by_author_name(author)
        except Exception as e:
            print(f"❌ Error retrieving notes: {e}")
            return None

    async def get_notes_by_type(self, note_type: str) -> Optional[List[tables_data.Note]]:
        """Retrieve all notes of a specific type."""
        try:
            return await self.note_repo.get_all_by_note_type(note_type)
        except Exception as e:
            print(f"❌ Error retrieving notes: {e}")
            return None

# --- TEST AREA ---
if __name__ == "__main__":
    import asyncio

    async def main():
        manager = DatabaseNoteManager()

        # Example usage (make sure project and author exist in database)
        # id_1 = await manager.add_note(
        #     text="Python is great for RAG pipelines.",
        #     project_name="MyProject",
        #     author="John Doe",
        #     embedding=[0.0] * 1536,  # Replace with actual embedding
        #     note_type="general"
        # )

        # id_2 = await manager.add_note(
        #     text="This note will be deleted.",
        #     project_name="MyProject",
        #     author="John Doe",
        #     embedding=[0.0] * 1536,
        #     note_type="general"
        # )

        # await manager.list_notes("MyProject")

        # if id_2:
        #     await manager.delete_note(id_2)

        # await manager.list_notes("MyProject")

    asyncio.run(main())