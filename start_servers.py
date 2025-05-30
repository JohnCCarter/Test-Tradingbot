"""
Startar både backend (Flask) och frontend (Next.js) parallellt.
Backend körs via dashboard.py, frontend via npm run dev.
"""

import subprocess
import threading
import os
import sys


def run_backend():
    """Startar Flask-backend via dashboard.py."""
    backend_dir = os.path.join(os.path.dirname(__file__), "backend", "src")
    cmd = [sys.executable, "dashboard.py"]
    print(f"[Backend] Startar: {' '.join(cmd)} i {backend_dir}")
    subprocess.run(cmd, cwd=backend_dir)


def run_frontend():
    """Startar Next.js frontend via npm run dev."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    cmd = ["npm", "run", "dev"]
    print(f"[Frontend] Startar: {' '.join(cmd)} i {frontend_dir}")
    subprocess.run(cmd, cwd=frontend_dir)


def main():
    """Startar backend och frontend parallellt."""
    t1 = threading.Thread(target=run_backend)
    t2 = threading.Thread(target=run_frontend)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
