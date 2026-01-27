import json
import os
import uuid
import datetime

# Configuration
NOTES_FILE = "my_notes.txt"

class FileNoteManager:
    def __init__(self):
        # Create the file if it doesn't exist
        if not os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'w') as f:
                json.dump([], f)  # Initialize with an empty list

    # --- HELPER FUNCTIONS FOR FILE HANDLING ---
    def _read_file(self):
        """Reads the list of notes from the text file."""
        try:
            with open(NOTES_FILE, 'r') as f:
                content = f.read()
                # Handle empty file case
                if not content: 
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            return []

    def _write_file(self, notes):
        """Writes the updated list of notes back to the text file."""
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=4)

    def _sync_to_rag(self, note_id, content, action):
        """
        Placeholder: logic to send data to your Vector DB (RAG).
        """
        print(f"   [RAG SYNC] Action: {action.upper()} | ID: {note_id} | Content Preview: {str(content)[:15]}...")

    # --- MAIN FUNCTIONS ---

    def add_note(self, text):
        notes = self._read_file()
        
        note_id = str(uuid.uuid4())[:8] # Short unique ID
        new_note = {
            "id": note_id,
            "text": text,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        notes.append(new_note)
        self._write_file(notes)
        
        # Trigger RAG update
        self._sync_to_rag(note_id, text, "add")
        print(f"✅ Note Added (ID: {note_id})")
        return note_id

    def edit_note(self, note_id, new_text):
        notes = self._read_file()
        found = False
        
        for note in notes:
            if note["id"] == note_id:
                note["text"] = new_text
                note["timestamp"] = datetime.datetime.now().isoformat() # Update time
                found = True
                break
        
        if found:
            self._write_file(notes)
            # Trigger RAG update (re-embedding)
            self._sync_to_rag(note_id, new_text, "edit")
            print(f"✏️  Note Edited (ID: {note_id})")
        else:
            print(f"❌ Error: Note ID {note_id} not found.")

    def delete_note(self, note_id):
        notes = self._read_file()
        
        # Filter out the note with the specific ID
        original_count = len(notes)
        notes = [n for n in notes if n["id"] != note_id]
        
        if len(notes) < original_count:
            self._write_file(notes)
            # Trigger RAG update (delete vector)
            self._sync_to_rag(note_id, None, "delete")
            print(f"🗑️  Note Deleted (ID: {note_id})")
        else:
            print(f"❌ Error: Note ID {note_id} not found.")

    def list_notes(self):
        """Helper to see what is currently in the file"""
        notes = self._read_file()
        print("\n--- Current Notes in File ---")
        for n in notes:
            print(f"ID: {n['id']} | Text: {n['text']}")
        print("-----------------------------\n")

# --- TEST AREA ---
if __name__ == "__main__":
    manager = FileNoteManager()

    # 1. Add
    id_1 = manager.add_note("Python is great for RAG pipelines.")
    id_2 = manager.add_note("This note will be deleted.")
    id_3 = manager.add_note("ddddddddddd")

    manager.list_notes()

    # 2. Edit
    manager.edit_note(id_1, "Python is EXCELLENT for RAG pipelines.")

    # 3. Delete
    manager.delete_note(id_2)

    manager.list_notes()