"""
archive.py — Forensic-grade append-only archive for the LLM system.

Features:
- SQLite metadata database (append-only, no deletes)
- Filesystem: YYYY/MM/DD/session_id/ structure
- SHA-256 checksums for every stored file
- Interaction + log records
"""

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from utils import archive_path, sha256_bytes, sha256_file, sha256_str, utc_now_str, get_logger


logger = get_logger("archive")

# ---------------------------------------------------------------------------
# Database schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    created_at   TEXT NOT NULL,
    worker_id    TEXT,
    model        TEXT,
    metadata     TEXT  -- JSON blob
);

CREATE TABLE IF NOT EXISTS interactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    timestamp    TEXT NOT NULL,
    role         TEXT NOT NULL,  -- 'user' | 'assistant'
    content      TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    model        TEXT,
    worker_id    TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS files (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    timestamp    TEXT NOT NULL,
    file_type    TEXT NOT NULL,  -- 'image' | 'audio' | 'log' | 'other'
    filename     TEXT NOT NULL,
    abs_path     TEXT NOT NULL,
    sha256       TEXT NOT NULL,
    size_bytes   INTEGER NOT NULL,
    metadata     TEXT,           -- JSON blob
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    session_id   TEXT,
    worker_id    TEXT,
    detail       TEXT            -- JSON blob
);
"""


# ---------------------------------------------------------------------------
# Archive class
# ---------------------------------------------------------------------------

class Archive:
    """
    Manages the forensic append-only archive.

    Usage::

        archive = Archive(db_path="path/to/metadata.db", base_dir="path/to/Archiv")
        archive.start_session(session_id, worker_id="worker_1", model="mistral:7b")
        archive.log_interaction(session_id, role="user", content="Hello")
        archive.log_interaction(session_id, role="assistant", content="Hi!")
        archive.store_file(session_id, src_path="/tmp/frame.jpg", file_type="image")
    """

    def __init__(self, db_path: str | Path, base_dir: str | Path):
        self.db_path = Path(db_path)
        self.base_dir = Path(base_dir)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _audit(
        self,
        conn: sqlite3.Connection,
        event_type: str,
        session_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        detail: Optional[dict] = None,
    ) -> None:
        conn.execute(
            "INSERT INTO audit_log (timestamp, event_type, session_id, worker_id, detail) "
            "VALUES (?, ?, ?, ?, ?)",
            (utc_now_str(), event_type, session_id, worker_id, json.dumps(detail) if detail else None),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(
        self,
        session_id: str,
        worker_id: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Register a new session in the database."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sessions (session_id, created_at, worker_id, model, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    utc_now_str(),
                    worker_id,
                    model,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            self._audit(conn, "session_start", session_id=session_id, worker_id=worker_id)
        logger.info("Session started: %s (worker=%s, model=%s)", session_id, worker_id, model)

    def log_interaction(
        self,
        session_id: str,
        role: str,
        content: str,
        model: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> int:
        """
        Append a user/assistant interaction.
        Returns the new row id.
        """
        content_hash = sha256_str(content)
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO interactions "
                "(session_id, timestamp, role, content, content_hash, model, worker_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, utc_now_str(), role, content, content_hash, model, worker_id),
            )
            self._audit(
                conn,
                "interaction",
                session_id=session_id,
                worker_id=worker_id,
                detail={"role": role, "hash": content_hash},
            )
        return cur.lastrowid

    def store_file(
        self,
        session_id: str,
        src_path: str | Path,
        file_type: str = "other",
        metadata: Optional[dict] = None,
    ) -> Path:
        """
        Copy a file into the archive structure and register it.
        Returns the destination path.
        """
        src_path = Path(src_path)
        dest_dir = archive_path(self.base_dir, session_id)
        dest_path = dest_dir / src_path.name

        shutil.copy2(src_path, dest_path)
        checksum = sha256_file(dest_path)
        size = dest_path.stat().st_size

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO files "
                "(session_id, timestamp, file_type, filename, abs_path, sha256, size_bytes, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    utc_now_str(),
                    file_type,
                    src_path.name,
                    str(dest_path),
                    checksum,
                    size,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            self._audit(
                conn,
                "file_stored",
                session_id=session_id,
                detail={"file": src_path.name, "sha256": checksum, "type": file_type},
            )

        logger.info("Stored %s (%s bytes, sha256=%s…)", dest_path.name, size, checksum[:16])
        return dest_path

    def store_bytes(
        self,
        session_id: str,
        data: bytes,
        filename: str,
        file_type: str = "other",
        metadata: Optional[dict] = None,
    ) -> Path:
        """
        Write raw bytes directly into the archive structure.
        Returns the destination path.
        """
        dest_dir = archive_path(self.base_dir, session_id)
        dest_path = dest_dir / filename
        dest_path.write_bytes(data)
        checksum = sha256_bytes(data)
        size = len(data)

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO files "
                "(session_id, timestamp, file_type, filename, abs_path, sha256, size_bytes, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    utc_now_str(),
                    file_type,
                    filename,
                    str(dest_path),
                    checksum,
                    size,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            self._audit(
                conn,
                "bytes_stored",
                session_id=session_id,
                detail={"file": filename, "sha256": checksum, "type": file_type},
            )

        logger.info("Stored bytes → %s (%s bytes)", filename, size)
        return dest_path

    def get_session_interactions(self, session_id: str) -> list[dict]:
        """Return all interactions for a session, ordered by id."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM interactions WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session_files(self, session_id: str) -> list[dict]:
        """Return all archived files for a session."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM files WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]
