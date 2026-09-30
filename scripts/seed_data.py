import sys
import os
import asyncio
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.seed import seed_all

if __name__ == "__main__":
    print("[INFO] Starting AI Resume Analyzer database seeding...")
    asyncio.run(seed_all())
    print("[SUCCESS] Database seeding finished successfully!")
