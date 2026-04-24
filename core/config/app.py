from flask import Flask, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

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
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.secret_key = settings.secret_key
    app.config["APP_ENV"] = settings.app_env
    app.config["DEBUG"] = settings.debug
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.jinja_env.auto_reload = True

    @app.after_request
    def force_html_utf8(response):
        if response.mimetype == "text/html":
            response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    if settings.app_env == "production" and settings.using_default_secret:
        print("WARNING: SECRET_KEY is not set. Using the default (unsafe) fallback.")

    register_blueprints(app)

    @app.context_processor
    def inject_menu_permissions():
        def asset_url(path: str | None) -> str:
            if not path:
                return ""
            valor = str(path).strip()
            if not valor:
                return ""
            if valor.startswith(("http://", "https://", "data:")):
                return valor
            if valor.startswith("/static/"):
                return f"{request.script_root}{valor}"
            if valor.startswith("static/"):
                return f"{request.script_root}/{valor}"
            return valor

        role = session.get("role", "pessoal")
        default_permissions = {
            "dashboard": True,
            "attendance": role in {"admin", "atendimentos"},
            "schedule": role in {"admin", "oficina", "atendimentos", "pessoal"},
            "tasks": role in {"admin", "oficina", "atendimentos", "pessoal"},
            "financial": role in {"admin", "oficina", "loja", "atendimentos", "pessoal"},
            "products": role in {"admin", "oficina", "loja"},
            "clients": role in {"admin", "oficina", "loja", "atendimentos"},
            "budgets": role in {"admin", "oficina", "loja"},
            "services": role in {"admin", "oficina", "loja"},
            "employees": role in {"admin", "oficina"},
            "mechanics": role in {"admin", "oficina"},
            "admin_users": role == "admin",
        }
        if "id" not in session:
            return dict(
                menu_permissions=default_permissions,
                user_role=role,
                asset_url=asset_url,
            )

        try:
            conn = get_db_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT menu_key, can_view FROM role_menu_permissions WHERE role = %s", (role,))
                rows = cursor.fetchall()
                db_perms = {row["menu_key"]: bool(row["can_view"]) for row in rows}
                permissions = default_permissions.copy()
                permissions.update(db_perms or {})
                if permissions.get("mechanics") and "employees" not in db_perms:
                    permissions["employees"] = True
                if role in {"admin", "oficina"}:
                    permissions["employees"] = True
                    permissions["mechanics"] = True
            finally:
                conn.close()
        except Exception:
            permissions = default_permissions

        return dict(
            menu_permissions=permissions,
            user_role=role,
            asset_url=asset_url,
        )

    return app
