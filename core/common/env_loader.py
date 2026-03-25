import os
from pathlib import Path


def load_env_file(path: str | Path = ".env") -> None:
    """Load KEY=VALUE pairs from a .env file into process env (non-destructive).

    - Only sets variables that are not already present in os.environ.
    - Keeps parsing intentionally simple (good enough for local dev).
    """
    # Allow selecting a specific env file at runtime (useful for dev/prod split).
    # Example: ENV_FILE=.env.prod gunicorn -w 2 -b 127.0.0.1:5050 main:app
    env_file = os.getenv("ENV_FILE")
    if env_file:
        path = env_file

    env_path = Path(path)
    candidates = [env_path]
    if not env_path.is_absolute():
        # Allow running the app from another working directory.
        base_dir = Path(__file__).resolve().parent.parent
        candidates.append(base_dir / env_path)

    env_path = next((p for p in candidates if p.exists()), None)
    if env_path is None:
        return

    try:
        content = env_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback for Windows/legacy encodings.
        content = env_path.read_text(encoding="latin-1")

    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        # Strip simple quotes around the value.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        if key not in os.environ:
            os.environ[key] = value
