import subprocess
import sys
from pathlib import Path

MIGRATION_FILE = Path(__file__).resolve().parent / "db" / "migration.py"


def main() -> int:
    print("[LEGACY] apply_sql_17.py descontinuado.")
    print("Use o fluxo oficial: python db/migration.py up")
    return subprocess.call([sys.executable, str(MIGRATION_FILE), "up"], cwd=str(MIGRATION_FILE.parent))


if __name__ == "__main__":
    raise SystemExit(main())


