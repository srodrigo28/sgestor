from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from common.database import get_db_connection
from apps.auth.views import login_required
from datetime import datetime, date
import json


financial_bp = Blueprint(
    'financial',
    __name__,
    template_folder='../../templates/financial',
    url_prefix='/financial'
)

FINANCIAL_CATEGORY_DEFAULTS = {
    'income': [
        {'name': 'serviço', 'icon': '🛠️', 'color': '#8b5cf6'},
        {'name': 'contrato', 'icon': '📄', 'color': '#3b82f6'},
        {'name': 'salário mensal', 'icon': '💼', 'color': '#22c55e'},
        {'name': 'bico', 'icon': '⚡', 'color': '#eab308'},
    ],
    'expense': [
        {'name': 'Operacional', 'icon': '🏭', 'color': '#f97316'},
        {'name': 'Fornecedores', 'icon': '📦', 'color': '#3b82f6'},
        {'name': 'Pessoal', 'icon': '👥', 'color': '#a855f7'},
        {'name': 'Outros', 'icon': '🧾', 'color': '#6b7280'},
    ],
}


def _normalize_name(value):
    return ' '.join(str(value or '').strip().split())


def _resolve_month_window(raw_value=None):
    today = date.today()
    default_value = f"{today.year:04d}-{today.month:02d}"
    selected = (raw_value or default_value).strip()
    try:
        start_month = datetime.strptime(selected, '%Y-%m').date()
    except ValueError:
        selected = default_value
        start_month = datetime.strptime(selected, '%Y-%m').date()

    if start_month.month == 12:
        end_month = date(start_month.year + 1, 1, 1)
    else:
        end_month = date(start_month.year, start_month.month + 1, 1)
    return selected, start_month, end_month


def _month_options():
    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    options = []
    base = date.today().replace(day=1)
    base_total = base.year * 12 + (base.month - 1)
    for i in range(5, -1, -1):
        total = base_total - i
        year = total // 12
        month = total % 12 + 1
        value = f"{year:04d}-{month:02d}"
        label = f"{months_pt[month]}/{str(year)[-2:]}"
        options.append({'value': value, 'label': label})
    return options


def _ensure_financial_category_schema(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS financial_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            kind ENUM('income', 'expense') NOT NULL,
            name VARCHAR(80) NOT NULL,
            icon VARCHAR(20) DEFAULT '🏷️',
            color VARCHAR(20) DEFAULT '#6b7280',
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_financial_categories_user_kind_name (user_id, kind, name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    try:
        cursor.execute("ALTER TABLE financial_income MODIFY COLUMN category VARCHAR(80) NOT NULL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE financial_expenses MODIFY COLUMN category VARCHAR(80) NOT NULL")
    except Exception:
        pass


def _seed_financial_categories(cursor, user_id, kind):
    defaults = FINANCIAL_CATEGORY_DEFAULTS[kind]
    for item in defaults:
        cursor.execute(
            "INSERT IGNORE INTO financial_categories (user_id, kind, name, icon, color) VALUES (%s, %s, %s, %s, %s)",
            (user_id, kind, item['name'], item['icon'], item['color'])
        )


def _sync_legacy_financial_categories(cursor, user_id, kind):
    table = 'financial_income' if kind == 'income' else 'financial_expenses'
    cursor.execute(
        f"SELECT DISTINCT category FROM {table} WHERE user_id = %s AND category IS NOT NULL AND TRIM(category) <> ''",
        (user_id,)
    )
    existing_rows = cursor.fetchall()
    for row in existing_rows:
        name = _normalize_name(row.get('category'))
        if not name:
            continue
        default = next((item for item in FINANCIAL_CATEGORY_DEFAULTS[kind] if item['name'].casefold() == name.casefold()), None)
        icon = default['icon'] if default else '🏷️'
        color = default['color'] if default else '#6b7280'
        cursor.execute(
            "INSERT IGNORE INTO financial_categories (user_id, kind, name, icon, color) VALUES (%s, %s, %s, %s, %s)",
            (user_id, kind, name, icon, color)
        )


def _ensure_financial_categories_ready(cursor, user_id, kind):
    _ensure_financial_category_schema(cursor)
    cursor.execute("SELECT COUNT(*) AS total FROM financial_categories WHERE user_id = %s AND kind = %s", (user_id, kind))
    total = int((cursor.fetchone() or {}).get('total') or 0)
    if total == 0:
        _seed_financial_categories(cursor, user_id, kind)
    _sync_legacy_financial_categories(cursor, user_id, kind)


def _fetch_financial_categories(cursor, user_id, kind):
    _ensure_financial_categories_ready(cursor, user_id, kind)
    table = 'financial_income' if kind == 'income' else 'financial_expenses'
    cursor.execute(
        f"""
        SELECT fc.*, COUNT(f.id) AS usage_count
        FROM financial_categories fc
        LEFT JOIN {table} f
          ON f.user_id = fc.user_id
         AND f.category = fc.name
        WHERE fc.user_id = %s AND fc.kind = %s AND fc.is_active = 1
        GROUP BY fc.id, fc.user_id, fc.kind, fc.name, fc.icon, fc.color, fc.is_active, fc.created_at, fc.updated_at
        ORDER BY fc.name ASC
        """,
        (user_id, kind)
    )
    rows = cursor.fetchall()
    for row in rows:
        row['usage_count'] = int(row.get('usage_count') or 0)
    return rows


def _resolve_financial_category(cursor, user_id, kind, category_id=None, category_name=None):
    _ensure_financial_categories_ready(cursor, user_id, kind)
    if category_id:
        cursor.execute(
            "SELECT * FROM financial_categories WHERE id = %s AND user_id = %s AND kind = %s AND is_active = 1",
            (category_id, user_id, kind)
        )
        row = cursor.fetchone()
        if row:
            return row
    name = _normalize_name(category_name)
    if name:
        cursor.execute(
            "SELECT * FROM financial_categories WHERE user_id = %s AND kind = %s AND name = %s AND is_active = 1",
            (user_id, kind, name)
        )
        row = cursor.fetchone()
        if row:
            return row
    cursor.execute(
        "SELECT * FROM financial_categories WHERE user_id = %s AND kind = %s AND is_active = 1 ORDER BY name ASC LIMIT 1",
        (user_id, kind)
    )
    return cursor.fetchone()


def _attach_category_meta(records, categories_by_name):
    for record in records:
        meta = categories_by_name.get(_normalize_name(record.get('category')).casefold())
        record['category_id'] = meta['id'] if meta else ''
        record['category_icon'] = meta['icon'] if meta else '🏷️'
        record['category_color'] = meta['color'] if meta else '#6b7280'


def _income_stats(cursor, user_id, start_month=None, end_month=None):
    where = ["user_id = %s"]
    params = [user_id]
    if start_month and end_month:
        where.append("entry_date >= %s AND entry_date < %s")
        params.extend([start_month, end_month])
    where_sql = " AND ".join(where)
    cursor.execute(f"""
        SELECT 
            COALESCE(SUM(amount), 0) as total_month,
            COALESCE(SUM(CASE WHEN status = 'received' THEN amount ELSE 0 END), 0) as received_month,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as pending_month
        FROM financial_income 
        WHERE {where_sql}
    """, tuple(params))
    stats_data = cursor.fetchone() or {}
    total_month = float(stats_data.get('total_month') or 0)
    if start_month and end_month:
        today = date.today()
        if start_month.year == today.year and start_month.month == today.month:
            divisor = max(today.day, 1)
        else:
            divisor = max((end_month - start_month).days, 1)
    else:
        divisor = max(date.today().day, 1)
    return {
        'total_month': total_month,
        'received_month': float(stats_data.get('received_month') or 0),
        'pending_month': float(stats_data.get('pending_month') or 0),
        'avg_daily_month': total_month / divisor,
    }


def _income_charts(cursor, user_id, category_name='', status_filter='', month_filter='all'):
    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    params = [user_id]
    where = "user_id = %s"
    if status_filter:
        where += " AND status = %s"
        params.append(status_filter)
    if category_name:
        where += " AND category = %s"
        params.append(category_name)

    if month_filter and month_filter != 'all':
        try:
            start_month = datetime.strptime(month_filter, '%Y-%m').date()
        except ValueError:
            start_month = None
        if start_month:
            end_month = date(start_month.year + 1, 1, 1) if start_month.month == 12 else date(start_month.year, start_month.month + 1, 1)
            chart_history_query = f"SELECT DATE(entry_date) as date, SUM(amount) as total FROM financial_income WHERE {where} AND entry_date >= %s AND entry_date < %s GROUP BY DATE(entry_date) ORDER BY date ASC"
            history_params = params + [start_month, end_month]
            cursor.execute(chart_history_query, tuple(history_params))
            rows = cursor.fetchall()
            totals_map = {str(row['date']): float(row['total'] or 0) for row in rows}
            history = {'labels': [], 'values': []}
            for day in range(1, (end_month - start_month).days + 1):
                current = date(start_month.year, start_month.month, day)
                history['labels'].append(current.strftime('%d/%m'))
                history['values'].append(totals_map.get(str(current), 0.0))
            category_query = f"SELECT category, SUM(amount) as total FROM financial_income WHERE {where} AND entry_date >= %s AND entry_date < %s GROUP BY category"
            category_params = params + [start_month, end_month]
        else:
            history = {'labels': [], 'values': []}
            category_query = f"SELECT category, SUM(amount) as total FROM financial_income WHERE {where} GROUP BY category"
            category_params = params
    else:
        chart_history_query = f"SELECT DATE_FORMAT(entry_date, '%Y-%m') as month_year, SUM(amount) as total FROM financial_income WHERE {where} AND entry_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) GROUP BY DATE_FORMAT(entry_date, '%Y-%m') ORDER BY month_year ASC"
        cursor.execute(chart_history_query, tuple(params))
        rows = cursor.fetchall()
        totals_map = {row['month_year']: float(row['total'] or 0) for row in rows}
        history = {'labels': [], 'values': []}
        base = date.today().replace(day=1)
        base_total = base.year * 12 + (base.month - 1)
        for i in range(5, -1, -1):
            total = base_total - i
            year = total // 12
            month = total % 12 + 1
            key = f"{year:04d}-{month:02d}"
            history['labels'].append(f"{months_pt[month]}/{str(year)[-2:]}")
            history['values'].append(totals_map.get(key, 0.0))
        category_query = f"SELECT category, SUM(amount) as total FROM financial_income WHERE {where} AND entry_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY category"
        category_params = params

    cursor.execute(category_query, tuple(category_params))
    category_rows = cursor.fetchall()
    category_chart = {'labels': [], 'values': []}
    for row in category_rows:
        category_chart['labels'].append(str(row['category'] or 'Sem Categoria').title())
        category_chart['values'].append(float(row['total'] or 0))
    return history, category_chart


def _expense_stats(cursor, user_id, start_month=None, end_month=None):
    where = ["user_id = %s"]
    params = [user_id]
    if start_month and end_month:
        where.append("due_date >= %s AND due_date < %s")
        params.extend([start_month, end_month])
    where_sql = " AND ".join(where)
    cursor.execute(f"""
        SELECT 
            COALESCE(SUM(amount), 0) as total_month,
            COALESCE(SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END), 0) as paid_month,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as pending_month
        FROM financial_expenses 
        WHERE {where_sql}
    """, tuple(params))
    stats_data = cursor.fetchone() or {}
    total_month = float(stats_data.get('total_month') or 0)
    if start_month and end_month:
        today = date.today()
        if start_month.year == today.year and start_month.month == today.month:
            divisor = max(today.day, 1)
        else:
            divisor = max((end_month - start_month).days, 1)
    else:
        divisor = max(date.today().day, 1)
    return {
        'total_month': total_month,
        'paid_month': float(stats_data.get('paid_month') or 0),
        'pending_month': float(stats_data.get('pending_month') or 0),
        'avg_daily_month': total_month / divisor,
    }



def _expense_charts(cursor, user_id, category_name='', status_filter='', month_filter='all'):
    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    params = [user_id]
    where = "user_id = %s"
    if status_filter:
        where += " AND status = %s"
        params.append(status_filter)
    if category_name:
        where += " AND category = %s"
        params.append(category_name)

    if month_filter and month_filter != 'all':
        try:
            start_month = datetime.strptime(month_filter, '%Y-%m').date()
        except ValueError:
            start_month = None
        if start_month:
            end_month = date(start_month.year + 1, 1, 1) if start_month.month == 12 else date(start_month.year, start_month.month + 1, 1)
            chart_history_query = f"SELECT DATE(due_date) as date, SUM(amount) as total FROM financial_expenses WHERE {where} AND due_date >= %s AND due_date < %s GROUP BY DATE(due_date) ORDER BY date ASC"
            history_params = params + [start_month, end_month]
            cursor.execute(chart_history_query, tuple(history_params))
            rows = cursor.fetchall()
            totals_map = {str(row['date']): float(row['total'] or 0) for row in rows}
            history = {'labels': [], 'values': []}
            for day in range(1, (end_month - start_month).days + 1):
                current = date(start_month.year, start_month.month, day)
                history['labels'].append(current.strftime('%d/%m'))
                history['values'].append(totals_map.get(str(current), 0.0))
            category_query = f"SELECT category, SUM(amount) as total FROM financial_expenses WHERE {where} AND due_date >= %s AND due_date < %s GROUP BY category"
            category_params = params + [start_month, end_month]
        else:
            history = {'labels': [], 'values': []}
            category_query = f"SELECT category, SUM(amount) as total FROM financial_expenses WHERE {where} GROUP BY category"
            category_params = params
    else:
        chart_history_query = f"SELECT DATE_FORMAT(due_date, '%Y-%m') as month_year, SUM(amount) as total FROM financial_expenses WHERE {where} AND due_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) GROUP BY DATE_FORMAT(due_date, '%Y-%m') ORDER BY month_year ASC"
        cursor.execute(chart_history_query, tuple(params))
        rows = cursor.fetchall()
        totals_map = {row['month_year']: float(row['total'] or 0) for row in rows}
        history = {'labels': [], 'values': []}
        base = date.today().replace(day=1)
        base_total = base.year * 12 + (base.month - 1)
        for i in range(5, -1, -1):
            total = base_total - i
            year = total // 12
            month = total % 12 + 1
            key = f"{year:04d}-{month:02d}"
            history['labels'].append(f"{months_pt[month]}/{str(year)[-2:]}")
            history['values'].append(totals_map.get(key, 0.0))
        category_query = f"SELECT category, SUM(amount) as total FROM financial_expenses WHERE {where} AND due_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY category"
        category_params = params

    cursor.execute(category_query, tuple(category_params))
    category_rows = cursor.fetchall()
    category_chart = {'labels': [], 'values': []}
    for row in category_rows:
        category_chart['labels'].append(str(row['category'] or 'Sem Categoria').title())
        category_chart['values'].append(float(row['total'] or 0))
    return history, category_chart




@financial_bp.route('/income')
@login_required
def income_list():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    selected_month, start_month, end_month = _resolve_month_window(request.args.get('month'))
    user_id = session['id']
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    income_categories = _fetch_financial_categories(cursor, user_id, 'income')
    income_categories_by_name = {cat['name'].casefold(): cat for cat in income_categories}
    selected_category = _resolve_financial_category(cursor, user_id, 'income', category_id=category_filter, category_name=category_filter) if category_filter else None
    selected_category_name = selected_category['name'] if selected_category and category_filter else ''
    active_category_filter = str(selected_category['id']) if selected_category and category_filter else ''

    query = "SELECT * FROM financial_income WHERE user_id = %s AND entry_date >= %s AND entry_date < %s"
    params = [user_id, start_month, end_month]
    if search_query:
        term = f"%{search_query}%"
        query += " AND (description LIKE %s OR category LIKE %s OR CAST(amount AS CHAR) LIKE %s)"
        params.extend([term, term, term])
    if selected_category_name:
        query += " AND category = %s"
        params.append(selected_category_name)
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)

    count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
    cursor.execute(count_query, tuple(params))
    total_records = int((cursor.fetchone() or {}).get('total') or 0)
    total_pages = (total_records + per_page - 1) // per_page if total_records else 1

    stats = _income_stats(cursor, user_id, start_month, end_month)

    query += " ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    cursor.execute(query, tuple(params + [per_page, offset]))
    incomes = cursor.fetchall()
    _attach_category_meta(incomes, income_categories_by_name)

    chart_history, chart_category = _income_charts(cursor, user_id, selected_category_name, status_filter, selected_month)

    cursor.close()
    conn.close()

    return render_template(
        'income.html',
        incomes=incomes,
        page=page,
        total_pages=total_pages,
        search=search_query,
        stats=stats,
        category_filter=active_category_filter,
        status_filter=status_filter,
        today=date.today(),
        chart_history_json=json.dumps(chart_history),
        chart_category_json=json.dumps(chart_category),
        month_options=_month_options(),
        selected_month=selected_month,
        income_categories=income_categories,
        selected_month_label=next((opt['label'] for opt in _month_options() if opt['value'] == selected_month), selected_month),
    )


@financial_bp.route('/charts')
@login_required
def charts():
    category_filter = request.args.get('category', '')
    month_filter = request.args.get('month', 'all')
    status_filter = request.args.get('status', '')
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    selected_category = _resolve_financial_category(cursor, user_id, 'income', category_id=category_filter, category_name=category_filter) if category_filter else None
    selected_category_name = selected_category['name'] if selected_category and category_filter else ''
    chart_history, chart_category = _income_charts(cursor, user_id, selected_category_name, status_filter, month_filter)
    cursor.close()
    conn.close()
    return jsonify({'history': chart_history, 'category': chart_category})


@financial_bp.route('/expenses/charts')
@login_required
def expense_charts():
    month_filter = request.args.get('month', 'all')
    status_filter = request.args.get('status', '')
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    chart_history, chart_category = _expense_charts(cursor, user_id, '', status_filter, month_filter)
    cursor.close()
    conn.close()
    return jsonify({'history': chart_history, 'category': chart_category})


@financial_bp.route('/income/add', methods=['POST'])
@login_required
def add_income():
    description = request.form['description']
    amount = request.form['amount']
    payment_type = request.form['payment_type']
    entry_date = request.form['entry_date']
    status = request.form.get('status', 'received')
    user_id = session['id']

    if not description or not amount or not entry_date:
        flash('Preencha os campos de descrição, valor e data.', 'error')
        return redirect(url_for('financial.income_list'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        category = _resolve_financial_category(cursor, user_id, 'income', category_id=request.form.get('category_id'), category_name=request.form.get('category'))
        if not category:
            flash('Categoria de entrada inválida.', 'error')
            return redirect(url_for('financial.income_list'))
        received_date = entry_date if status == 'received' else None
        query = """
            INSERT INTO financial_income (user_id, description, amount, category, payment_type, entry_date, status, received_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, description, amount, category['name'], payment_type, entry_date, status, received_date))
        conn.commit()
        flash('Entrada registrada com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao salvar: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.income_list'))


@financial_bp.route('/income/delete/<int:id>', methods=['POST'])
@login_required
def delete_income(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM financial_income WHERE id = %s AND user_id = %s", (id, session['id']))
        if cursor.rowcount == 0:
            flash('Registro não encontrado ou sem permissão.', 'error')
        else:
            conn.commit()
            flash('Registro removido com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao remover: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.income_list'))


@financial_bp.route('/income/update/<int:id>', methods=['POST'])
@login_required
def update_income(id):
    description = request.form['description']
    amount = request.form['amount']
    payment_type = request.form['payment_type']
    entry_date = request.form['entry_date']
    status = request.form.get('status', 'received')
    user_id = session['id']

    if not description or not amount or not entry_date:
        flash('Preencha os campos de descrição, valor e data.', 'error')
        return redirect(url_for('financial.income_list'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM financial_income WHERE id=%s AND user_id=%s", (id, user_id))
        if not cursor.fetchone():
            flash('Registro não encontrado ou sem permissão.', 'error')
            return redirect(url_for('financial.income_list'))

        category = _resolve_financial_category(cursor, user_id, 'income', category_id=request.form.get('category_id'), category_name=request.form.get('category'))
        if not category:
            flash('Categoria de entrada inválida.', 'error')
            return redirect(url_for('financial.income_list'))

        received_date = entry_date if status == 'received' else None
        update_query = """
            UPDATE financial_income
            SET description=%s, amount=%s, category=%s, payment_type=%s, entry_date=%s, status=%s, received_date=%s
            WHERE id=%s AND user_id=%s
        """
        cursor.execute(update_query, (description, amount, category['name'], payment_type, entry_date, status, received_date, id, user_id))
        conn.commit()
        flash('Entrada atualizada com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao salvar: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.income_list'))


@financial_bp.route('/expenses')
@login_required
def expenses_list():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    selected_month, start_month, end_month = _resolve_month_window(request.args.get('month'))
    user_id = session['id']
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    expense_categories = _fetch_financial_categories(cursor, user_id, 'expense')
    expense_categories_by_name = {cat['name'].casefold(): cat for cat in expense_categories}

    query = "SELECT * FROM financial_expenses WHERE user_id = %s AND due_date >= %s AND due_date < %s"
    params = [user_id, start_month, end_month]
    if search_query:
        term = f"%{search_query}%"
        query += " AND (description LIKE %s OR category LIKE %s OR CAST(amount AS CHAR) LIKE %s)"
        params.extend([term, term, term])
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)

    count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
    cursor.execute(count_query, tuple(params))
    total_records = int((cursor.fetchone() or {}).get('total') or 0)
    total_pages = (total_records + per_page - 1) // per_page if total_records else 1

    stats = _expense_stats(cursor, user_id, start_month, end_month)

    query += " ORDER BY due_date ASC, id DESC LIMIT %s OFFSET %s"
    cursor.execute(query, tuple(params + [per_page, offset]))
    expenses = cursor.fetchall()
    _attach_category_meta(expenses, expense_categories_by_name)

    chart_history, chart_category = _expense_charts(cursor, user_id, '', status_filter, selected_month)

    cursor.close()
    conn.close()

    return render_template(
        'financial/expenses.html',
        expenses=expenses,
        page=page,
        total_pages=total_pages,
        search=search_query,
        stats=stats,
        today=date.today(),
        expense_categories=expense_categories,
        status_filter=status_filter,
        selected_month=selected_month,
        month_options=_month_options(),
        chart_history_json=json.dumps(chart_history),
        chart_category_json=json.dumps(chart_category),
        selected_month_label=next((opt['label'] for opt in _month_options() if opt['value'] == selected_month), selected_month),
    )


@financial_bp.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    description = request.form['description']
    amount = request.form['amount']
    payment_type = request.form['payment_type']
    due_date = request.form['due_date']
    status = request.form.get('status', 'pending')
    user_id = session['id']

    if not description or not amount or not due_date:
        flash('Preencha os campos de descrição, valor e data.', 'error')
        return redirect(url_for('financial.expenses_list'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        category = _resolve_financial_category(cursor, user_id, 'expense', category_id=request.form.get('category_id'), category_name=request.form.get('category'))
        if not category:
            flash('Categoria de despesa inválida.', 'error')
            return redirect(url_for('financial.expenses_list'))
        paid_date = due_date if status == 'paid' else None
        query = "INSERT INTO financial_expenses (user_id, description, amount, category, payment_type, due_date, status, paid_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (user_id, description, amount, category['name'], payment_type, due_date, status, paid_date))
        conn.commit()
        flash('Despesa registrada com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao salvar: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.expenses_list'))


@financial_bp.route('/expenses/update/<int:id>', methods=['POST'])
@login_required
def update_expense(id):
    description = request.form['description']
    amount = request.form['amount']
    payment_type = request.form['payment_type']
    due_date = request.form['due_date']
    status = request.form.get('status', 'pending')
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        category = _resolve_financial_category(cursor, user_id, 'expense', category_id=request.form.get('category_id'), category_name=request.form.get('category'))
        if not category:
            flash('Categoria de despesa inválida.', 'error')
            return redirect(url_for('financial.expenses_list'))
        paid_date = due_date if status == 'paid' else None
        query = "UPDATE financial_expenses SET description=%s, amount=%s, category=%s, payment_type=%s, due_date=%s, status=%s, paid_date=%s WHERE id=%s AND user_id=%s"
        cursor.execute(query, (description, amount, category['name'], payment_type, due_date, status, paid_date, id, user_id))
        conn.commit()
        flash('Despesa atualizada com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao salvar: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.expenses_list'))


@financial_bp.route('/expenses/delete/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM financial_expenses WHERE id=%s AND user_id=%s", (id, session['id']))
        conn.commit()
        flash('Despesa removida com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao salvar: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.expenses_list'))


@financial_bp.route('/categories/<kind>/add', methods=['POST'])
@login_required
def add_category(kind):
    if kind not in {'income', 'expense'}:
        return redirect(url_for('financial.income_list'))
    user_id = session['id']
    name = _normalize_name(request.form.get('name'))
    icon = (request.form.get('icon') or '🏷️').strip()[:10] or '🏷️'
    color = (request.form.get('color') or '#6b7280').strip() or '#6b7280'
    if not name:
        flash('Informe o nome da categoria.', 'error')
        return redirect(url_for('financial.income_list' if kind == 'income' else 'financial.expenses_list'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        _ensure_financial_categories_ready(cursor, user_id, kind)
        cursor.execute('SELECT id FROM financial_categories WHERE user_id = %s AND kind = %s AND name = %s', (user_id, kind, name))
        if cursor.fetchone():
            flash('Já existe uma categoria com esse nome.', 'error')
        else:
            cursor.execute('INSERT INTO financial_categories (user_id, kind, name, icon, color) VALUES (%s, %s, %s, %s, %s)', (user_id, kind, name, icon, color))
            conn.commit()
            flash('Categoria criada com sucesso!', 'success')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.income_list' if kind == 'income' else 'financial.expenses_list'))


@financial_bp.route('/categories/<kind>/edit/<int:category_id>', methods=['POST'])
@login_required
def edit_category(kind, category_id):
    if kind not in {'income', 'expense'}:
        return redirect(url_for('financial.income_list'))
    user_id = session['id']
    name = _normalize_name(request.form.get('name'))
    icon = (request.form.get('icon') or '🏷️').strip()[:10] or '🏷️'
    color = (request.form.get('color') or '#6b7280').strip() or '#6b7280'

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        _ensure_financial_categories_ready(cursor, user_id, kind)
        cursor.execute('SELECT * FROM financial_categories WHERE id = %s AND user_id = %s AND kind = %s', (category_id, user_id, kind))
        category = cursor.fetchone()
        if not category:
            flash('Categoria não encontrada.', 'error')
            return redirect(url_for('financial.income_list' if kind == 'income' else 'financial.expenses_list'))

        cursor.execute('SELECT id FROM financial_categories WHERE user_id = %s AND kind = %s AND name = %s AND id <> %s', (user_id, kind, name, category_id))
        if cursor.fetchone():
            flash('Já existe outra categoria com esse nome.', 'error')
            return redirect(url_for('financial.income_list' if kind == 'income' else 'financial.expenses_list'))

        old_name = category['name']
        table = 'financial_income' if kind == 'income' else 'financial_expenses'
        cursor.execute('UPDATE financial_categories SET name = %s, icon = %s, color = %s WHERE id = %s AND user_id = %s AND kind = %s', (name, icon, color, category_id, user_id, kind))
        if old_name != name:
            cursor.execute(f'UPDATE {table} SET category = %s WHERE user_id = %s AND category = %s', (name, user_id, old_name))
        conn.commit()
        flash('Categoria atualizada com sucesso!', 'success')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.income_list' if kind == 'income' else 'financial.expenses_list'))


@financial_bp.route('/categories/<kind>/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(kind, category_id):
    if kind not in {'income', 'expense'}:
        return redirect(url_for('financial.income_list'))
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        _ensure_financial_categories_ready(cursor, user_id, kind)
        cursor.execute('SELECT * FROM financial_categories WHERE id = %s AND user_id = %s AND kind = %s', (category_id, user_id, kind))
        category = cursor.fetchone()
        if not category:
            flash('Categoria não encontrada.', 'error')
            return redirect(url_for('financial.income_list' if kind == 'income' else 'financial.expenses_list'))

        cursor.execute('SELECT COUNT(*) AS total FROM financial_categories WHERE user_id = %s AND kind = %s AND is_active = 1', (user_id, kind))
        total_categories = int((cursor.fetchone() or {}).get('total') or 0)
        table = 'financial_income' if kind == 'income' else 'financial_expenses'
        cursor.execute(f'SELECT COUNT(*) AS total FROM {table} WHERE user_id = %s AND category = %s', (user_id, category['name']))
        usage_count = int((cursor.fetchone() or {}).get('total') or 0)
        if total_categories <= 1:
            flash('Mantenha pelo menos uma categoria ativa.', 'error')
        elif usage_count > 0:
            flash('Categoria em uso. Reclassifique os lançamentos antes de excluir.', 'error')
        else:
            cursor.execute('DELETE FROM financial_categories WHERE id = %s AND user_id = %s AND kind = %s', (category_id, user_id, kind))
            conn.commit()
            flash('Categoria removida com sucesso!', 'success')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.income_list' if kind == 'income' else 'financial.expenses_list'))
