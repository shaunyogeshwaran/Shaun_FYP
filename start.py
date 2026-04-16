#!/usr/bin/env python3
"""Start all AFLHR Lite services on available ports."""

import os
import signal
import socket
import subprocess
import sys
import time

VENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
PYTHON = os.path.join(VENV, "bin", "python")
NPM = os.path.join(VENV, "bin", "npm")
NPX = os.path.join(VENV, "bin", "npx")
PID_FILE = "/tmp/aflhr_pids.txt"

# Preferred ports (will auto-increment if busy)
PREFERRED = {"backend": 8000, "frontend": 5173, "docs": 4000}


def find_free_port(start):
    """Find the next free port starting from `start`."""
    port = start
    while port < start + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    print(f"Error: no free port found in range {start}-{start+99}")
    sys.exit(1)


def wait_for_port(port, timeout=60):
    """Wait until a port is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(2)
    return False


def stop():
    """Kill any previously started services."""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            for line in f:
                pid = line.strip()
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except (ProcessLookupError, ValueError):
                        pass
        os.remove(PID_FILE)

    # Also kill by name as fallback
    for pattern in ["uvicorn api:app"]:
        subprocess.run(["pkill", "-f", pattern],
                       capture_output=True)
    time.sleep(1)


def main():
    if not os.path.exists(PYTHON):
        print("Error: venv not found. Run 'make install' first.")
        sys.exit(1)

    env = os.environ.copy()
    env["PATH"] = os.path.join(VENV, "bin") + ":" + env.get("PATH", "")
    env["npm_config_cache"] = os.path.join(VENV, ".npm-cache")

    # Stop previous instances
    stop()

    pids = []

    # --- Backend ---
    bp = find_free_port(PREFERRED["backend"])
    print(f"Starting backend on port {bp}...")
    backend = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "api:app", "--port", str(bp),
         "--log-level", "warning"],
        stdout=open("/tmp/aflhr_backend.log", "w"),
        stderr=subprocess.STDOUT,
        env=env,
    )
    pids.append(backend.pid)

    print("Waiting for backend (loading models, ~20s)...")
    if wait_for_port(bp, timeout=60):
        print(f"  ✓ Backend ready on port {bp}")
    else:
        print(f"  ✗ Backend failed — check: tail /tmp/aflhr_backend.log")

    # --- Frontend ---
    fp = find_free_port(PREFERRED["frontend"])
    print(f"Starting frontend on port {fp}...")

    # Write VITE_API_URL so frontend knows where the backend is
    env["VITE_API_URL"] = f"http://localhost:{bp}"

    frontend = subprocess.Popen(
        [NPM, "run", "dev", "--", "--port", str(fp), "--strictPort"],
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend"),
        stdout=open("/tmp/aflhr_frontend.log", "w"),
        stderr=subprocess.STDOUT,
        env=env,
    )
    pids.append(frontend.pid)

    if wait_for_port(fp, timeout=15):
        print(f"  ✓ Frontend ready on port {fp}")
    else:
        print(f"  ✗ Frontend failed — check: tail /tmp/aflhr_frontend.log")

    # --- Docs ---
    dp = find_free_port(PREFERRED["docs"])
    print(f"Starting docs on port {dp}...")
    docs = subprocess.Popen(
        [NPX, "docusaurus", "start", "--port", str(dp), "--no-open"],
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs"),
        stdout=open("/tmp/aflhr_docs.log", "w"),
        stderr=subprocess.STDOUT,
        env=env,
    )
    pids.append(docs.pid)

    if wait_for_port(dp, timeout=15):
        print(f"  ✓ Docs ready on port {dp}")
    else:
        print(f"  ✗ Docs failed — check: tail /tmp/aflhr_docs.log")

    # Save PIDs for stop
    with open(PID_FILE, "w") as f:
        for pid in pids:
            f.write(f"{pid}\n")

    print()
    print(f"  → App:  http://localhost:{fp}")
    print(f"  → Docs: http://localhost:{dp}")
    print(f"  → API:  http://localhost:{bp}/docs")
    print()


if __name__ == "__main__":
    main()
