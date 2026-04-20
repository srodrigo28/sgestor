from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from common.database import get_db_connection
from datetime import datetime, timedelta
from calendar import monthrange
import json


tasks_bp = Blueprint('tasks', __name__)

TASK_CATEGORY_DEFAULTS = [
    {'name': 'Trabalho', 'icon': '💼', 'color': '#3b82f6'},
    {'name': 'Estudo', 'icon': '📚', 'color': '#8b5cf6'},
    {'name': 'Pessoal', 'icon': '🏠', 'color': '#f97316'},
    {'name': 'Saúde', 'icon': '💪', 'color': '#22c55e'},
]


MONTH_NAMES_PT_BR = {
    1: 'janeiro',
    2: 'fevereiro',
    3: 'marco',
    4: 'abril',
    5: 'maio',
    6: 'junho',
    7: 'julho',
    8: 'agosto',
    9: 'setembro',
    10: 'outubro',
    11: 'novembro',
    12: 'dezembro',
}


def _format_dashboard_date(now):
    month_name = MONTH_NAMES_PT_BR.get(now.month, '')
    return f"{now.day:02d} de {month_name} de {now.year}"


def _get_period_ranges(now):
    day_start = datetime(now.year, now.month, now.day)
    next_day = day_start + timedelta(days=1)
    week_start = day_start - timedelta(days=day_start.weekday())
    month_start = day_start.replace(day=1)
    month_days = monthrange(now.year, now.month)[1]
    next_month = month_start.replace(day=month_days) + timedelta(days=1)

    return {
        'day': {'start': day_start, 'end': next_day},
        'week': {'start': week_start, 'end': next_day},
        'month': {'start': month_start, 'end': next_month},
    }


def _fetch_scalar(cursor, query, params):
    cursor.execute(query, params)
    row = cursor.fetchone() or {}
    return int(row.get('total') or 0)


def _fetch_period_stats(cursor, user_id, start, end):
    budgets = _fetch_scalar(
        cursor,
        """
            SELECT COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
        """,
        (user_id, start, end),
    )

    waiting = _fetch_scalar(
        cursor,
        """
            SELECT COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'sent'
              AND created_at >= %s
              AND created_at < %s
        """,
        (user_id, start, end),
    )

    approved = _fetch_scalar(
        cursor,
        """
            SELECT COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'approved'
              AND COALESCE(approved_at, created_at) >= %s
              AND COALESCE(approved_at, created_at) < %s
        """,
        (user_id, start, end),
    )

    clients = _fetch_scalar(
        cursor,
        """
            SELECT COUNT(*) AS total
            FROM clients
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
        """,
        (user_id, start, end),
    )

    return {
        'budgets': budgets,
        'waiting': waiting,
        'approved': approved,
        'clients': clients,
    }


def _fetch_grouped_counts(cursor, query, params, key_name):
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return {row[key_name]: int(row['total'] or 0) for row in rows if row.get(key_name) is not None}


def _build_chart_data(cursor, user_id, now):
    ranges = _get_period_ranges(now)
    chart_data = {}

    day_start = ranges['day']['start']
    day_end = ranges['day']['end']
    day_budget_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT HOUR(created_at) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
            GROUP BY HOUR(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, day_start, day_end),
        'bucket',
    )
    day_waiting_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT HOUR(created_at) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'sent'
              AND created_at >= %s
              AND created_at < %s
            GROUP BY HOUR(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, day_start, day_end),
        'bucket',
    )
    day_approved_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT HOUR(COALESCE(approved_at, created_at)) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'approved'
              AND COALESCE(approved_at, created_at) >= %s
              AND COALESCE(approved_at, created_at) < %s
            GROUP BY HOUR(COALESCE(approved_at, created_at))
            ORDER BY bucket ASC
        """,
        (user_id, day_start, day_end),
        'bucket',
    )
    day_client_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT HOUR(created_at) AS bucket, COUNT(*) AS total
            FROM clients
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
            GROUP BY HOUR(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, day_start, day_end),
        'bucket',
    )

    chart_data['day'] = {
        'labels': [f'{hour:02d}h' for hour in range(24)],
        'budgets': [day_budget_map.get(hour, 0) for hour in range(24)],
        'waiting': [day_waiting_map.get(hour, 0) for hour in range(24)],
        'approved': [day_approved_map.get(hour, 0) for hour in range(24)],
        'clients': [day_client_map.get(hour, 0) for hour in range(24)],
    }

    week_start = ranges['week']['start'].date()
    week_end = ranges['week']['end'].date()
    week_budget_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(created_at) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
            GROUP BY DATE(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, week_start, week_end),
        'bucket',
    )
    week_waiting_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(created_at) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'sent'
              AND created_at >= %s
              AND created_at < %s
            GROUP BY DATE(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, week_start, week_end),
        'bucket',
    )
    week_approved_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(COALESCE(approved_at, created_at)) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'approved'
              AND COALESCE(approved_at, created_at) >= %s
              AND COALESCE(approved_at, created_at) < %s
            GROUP BY DATE(COALESCE(approved_at, created_at))
            ORDER BY bucket ASC
        """,
        (user_id, week_start, week_end),
        'bucket',
    )
    week_client_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(created_at) AS bucket, COUNT(*) AS total
            FROM clients
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
            GROUP BY DATE(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, week_start, week_end),
        'bucket',
    )

    week_days = [week_start + timedelta(days=i) for i in range((week_end - week_start).days)]
    chart_data['week'] = {
        'labels': [day.strftime('%d/%m') for day in week_days],
        'budgets': [week_budget_map.get(day, 0) for day in week_days],
        'waiting': [week_waiting_map.get(day, 0) for day in week_days],
        'approved': [week_approved_map.get(day, 0) for day in week_days],
        'clients': [week_client_map.get(day, 0) for day in week_days],
    }

    month_start = ranges['month']['start'].date()
    month_end = ranges['month']['end'].date()
    month_budget_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(created_at) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
            GROUP BY DATE(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, month_start, month_end),
        'bucket',
    )
    month_waiting_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(created_at) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'sent'
              AND created_at >= %s
              AND created_at < %s
            GROUP BY DATE(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, month_start, month_end),
        'bucket',
    )
    month_approved_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(COALESCE(approved_at, created_at)) AS bucket, COUNT(*) AS total
            FROM budgets
            WHERE user_id = %s
              AND COALESCE(approval_status, status) = 'approved'
              AND COALESCE(approved_at, created_at) >= %s
              AND COALESCE(approved_at, created_at) < %s
            GROUP BY DATE(COALESCE(approved_at, created_at))
            ORDER BY bucket ASC
        """,
        (user_id, month_start, month_end),
        'bucket',
    )
    month_client_map = _fetch_grouped_counts(
        cursor,
        """
            SELECT DATE(created_at) AS bucket, COUNT(*) AS total
            FROM clients
            WHERE user_id = %s
              AND created_at >= %s
              AND created_at < %s
            GROUP BY DATE(created_at)
            ORDER BY bucket ASC
        """,
        (user_id, month_start, month_end),
        'bucket',
    )

    month_days = (month_end - month_start).days
    month_labels = []
    month_budgets = []
    month_waiting = []
    month_approved = []
    month_clients = []
    for day_offset in range(month_days):
        current_day = month_start + timedelta(days=day_offset)
        month_labels.append(current_day.strftime('%d/%m'))
        month_budgets.append(month_budget_map.get(current_day, 0))
        month_waiting.append(month_waiting_map.get(current_day, 0))
        month_approved.append(month_approved_map.get(current_day, 0))
        month_clients.append(month_client_map.get(current_day, 0))

    chart_data['month'] = {
        'labels': month_labels,
        'budgets': month_budgets,
        'waiting': month_waiting,
        'approved': month_approved,
        'clients': month_clients,
    }

    return chart_data


def _ensure_task_categories_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS task_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(80) NOT NULL,
            icon VARCHAR(20) DEFAULT '🏷️',
            color VARCHAR(20) DEFAULT '#6b7280',
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_task_categories_user_name (user_id, name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )


def _normalize_category_name(value):
    if not value:
        return ''
    return ' '.join(value.strip().split())


def _get_default_category_meta(name):
    normalized = (name or '').strip().lower()
    for item in TASK_CATEGORY_DEFAULTS:
        if item['name'].lower() == normalized:
            return item
    return {'name': name or 'Geral', 'icon': '🏷️', 'color': '#6b7280'}


def _sync_legacy_categories(cursor, user_id):
    cursor.execute("SELECT DISTINCT category FROM tasks WHERE user_id = %s AND category IS NOT NULL AND TRIM(category) <> ''", (user_id,))
    legacy_names = [_normalize_category_name(row['category']) for row in cursor.fetchall() if row.get('category')]
    if not legacy_names:
        return

    cursor.execute("SELECT name FROM task_categories WHERE user_id = %s", (user_id,))
    existing = {_normalize_category_name(row['name']) for row in cursor.fetchall()}

    for name in legacy_names:
        if not name or name in existing:
            continue
        meta = _get_default_category_meta(name)
        cursor.execute(
            "INSERT INTO task_categories (user_id, name, icon, color) VALUES (%s, %s, %s, %s)",
            (user_id, name, meta['icon'], meta['color'])
        )
        existing.add(name)


def _ensure_task_categories_ready(cursor, user_id):
    _ensure_task_categories_table(cursor)
    cursor.execute("SELECT COUNT(*) AS total FROM task_categories WHERE user_id = %s", (user_id,))
    total = int((cursor.fetchone() or {}).get('total') or 0)
    if total == 0:
        for item in TASK_CATEGORY_DEFAULTS:
            cursor.execute(
                "INSERT INTO task_categories (user_id, name, icon, color) VALUES (%s, %s, %s, %s)",
                (user_id, item['name'], item['icon'], item['color'])
            )
    _sync_legacy_categories(cursor, user_id)


def _fetch_task_categories(cursor, user_id):
    _ensure_task_categories_ready(cursor, user_id)
    cursor.execute(
        """
        SELECT tc.*, COUNT(t.id) AS task_count
        FROM task_categories tc
        LEFT JOIN tasks t
          ON t.user_id = tc.user_id
         AND t.category = tc.name
        WHERE tc.user_id = %s AND tc.is_active = 1
        GROUP BY tc.id, tc.user_id, tc.name, tc.icon, tc.color, tc.is_active, tc.created_at, tc.updated_at
        ORDER BY tc.name ASC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    for row in rows:
        row['task_count'] = int(row.get('task_count') or 0)
    return rows


def _resolve_task_category(cursor, user_id, category_id=None, category_name=None):
    _ensure_task_categories_ready(cursor, user_id)
    if category_id:
        cursor.execute(
            "SELECT * FROM task_categories WHERE id = %s AND user_id = %s AND is_active = 1",
            (category_id, user_id)
        )
        found = cursor.fetchone()
        if found:
            return found

    normalized_name = _normalize_category_name(category_name)
    if normalized_name:
        cursor.execute(
            "SELECT * FROM task_categories WHERE user_id = %s AND name = %s AND is_active = 1",
            (user_id, normalized_name)
        )
        found = cursor.fetchone()
        if found:
            return found

    cursor.execute(
        "SELECT * FROM task_categories WHERE user_id = %s AND is_active = 1 ORDER BY name ASC LIMIT 1",
        (user_id,)
    )
    return cursor.fetchone()


def _build_task_chart_data(cursor, user_id):
    cursor.execute(
        """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM tasks
        WHERE user_id = %s
          AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date ASC
        """,
        (user_id,)
    )
    results = cursor.fetchall()
    chart_data = {'dates': [], 'counts': []}
    dates_map = {str(row['date']): row['count'] for row in results}

    for i in range(6, -1, -1):
        date_obj = datetime.now() - timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d')
        chart_data['dates'].append(date_obj.strftime('%d/%m'))
        chart_data['counts'].append(dates_map.get(date_str, 0))

    return chart_data


@tasks_bp.route('/dashboard')
def dashboard():
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    now = datetime.now()
    period_ranges = _get_period_ranges(now)
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        stats_by_period = {
            period: _fetch_period_stats(cursor, user_id, bounds['start'], bounds['end'])
            for period, bounds in period_ranges.items()
        }
        chart_data_by_period = _build_chart_data(cursor, user_id, now)
    finally:
        conn.close()

    return render_template(
        'dashboard.html',
        stats=stats_by_period['day'],
        stats_by_period=stats_by_period,
        chart_data_by_period=chart_data_by_period,
        selected_period='day',
        now=now,
        current_date_label=_format_dashboard_date(now),
    )


@tasks_bp.route('/tasks/add', methods=['POST'])
def create_task():
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    title = request.form['title']
    description = request.form.get('description', '')
    category_id = request.form.get('category_id')
    due_date_raw = (request.form.get('due_date') or '').strip()
    due_date = due_date_raw if due_date_raw else None
    user_id = session['id']

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        category = _resolve_task_category(cursor, user_id, category_id=category_id, category_name=request.form.get('category'))
        if not category:
            flash('Nenhuma categoria disponível para criar a tarefa.')
            return redirect(url_for('tasks.list'))

        cursor.execute(
            'INSERT INTO tasks (user_id, title, description, category, due_date) VALUES (%s, %s, %s, %s, %s)',
            (user_id, title, description, category['name'], due_date)
        )
        conn.commit()
    finally:
        conn.close()

    flash('Tarefa criada com sucesso!')
    return redirect(url_for('tasks.list'))


@tasks_bp.route('/tasks')
def list():
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['id']
    category_id = (request.args.get('category') or 'all').strip()
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    task_categories = _fetch_task_categories(cursor, user_id)
    categories_by_name = {_normalize_category_name(item['name']): item for item in task_categories}
    selected_category = None
    if category_id and category_id != 'all':
        selected_category = _resolve_task_category(cursor, user_id, category_id=category_id, category_name=category_id)

    query = 'SELECT * FROM tasks WHERE user_id = %s'
    params = [user_id]

    if selected_category:
        query += ' AND category = %s'
        params.append(selected_category['name'])
        category_id = str(selected_category['id'])
    else:
        category_id = 'all'

    if search:
        query += ' AND (title LIKE %s OR description LIKE %s)'
        params.extend([f'%{search}%', f'%{search}%'])

    count_sql = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
    cursor.execute(count_sql, tuple(params))
    total_tasks = cursor.fetchone()['total']
    total_pages = (total_tasks + per_page - 1) // per_page if total_tasks else 1

    query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
    params.extend([per_page, offset])
    cursor.execute(query, tuple(params))
    tasks = cursor.fetchall()

    for task in tasks:
        category_meta = categories_by_name.get(_normalize_category_name(task.get('category')))
        task['category_id'] = category_meta['id'] if category_meta else ''
        task['category_icon'] = category_meta['icon'] if category_meta else '🏷️'
        task['category_color'] = category_meta['color'] if category_meta else '#6b7280'

    cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = %s", (user_id,))
    total = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'feito'", (user_id,))
    done = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'fazendo'", (user_id,))
    doing = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'a_fazer'", (user_id,))
    todo = cursor.fetchone()['count']

    stats = {
        'total': total,
        'done': done,
        'doing': doing,
        'todo': todo,
    }

    chart_data = _build_task_chart_data(cursor, user_id)
    conn.close()

    return render_template(
        'tasks.html',
        tasks=tasks,
        active_category_id=category_id,
        task_categories=task_categories,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        search=search,
        stats=stats,
        chart_data_json=json.dumps(chart_data),
        stats_json=json.dumps(stats),
    )


@tasks_bp.route('/tasks/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    title = request.form['title']
    description = request.form.get('description', '')
    category_id = request.form.get('category_id')
    status = request.form.get('status', 'a_fazer')
    due_date_raw = (request.form.get('due_date') or '').strip()
    due_date = due_date_raw if due_date_raw else None
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        'SELECT status, completed_at FROM tasks WHERE id = %s AND user_id = %s',
        (task_id, user_id)
    )
    current_task = cursor.fetchone()

    if not current_task:
        conn.close()
        flash('Tarefa não encontrada ou sem permissão.')
        return redirect(url_for('tasks.list'))

    category = _resolve_task_category(cursor, user_id, category_id=category_id, category_name=request.form.get('category'))
    if not category:
        conn.close()
        flash('Categoria inválida para esta conta.')
        return redirect(url_for('tasks.list'))

    existing_completed_at = current_task.get('completed_at')
    final_completed_at = existing_completed_at if status == 'feito' and existing_completed_at else (datetime.now() if status == 'feito' else None)

    cursor.execute(
        'UPDATE tasks SET title = %s, description = %s, category = %s, status = %s, completed_at = %s, due_date = %s WHERE id = %s AND user_id = %s',
        (title, description, category['name'], status, final_completed_at, due_date, task_id, user_id)
    )
    conn.commit()
    conn.close()

    flash('Tarefa atualizada com sucesso!')
    return redirect(url_for('tasks.list'))


@tasks_bp.route('/tasks/categories/add', methods=['POST'])
def add_category():
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['id']
    name = _normalize_category_name(request.form.get('name'))
    icon = (request.form.get('icon') or '🏷️').strip()[:10] or '🏷️'
    color = (request.form.get('color') or '#6b7280').strip() or '#6b7280'

    if not name:
        flash('Informe o nome da categoria.')
        return redirect(url_for('tasks.list'))

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        _ensure_task_categories_ready(cursor, user_id)
        cursor.execute('SELECT id FROM task_categories WHERE user_id = %s AND name = %s', (user_id, name))
        if cursor.fetchone():
            flash('Já existe uma categoria com esse nome.')
            return redirect(url_for('tasks.list'))

        cursor.execute(
            'INSERT INTO task_categories (user_id, name, icon, color) VALUES (%s, %s, %s, %s)',
            (user_id, name, icon, color)
        )
        conn.commit()
        flash('Categoria criada com sucesso!')
    finally:
        conn.close()

    return redirect(url_for('tasks.list'))


@tasks_bp.route('/tasks/categories/edit/<int:category_id>', methods=['POST'])
def edit_category(category_id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['id']
    name = _normalize_category_name(request.form.get('name'))
    icon = (request.form.get('icon') or '🏷️').strip()[:10] or '🏷️'
    color = (request.form.get('color') or '#6b7280').strip() or '#6b7280'

    if not name:
        flash('Informe o nome da categoria.')
        return redirect(url_for('tasks.list'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    _ensure_task_categories_ready(cursor, user_id)

    cursor.execute('SELECT * FROM task_categories WHERE id = %s AND user_id = %s', (category_id, user_id))
    category = cursor.fetchone()
    if not category:
        conn.close()
        flash('Categoria não encontrada.')
        return redirect(url_for('tasks.list'))

    cursor.execute(
        'SELECT id FROM task_categories WHERE user_id = %s AND name = %s AND id <> %s',
        (user_id, name, category_id)
    )
    if cursor.fetchone():
        conn.close()
        flash('Já existe outra categoria com esse nome.')
        return redirect(url_for('tasks.list'))

    old_name = category['name']
    cursor.execute(
        'UPDATE task_categories SET name = %s, icon = %s, color = %s WHERE id = %s AND user_id = %s',
        (name, icon, color, category_id, user_id)
    )
    if old_name != name:
        cursor.execute('UPDATE tasks SET category = %s WHERE user_id = %s AND category = %s', (name, user_id, old_name))

    conn.commit()
    conn.close()

    flash('Categoria atualizada com sucesso!')
    return redirect(url_for('tasks.list'))


@tasks_bp.route('/tasks/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    _ensure_task_categories_ready(cursor, user_id)

    cursor.execute('SELECT * FROM task_categories WHERE id = %s AND user_id = %s', (category_id, user_id))
    category = cursor.fetchone()
    if not category:
        conn.close()
        flash('Categoria não encontrada.')
        return redirect(url_for('tasks.list'))

    cursor.execute('SELECT COUNT(*) AS total FROM task_categories WHERE user_id = %s AND is_active = 1', (user_id,))
    total_categories = int((cursor.fetchone() or {}).get('total') or 0)
    if total_categories <= 1:
        conn.close()
        flash('Você precisa manter pelo menos uma categoria ativa.')
        return redirect(url_for('tasks.list'))

    cursor.execute('SELECT COUNT(*) AS total FROM tasks WHERE user_id = %s AND category = %s', (user_id, category['name']))
    in_use = int((cursor.fetchone() or {}).get('total') or 0)
    if in_use > 0:
        conn.close()
        flash('Essa categoria possui tarefas vinculadas e não pode ser excluída.')
        return redirect(url_for('tasks.list'))

    cursor.execute('DELETE FROM task_categories WHERE id = %s AND user_id = %s', (category_id, user_id))
    conn.commit()
    conn.close()

    flash('Categoria removida com sucesso!')
    return redirect(url_for('tasks.list'))


@tasks_bp.route('/tasks/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = %s AND user_id = %s', (task_id, session['id']))
    conn.commit()
    conn.close()

    flash('Tarefa removida com sucesso!')
    return redirect(url_for('tasks.list'))


@tasks_bp.route('/tasks/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT status FROM tasks WHERE id = %s AND user_id = %s', (task_id, session['id']))
    task = cursor.fetchone()

    if task:
        if task['status'] != 'feito':
            new_status = 'feito'
            completed_at = datetime.now()
        else:
            new_status = 'a_fazer'
            completed_at = None

        cursor.execute(
            'UPDATE tasks SET status = %s, completed_at = %s WHERE id = %s AND user_id = %s',
            (new_status, completed_at, task_id, session['id'])
        )
        conn.commit()

    conn.close()
    return redirect(url_for('tasks.list'))
