"""
utils.py — Shared utilities for the LLM orchestration system.

Provides: config loading, logging, checksums, timestamps, session IDs.
"""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Return a pre-configured logger with timestamp + user context."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    return logger


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(config_path: str | Path) -> dict:
    """Load YAML config file and return as dict."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_models(models_path: str | Path) -> list[dict]:
    """Load models.json and return list of model definitions."""
    models_path = Path(models_path)
    if not models_path.exists():
        raise FileNotFoundError(f"models.json not found: {models_path}")
    with models_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("models", [])


# ---------------------------------------------------------------------------
# Session / Timestamps
# ---------------------------------------------------------------------------

def new_session_id() -> str:
    """Generate a new unique session ID (UUID4)."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(tz=timezone.utc)


def utc_now_str() -> str:
    """Return current UTC datetime as ISO-8601 string."""
    return utc_now().isoformat()


def archive_path(base_dir: str | Path, session_id: str) -> Path:
    """
    Return a structured archive path: base_dir/YYYY/MM/DD/session_id/
    Creates the directory if it does not exist.
    """
    now = utc_now()
    path = (
        Path(base_dir)
        / now.strftime("%Y")
        / now.strftime("%m")
        / now.strftime("%d")
        / session_id
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Checksums
# ---------------------------------------------------------------------------

def sha256_file(file_path: str | Path) -> str:
    """Return SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_str(text: str) -> str:
    """Return SHA-256 hex digest of a UTF-8 string."""
    return sha256_bytes(text.encode("utf-8"))


# ---------------------------------------------------------------------------
# Env helpers
# ---------------------------------------------------------------------------

def require_env(name: str) -> str:
    """Return env var value or raise if not set."""
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set."
        )
    return value


def env_or(name: str, default: Any) -> Any:
    """Return env var value or a default."""
    return os.environ.get(name, default)


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

def safe_json(obj: Any) -> str:
    """Serialize to JSON with sensible defaults (datetime → ISO string)."""
    def _default(o: Any) -> str:
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")
    return json.dumps(obj, default=_default, ensure_ascii=False)
