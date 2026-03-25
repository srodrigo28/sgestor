import os
from dataclasses import dataclass

from common.env_loader import load_env_file


def truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str
    debug: bool
    secret_key: str
    using_default_secret: bool
    auto_migrate_on_startup: bool


def get_settings() -> Settings:
    load_env_file()

    app_env = (os.getenv("APP_ENV") or "development").strip().lower() or "development"
    default_debug = app_env != "production"
    debug = truthy(os.getenv("APP_DEBUG")) if os.getenv("APP_DEBUG") is not None else default_debug

    secret_key = os.getenv("SECRET_KEY") or "chave_super_secreta_para_sessao"
    using_default_secret = os.getenv("SECRET_KEY") is None

    return Settings(
        app_env=app_env,
        debug=debug,
        secret_key=secret_key,
        using_default_secret=using_default_secret,
        auto_migrate_on_startup=truthy(os.getenv("AUTO_MIGRATE_ON_STARTUP")),
    )
