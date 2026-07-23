"""
start_all.py — Starts the entire LLM orchestration system.

Launches all 7 workers (via SSH/PowerShell) and the master service.
Performs health checks every 30 seconds.

Usage:
    python start_all.py [--config path/to/config_workers.json] [--master-only] [--no-health-check]
"""

import argparse
import getpass
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = Path(__file__).parent / "config_workers.json"
_home = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
DEFAULT_PRODUKTION = os.environ.get(
    "PRODUKTION_PATH",
    str(_home / "OneDrive" / "Desktop" / "Produktion"),
)

# ---------------------------------------------------------------------------
# Logging (simple print-based, no external dep at startup)
# ---------------------------------------------------------------------------

def log(msg: str, level: str = "INFO") -> None:
    from datetime import datetime, timezone
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{ts} | {level:7s} | start_all | {msg}", flush=True)


def _resolve_ssh_username() -> str:
    return (
        os.environ.get("WORKER_SSH_USERNAME")
        or os.environ.get("USERNAME")
        or os.environ.get("USER")
        or getpass.getuser()
    )


# ---------------------------------------------------------------------------
# Master startup
# ---------------------------------------------------------------------------

def start_master(produktion_root: str = DEFAULT_PRODUKTION) -> Optional[subprocess.Popen]:
    """Start the master/orchestrator service locally."""
    script = Path(produktion_root) / "Start" / "start_master.ps1"
    if not script.exists():
        log(f"start_master.ps1 not found: {script}", "ERROR")
        return None

    log("Starting master service...")
    proc = subprocess.Popen(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)],
    )
    log(f"Master started (PID {proc.pid})")
    return proc


# ---------------------------------------------------------------------------
# Worker startup (SSH + PowerShell remoting)
# ---------------------------------------------------------------------------

def start_worker_ssh(worker: dict, produktion_root: str = DEFAULT_PRODUKTION) -> bool:
    """
    Connect to a remote worker via SSH and start the worker PowerShell script.
    Returns True on success.
    """
    host     = worker["host"]
    username = worker.get("username")
    if username is None:
        username = _resolve_ssh_username()
    wid      = worker["id"]
    port     = worker["port"]
    ssh_key  = worker.get("ssh_key")

    script_remote = f"{produktion_root}\\Start\\start_worker.ps1"
    ps_cmd = (
        f"powershell -ExecutionPolicy Bypass -File \"{script_remote}\" "
        f"-WorkerId {wid} -Port {port}"
    )

    ssh_args = ["ssh"]
    if ssh_key:
        ssh_args += ["-i", ssh_key]
    ssh_args += ["-o", "ConnectTimeout=10"]
    if os.environ.get("SSH_DISABLE_STRICT_HOST_KEY_CHECKING") == "1":
        ssh_args += ["-o", "StrictHostKeyChecking=no"]
    ssh_args += [f"{username}@{host}", ps_cmd]

    log(f"Starting {wid} on {host}:{port}...")
    try:
        result = subprocess.run(ssh_args, timeout=60, capture_output=True, text=True)
        if result.returncode == 0:
            log(f"{wid} started successfully.")
            return True
        else:
            log(f"{wid} SSH error: {result.stderr.strip()}", "WARN")
            return False
    except subprocess.TimeoutExpired:
        log(f"{wid} SSH timeout", "WARN")
        return False
    except FileNotFoundError:
        log("ssh not found — trying WinRM/PowerShell remoting...", "WARN")
        return _start_worker_winrm(worker, produktion_root)


def _start_worker_winrm(worker: dict, produktion_root: str) -> bool:
    """Fallback: use PowerShell Invoke-Command (WinRM) to start the worker."""
    host     = worker["host"]
    wid      = worker["id"]
    port     = worker["port"]

    script_remote = f"{produktion_root}\\Start\\start_worker.ps1"
    ps_cmd = (
        f"Invoke-Command -ComputerName {host} "
        f"-ScriptBlock {{ powershell -File '{script_remote}' -WorkerId {wid} -Port {port} }}"
    )

    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            timeout=60,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            log(f"{wid} started via WinRM.")
            return True
        log(f"{wid} WinRM failed: {result.stderr.strip()}", "WARN")
        return False
    except Exception as exc:
        log(f"{wid} WinRM error: {exc}", "WARN")
        return False


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

def check_master(master_port: int = 8000) -> bool:
    try:
        r = requests.get(f"http://localhost:{master_port}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def check_all_workers(workers: list[dict]) -> dict[str, bool]:
    results = {}
    for w in workers:
        host = w["host"]
        port = w["port"]
        wid  = w["id"]
        try:
            r = requests.get(f"http://{host}:{port}/health", timeout=5)
            results[wid] = r.status_code == 200
        except Exception:
            results[wid] = False
    return results


def health_loop(workers: list[dict], interval: int = 30) -> None:
    """Continuously check health and log status."""
    log(f"Health-check loop started (interval={interval}s). Press Ctrl+C to stop.")
    while True:
        master_ok = check_master()
        worker_status = check_all_workers(workers)
        online = sum(1 for v in worker_status.values() if v)
        total  = len(worker_status)
        log(f"Master: {'OK' if master_ok else 'OFFLINE'} | Workers online: {online}/{total}")
        for wid, ok in worker_status.items():
            if not ok:
                log(f"  ⚠  {wid} is OFFLINE", "WARN")
        time.sleep(interval)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Start all LLM orchestration services.")
    parser.add_argument("--config",        default=str(DEFAULT_CONFIG), help="Path to config_workers.json")
    parser.add_argument("--produktion",    default=DEFAULT_PRODUKTION, help="Path to Produktion root folder")
    parser.add_argument("--master-only",   action="store_true", help="Start only the master (no workers)")
    parser.add_argument("--workers-only",  action="store_true", help="Start only workers (master assumed running)")
    parser.add_argument("--no-health-check", action="store_true", help="Skip continuous health-check loop")
    parser.add_argument("--health-interval", type=int, default=30, help="Health-check interval in seconds")
    args = parser.parse_args()

    # Load worker config
    config_path = Path(args.config)
    if not config_path.exists():
        log(f"Worker config not found: {config_path}", "ERROR")
        sys.exit(1)

    with config_path.open("r") as fh:
        worker_config = json.load(fh)
    workers = worker_config.get("workers", [])
    log(f"Loaded {len(workers)} workers from {config_path}")

    # Start master
    master_proc = None
    if not args.workers_only:
        master_proc = start_master(args.produktion)
        log("Waiting 10s for master to initialize...")
        time.sleep(10)
        if check_master():
            log("Master is online ✓")
        else:
            log("Master did not respond — check logs.", "WARN")

    # Start workers
    if not args.master_only:
        started = 0
        for w in workers:
            ok = start_worker_ssh(w, args.produktion)
            if ok:
                started += 1
            time.sleep(2)  # small stagger
        log(f"Started {started}/{len(workers)} workers.")

        # Wait and verify
        log("Waiting 15s for workers to initialize...")
        time.sleep(15)
        statuses = check_all_workers(workers)
        online = sum(1 for v in statuses.values() if v)
        log(f"Workers online: {online}/{len(workers)}")
        for wid, ok in statuses.items():
            log(f"  {wid}: {'online ✓' if ok else 'OFFLINE ✗'}")

    # Continuous health checks
    if not args.no_health_check:
        try:
            health_loop(workers, interval=args.health_interval)
        except KeyboardInterrupt:
            log("Health-check loop stopped by user.")

    log("start_all.py done.")


if __name__ == "__main__":
    main()
