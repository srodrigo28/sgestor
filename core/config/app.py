from flask import Flask, session

from common.database import get_db_connection
from config.settings import get_settings
from config.urls import register_blueprints
from db import migration as migration_runner


def create_app() -> Flask:
    settings = get_settings()

    if settings.auto_migrate_on_startup:
        try:
            migration_runner.check_and_migrate_db(auto_seed=True)
        except Exception as e:
            print(f"ATENCAO: Falha ao rodar migrations automaticas: {e}")

    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = settings.secret_key
    app.config["APP_ENV"] = settings.app_env
    app.config["DEBUG"] = settings.debug

    if settings.app_env == "production" and settings.using_default_secret:
        print("WARNING: SECRET_KEY is not set. Using the default (unsafe) fallback.")

    register_blueprints(app)

    @app.context_processor
    def inject_menu_permissions():
        role = session.get("role", "pessoal")
        default_permissions = {
            "dashboard": True,
            "schedule": True,
            "tasks": True,
            "financial": True,
            "products": True,
            "clients": True,
            "budgets": True,
            "services": True,
            "mechanics": True,
            "admin_users": role == "admin",
        }
        if "id" not in session:
            return dict(menu_permissions=default_permissions, user_role=role)

        try:
            conn = get_db_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT menu_key, can_view FROM role_menu_permissions WHERE role = %s", (role,))
                rows = cursor.fetchall()
                db_perms = {row["menu_key"]: bool(row["can_view"]) for row in rows}
                permissions = default_permissions.copy()
                permissions.update(db_perms or {})
            finally:
                conn.close()
        except Exception:
            permissions = default_permissions

        return dict(menu_permissions=permissions, user_role=role)

    return app
