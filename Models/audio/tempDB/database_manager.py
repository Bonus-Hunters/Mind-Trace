import sqlite3
import numpy as np
import io
from typing import List, Tuple, Optional
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SPEAKER_DB_PATH = os.getenv(
    "SPEAKER_DB_PATH", Path(__file__).resolve().parents[1] / "data" / "speaker_embeddings.db"
)

# Ensure the data directory exists
os.makedirs(Path(SPEAKER_DB_PATH).parent, exist_ok=True)
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

class DatabaseManager:
    def __init__(self):
        self.db_path = str(SPEAKER_DB_PATH)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS speakers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    company TEXT,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def _serialize(self, emb: np.ndarray) -> bytes:
        buffer = io.BytesIO()
        np.save(buffer, emb.astype(np.float32))
        return buffer.getvalue()

    def _deserialize(self, blob: bytes) -> np.ndarray:
        return np.load(io.BytesIO(blob))

    def add_speaker(self, name: str, company: str, embedding: np.ndarray):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO speakers (name, company, embedding) VALUES (?, ?, ?)",
                    (name, company, self._serialize(embedding)),
                )
                return True
        except sqlite3.IntegrityError:
            return False

    def get_all_speakers(self) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, name, company FROM speakers")
            return [{"id": r[0], "name": r[1], "company": r[2]} for r in cursor.fetchall()]

    def delete_speaker(self, speaker_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM speakers WHERE id = ?", (speaker_id,))

    def get_embeddings_map(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name, embedding FROM speakers")
            return {name: self._deserialize(blob) for name, blob in cursor.fetchall()}