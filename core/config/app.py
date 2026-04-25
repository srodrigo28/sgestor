from datetime import datetime

from flask import Flask, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from common.database import get_db_connection
from config.settings import get_settings
from config.urls import register_blueprints
from db import migration as migration_runner


def _format_mobile_appointments(rows):
    appointments = []
    now = datetime.now()
    for row in rows:
        start_time = row.get("start_time")
        end_time = row.get("end_time")
        client_name = (row.get("client_name") or "").strip()
        title = (row.get("title") or "").strip()
        description = (row.get("description") or "").strip()
        is_overdue = bool(start_time and start_time < now)

        period = ""
        date_badge = ""
        time_badge = ""
        if start_time:
            date_badge = start_time.strftime("%d/%m")
            time_badge = start_time.strftime("%H:%M")
            if end_time:
                time_badge = f"{time_badge} - {end_time.strftime('%H:%M')}"
            period = start_time.strftime("%d/%m")
            if end_time:
                period = f"{period} as {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            else:
                period = f"{period} as {start_time.strftime('%H:%M')}"

        appointments.append(
            {
                "id": row.get("id"),
                "title": title,
                "client_name": client_name,
                "description": description,
                "status": row.get("status") or "scheduled",
                "period_label": period,
                "date_badge": date_badge,
                "time_badge": time_badge,
                "is_overdue": is_overdue,
            }
        )

    return appointments


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
            "schedule_list": role in {"admin", "oficina", "atendimentos", "pessoal"},
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
        empty_mobile_appointments = {
            "mobile_starred_appointments": [],
            "mobile_starred_appointments_count": 0,
        }
        if "id" not in session:
            return dict(
                menu_permissions=default_permissions,
                user_role=role,
                asset_url=asset_url,
                **empty_mobile_appointments,
            )

        appointments = []
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

                if permissions.get("schedule"):
                    cursor.execute(
                        """
                        SELECT a.id, a.title, a.description, a.start_time, a.end_time, a.status, c.name AS client_name
                        FROM appointments a
                        LEFT JOIN clients c ON c.id = a.client_id
                        WHERE a.user_id = %s
                          AND a.status = 'scheduled'
                        ORDER BY a.start_time ASC
                        LIMIT 6
                        """,
                        (session["id"],),
                    )
                    appointments = _format_mobile_appointments(cursor.fetchall())
            finally:
                conn.close()
        except Exception:
            permissions = default_permissions
            appointments = []

        return dict(
            menu_permissions=permissions,
            user_role=role,
            asset_url=asset_url,
            mobile_starred_appointments=appointments,
            mobile_starred_appointments_count=len(appointments),
        )

    return app
