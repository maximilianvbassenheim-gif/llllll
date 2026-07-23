"""
orchestrator.py — Master service for the LLM orchestration system.

Responsibilities:
- REST API on port 8000
- Worker registry (config-based + auto-discovery)
- Request routing to available workers
- Round-robin load balancing
- Health checks (every 30s)
"""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from archive import Archive
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

CONFIG_PATH = Path(
    env_or("CONFIG_PATH", r"C:\Users\maxim\OneDrive\Desktop\Produktion\AI Systeme\config.yaml")
)

config: dict = {}
archive: Optional[Archive] = None
logger = get_logger("orchestrator")


# ---------------------------------------------------------------------------
# Worker registry
# ---------------------------------------------------------------------------

class WorkerInfo(BaseModel):
    id: str
    host: str
    port: int
    ollama_port: int = 11434
    status: str = "unknown"  # "online" | "offline" | "busy" | "unknown"
    last_check: str = ""
    current_load: int = 0    # active requests

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class WorkerRegistry:
    """Thread-safe registry of all known worker nodes."""

    def __init__(self):
        self._workers: dict[str, WorkerInfo] = {}
        self._rr_index: int = 0
        self._lock = asyncio.Lock()

    def register(self, worker: WorkerInfo) -> None:
        self._workers[worker.id] = worker

    def load_from_config(self, worker_configs: list[dict]) -> None:
        for wc in worker_configs:
            self.register(WorkerInfo(**wc))

    async def update_status(self, worker_id: str, status: str) -> None:
        async with self._lock:
            if worker_id in self._workers:
                self._workers[worker_id].status = status
                self._workers[worker_id].last_check = utc_now_str()

    async def get_available_worker(self) -> Optional[WorkerInfo]:
        """Return an online worker using round-robin."""
        async with self._lock:
            online = [w for w in self._workers.values() if w.status == "online"]
            if not online:
                return None
            worker = online[self._rr_index % len(online)]
            self._rr_index = (self._rr_index + 1) % len(online)
            return worker

    def all_workers(self) -> list[WorkerInfo]:
        return list(self._workers.values())

    def get(self, worker_id: str) -> Optional[WorkerInfo]:
        return self._workers.get(worker_id)


registry = WorkerRegistry()


# ---------------------------------------------------------------------------
# Health-check loop
# ---------------------------------------------------------------------------

async def _health_check_loop(interval: int = 30) -> None:
    while True:
        for worker in registry.all_workers():
            status = "offline"
            try:
                r = requests.get(f"{worker.base_url}/health", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    status = "online" if data.get("status") == "ok" else "degraded"
            except Exception:
                status = "offline"
            await registry.update_status(worker.id, status)
            logger.debug("Health check %s → %s", worker.id, status)
        await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global config, archive

    # Load config
    try:
        config = load_config(CONFIG_PATH)
        logger.info("Config loaded from %s", CONFIG_PATH)
    except FileNotFoundError:
        logger.warning("Config not found; using defaults.")
        config = {}

    # Init archive
    archive_cfg = config.get("archive", {})
    db_path = Path(archive_cfg.get("db_path", "Archiv/metadata.db"))
    base_dir = Path(config.get("storage", {}).get("archive_dir", "Archiv"))
    archive = Archive(db_path=db_path, base_dir=base_dir)

    # Load workers
    registry.load_from_config(config.get("workers", []))
    logger.info("Loaded %d workers from config.", len(registry.all_workers()))

    # Start health-check background task
    interval = config.get("master", {}).get("health_check_interval", 30)
    task = asyncio.create_task(_health_check_loop(interval))

    logger.info("Orchestrator master started on port %d", config.get("master", {}).get("port", 8000))
    yield

    task.cancel()
    logger.info("Orchestrator stopped.")


app = FastAPI(
    title="LLM Orchestrator — Master",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RouteRequest(BaseModel):
    session_id: str = Field(default_factory=new_session_id)
    model: str = "mistral:7b"
    prompt: str
    system_prompt: Optional[str] = None
    options: dict = Field(default_factory=dict)
    preferred_worker: Optional[str] = None
    capture_webcam: bool = False
    capture_audio: bool = False
    audio_duration: int = 10


class RouteResponse(BaseModel):
    session_id: str
    worker_id: str
    model: str
    response: str
    timestamp: str
    duration_ms: float
    archived: bool = False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def master_health():
    workers = registry.all_workers()
    online = [w for w in workers if w.status == "online"]
    return {
        "status": "ok",
        "timestamp": utc_now_str(),
        "workers_total": len(workers),
        "workers_online": len(online),
    }


@app.get("/workers")
async def list_workers():
    """List all registered workers and their status."""
    return [w.model_dump() for w in registry.all_workers()]


@app.get("/workers/{worker_id}")
async def get_worker(worker_id: str):
    worker = registry.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker.model_dump()


@app.post("/generate", response_model=RouteResponse)
async def route_generate(req: RouteRequest):
    """
    Route an LLM generation request to an available worker.
    Supports preferred_worker for pinning a session to a specific node.
    """
    import time

    # Determine target worker
    if req.preferred_worker:
        worker = registry.get(req.preferred_worker)
        if not worker or worker.status != "online":
            raise HTTPException(
                status_code=503,
                detail=f"Preferred worker '{req.preferred_worker}' is not available.",
            )
    else:
        worker = await registry.get_available_worker()
        if not worker:
            raise HTTPException(status_code=503, detail="No workers available.")

    # Forward request to worker
    payload = req.model_dump()
    start = time.monotonic()
    try:
        r = requests.post(f"{worker.base_url}/generate", json=payload, timeout=300)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        await registry.update_status(worker.id, "offline")
        raise HTTPException(status_code=503, detail=f"Worker error: {exc}")

    elapsed_ms = (time.monotonic() - start) * 1000

    return RouteResponse(
        session_id=data.get("session_id", req.session_id),
        worker_id=data.get("worker_id", worker.id),
        model=data.get("model", req.model),
        response=data.get("response", ""),
        timestamp=utc_now_str(),
        duration_ms=elapsed_ms,
        archived=data.get("archived", False),
    )


@app.get("/models")
async def aggregate_models():
    """
    Aggregate available models from all online workers.
    Returns a deduplicated list.
    """
    seen: set[str] = set()
    models: list[dict] = []

    for worker in registry.all_workers():
        if worker.status != "online":
            continue
        try:
            r = requests.get(f"{worker.base_url}/models", timeout=5)
            if r.status_code == 200:
                for m in r.json().get("models", []):
                    key = m.get("name", "")
                    if key not in seen:
                        seen.add(key)
                        models.append(m)
        except Exception:
            pass

    return {"models": models}


@app.get("/status")
async def master_status():
    """Detailed master status."""
    return {
        "master": "online",
        "timestamp": utc_now_str(),
        "config_path": str(CONFIG_PATH),
        "workers": [w.model_dump() for w in registry.all_workers()],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    master_cfg = config.get("master", {}) if config else {}
    host = master_cfg.get("host", "0.0.0.0")
    port = int(master_cfg.get("port", 8000))
    uvicorn.run(
        "orchestrator:app",
        host=host,
        port=port,
        log_level="info",
        reload=False,
    )
