"""
worker.py — Worker service for the LLM orchestration system.

Each of the 7 worker machines runs this service.
It exposes a REST API on port 8001–8007, connects to a local Ollama instance,
processes LLM requests and optionally captures local multimedia.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from archive import Archive
from multimedia import MultimediaManager
from utils import (
    env_or,
    get_logger,
    load_config,
    new_session_id,
    utc_now_str,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_default_config = (
    Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
    / "OneDrive" / "Desktop" / "Produktion" / "AI Systeme" / "config.yaml"
)
CONFIG_PATH = Path(env_or("CONFIG_PATH", str(_default_config)))
WORKER_ID   = env_or("WORKER_ID", "worker_1")
WORKER_PORT = int(env_or("WORKER_PORT", "8001"))

config: dict = {}
archive: Optional[Archive] = None
media_manager: Optional[MultimediaManager] = None

logger = get_logger("worker")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global config, archive, media_manager

    # Load config
    try:
        config = load_config(CONFIG_PATH)
        logger.info("Config loaded from %s", CONFIG_PATH)
    except FileNotFoundError:
        logger.warning("Config not found at %s; using defaults.", CONFIG_PATH)
        config = {}

    # Init archive
    archive_cfg = config.get("archive", {})
    db_path = Path(archive_cfg.get("db_path", "Archiv/metadata.db"))
    base_dir = Path(config.get("storage", {}).get("archive_dir", "Archiv"))
    archive = Archive(db_path=db_path, base_dir=base_dir)

    # Init multimedia
    media_manager = MultimediaManager(config)

    logger.info("Worker %s started on port %d", WORKER_ID, WORKER_PORT)
    yield

    # Cleanup
    if media_manager:
        media_manager.release_all()
    logger.info("Worker %s stopped.", WORKER_ID)


app = FastAPI(
    title=f"LLM Worker — {WORKER_ID}",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class LLMRequest(BaseModel):
    session_id: str = Field(default_factory=new_session_id)
    model: str = "mistral:7b"
    prompt: str
    system_prompt: Optional[str] = None
    stream: bool = False
    options: dict = Field(default_factory=dict)
    capture_webcam: bool = False
    capture_audio: bool = False
    audio_duration: int = 10


class LLMResponse(BaseModel):
    session_id: str
    worker_id: str
    model: str
    response: str
    timestamp: str
    duration_ms: float
    archived: bool = False


class HealthResponse(BaseModel):
    worker_id: str
    status: str
    ollama_ok: bool
    timestamp: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ollama_url() -> str:
    """Return the base Ollama API URL for this worker."""
    port = None
    for w in config.get("workers", []):
        if w.get("id") == WORKER_ID:
            port = w.get("ollama_port", 11434)
            break
    return f"http://localhost:{port or 11434}"


def _check_ollama() -> bool:
    try:
        r = requests.get(f"{_ollama_url()}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        worker_id=WORKER_ID,
        status="ok",
        ollama_ok=_check_ollama(),
        timestamp=utc_now_str(),
    )


@app.get("/models")
async def list_models():
    """List available Ollama models on this worker."""
    try:
        r = requests.get(f"{_ollama_url()}/api/tags", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {exc}")


@app.post("/generate", response_model=LLMResponse)
async def generate(req: LLMRequest):
    """Process an LLM generation request via Ollama."""
    import time

    # Optional multimedia capture
    if req.capture_webcam and media_manager:
        frames = media_manager.capture_all_cameras()
        for frame_path in frames:
            if frame_path and archive:
                archive.store_file(req.session_id, frame_path, file_type="image",
                                   metadata={"worker_id": WORKER_ID})

    if req.capture_audio and media_manager:
        audio_path = media_manager.record_audio(duration=req.audio_duration)
        if audio_path and archive:
            archive.store_file(req.session_id, audio_path, file_type="audio",
                               metadata={"worker_id": WORKER_ID, "duration": req.audio_duration})

    # Log user interaction
    if archive:
        archive.start_session(req.session_id, worker_id=WORKER_ID, model=req.model)
        archive.log_interaction(req.session_id, role="user", content=req.prompt,
                                model=req.model, worker_id=WORKER_ID)

    # Build Ollama request payload
    payload: dict = {
        "model": req.model,
        "prompt": req.prompt,
        "stream": False,
        "options": req.options,
    }
    if req.system_prompt:
        payload["system"] = req.system_prompt

    start = time.monotonic()
    try:
        r = requests.post(
            f"{_ollama_url()}/api/generate",
            json=payload,
            timeout=300,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama error: {exc}")

    elapsed_ms = (time.monotonic() - start) * 1000
    response_text: str = data.get("response", "")

    # Archive assistant response
    if archive:
        archive.log_interaction(req.session_id, role="assistant", content=response_text,
                                model=req.model, worker_id=WORKER_ID)

    return LLMResponse(
        session_id=req.session_id,
        worker_id=WORKER_ID,
        model=req.model,
        response=response_text,
        timestamp=utc_now_str(),
        duration_ms=elapsed_ms,
        archived=archive is not None,
    )


@app.get("/status")
async def status():
    """Return worker runtime status."""
    return {
        "worker_id": WORKER_ID,
        "port": WORKER_PORT,
        "ollama_url": _ollama_url(),
        "ollama_ok": _check_ollama(),
        "timestamp": utc_now_str(),
        "config_path": str(CONFIG_PATH),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "worker:app",
        host="0.0.0.0",
        port=WORKER_PORT,
        log_level="info",
        reload=False,
    )
