from flask import Blueprint, redirect, render_template, request, session, url_for

from apps.auth.views import login_required
from common.database import get_db_connection


attendance_bp = Blueprint(
    "attendance",
    __name__,
    template_folder="../../templates/attendance",
    url_prefix="/atendimentos",
)

CLIENTS_PER_PAGE = 5
CLIENT_OPTIONAL_COLUMNS = [
    "legal_name",
    "trade_name",
    "contract_start_date",
    "cep",
    "complement",
    "address_number",
    "neighborhood",
    "city",
    "state",
]


def _fetch_scalar(cursor, query, params):
    cursor.execute(query, params)
    row = cursor.fetchone() or {}
    return int(row.get("total") or 0)


def _fetch_value(cursor, query, params):
    cursor.execute(query, params)
    row = cursor.fetchone() or {}
    return float(row.get("total") or 0)


def _has_menu_access() -> bool:
    return session.get("role") in {"admin", "atendimentos"}


def _get_client_columns(cursor):
    cursor.execute("SHOW COLUMNS FROM clients")
    return {row["Field"] for row in cursor.fetchall()}


def _client_select_expr(column, available_columns):
    if column in available_columns:
        return f"c.{column}"
    return f"NULL AS {column}"


@attendance_bp.route("/")
@login_required
def index():
    if not _has_menu_access():
        return redirect(url_for("tasks.dashboard"))

    user_id = session["id"]
    client_page = max(request.args.get("client_page", 1, type=int), 1)
    client_offset = (client_page - 1) * CLIENTS_PER_PAGE

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {
            "appointments_today": _fetch_scalar(cursor, "SELECT COUNT(*) AS total FROM appointments WHERE user_id = %s AND DATE(start_time) = CURDATE()", (user_id,)),
            "appointments_pending": _fetch_scalar(cursor, "SELECT COUNT(*) AS total FROM appointments WHERE user_id = %s AND status = 'scheduled' AND start_time >= NOW()", (user_id,)),
            "tasks_open": _fetch_scalar(cursor, "SELECT COUNT(*) AS total FROM tasks WHERE user_id = %s AND status <> 'feito'", (user_id,)),
            "clients_total": _fetch_scalar(cursor, "SELECT COUNT(*) AS total FROM clients WHERE user_id = %s", (user_id,)),
            "employees_active": _fetch_scalar(cursor, "SELECT COUNT(*) AS total FROM mechanics WHERE user_id = %s AND COALESCE(is_active, 1) = 1", (user_id,)),
            "income_month": _fetch_value(cursor, "SELECT COALESCE(SUM(amount), 0) AS total FROM financial_income WHERE user_id = %s AND entry_date >= DATE_FORMAT(CURDATE(), '%%Y-%%m-01') AND entry_date < DATE_ADD(DATE_FORMAT(CURDATE(), '%%Y-%%m-01'), INTERVAL 1 MONTH)", (user_id,)),
            "expenses_month": _fetch_value(cursor, "SELECT COALESCE(SUM(amount), 0) AS total FROM financial_expenses WHERE user_id = %s AND due_date >= DATE_FORMAT(CURDATE(), '%%Y-%%m-01') AND due_date < DATE_ADD(DATE_FORMAT(CURDATE(), '%%Y-%%m-01'), INTERVAL 1 MONTH)", (user_id,)),
        }

        client_columns = _get_client_columns(cursor)
        optional_selects = ",\n                ".join(
            _client_select_expr(column, client_columns) for column in CLIENT_OPTIONAL_COLUMNS
        )
        optional_group_by = ",\n                ".join(
            f"c.{column}" for column in CLIENT_OPTIONAL_COLUMNS if column in client_columns
        )
        group_by_clause = ",\n                ".join(
            ["c.id", "c.name", "c.sector", "c.cpf", "c.phone1", "c.phone2", "c.address"]
            + ([optional_group_by] if optional_group_by else [])
        )

        cursor.execute(
            f"""
            SELECT
                c.id,
                c.name,
                {optional_selects},
                c.sector,
                c.cpf,
                c.phone1,
                c.phone2,
                c.address,
                COUNT(b.id) AS contracts_total
            FROM clients c
            LEFT JOIN budgets b ON b.client_id = c.id AND b.user_id = c.user_id
            WHERE c.user_id = %s
            GROUP BY
                {group_by_clause}
            ORDER BY contracts_total DESC, c.name ASC
            LIMIT %s OFFSET %s
            """,
            (user_id, CLIENTS_PER_PAGE, client_offset),
        )
        contract_clients = cursor.fetchall()

        cursor.execute(
            """
            SELECT a.id, a.title, a.start_time, a.status, c.name AS client_name
            FROM appointments a
            LEFT JOIN clients c ON c.id = a.client_id
            WHERE a.user_id = %s
              AND a.start_time >= NOW()
            ORDER BY a.start_time ASC
            LIMIT 5
            """,
            (user_id,),
        )
        upcoming_appointments = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, title, category, status, due_date
            FROM tasks
            WHERE user_id = %s
              AND status <> 'feito'
            ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC, created_at DESC
            LIMIT 5
            """,
            (user_id,),
        )
        task_queue = cursor.fetchall()
    finally:
        conn.close()

    summary = {"balance_month": stats["income_month"] - stats["expenses_month"]}
    client_total_pages = max((stats["clients_total"] + CLIENTS_PER_PAGE - 1) // CLIENTS_PER_PAGE, 1)

    return render_template(
        "attendance/index.html",
        stats=stats,
        summary=summary,
        upcoming_appointments=upcoming_appointments,
        task_queue=task_queue,
        contract_clients=contract_clients,
        client_page=client_page,
        client_total_pages=client_total_pages,
    )
