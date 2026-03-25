import os
import mysql.connector
from common.env_loader import load_env_file

def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_app_env() -> str:
    env = (os.getenv("APP_ENV") or "development").strip().lower()
    return env or "development"


def _is_local_db_host(host: str) -> bool:
    h = (host or "").strip().lower()
    return h in {"localhost", "127.0.0.1", "::1"}


def get_db_connection():
    # Loads a dotenv file only if ENV_FILE is set (or defaults to .env).
    # Non-destructive: does not override already-exported env vars.
    load_env_file()

    host = os.getenv("DB_HOST", "localhost")
    app_env = _get_app_env()

    # Safety guard: avoid accidentally pointing dev to the client's production DB.
    if app_env != "production" and not _is_local_db_host(host) and not _truthy(os.getenv("ALLOW_REMOTE_DB")):
        raise RuntimeError(
            "Refusing to connect to a non-local DB while APP_ENV != 'production'. "
            f"(APP_ENV='{app_env}', DB_HOST='{host}'). "
            "Use a local DB for development (recommended) or set APP_ENV=production / ALLOW_REMOTE_DB=1 intentionally."
        )

    return mysql.connector.connect(
        host=host,
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "flask_crud"),
    )

