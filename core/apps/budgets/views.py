from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
from datetime import datetime, timedelta, date
from common.database import get_db_connection
from common.employees_schema import ensure_employees_schema

def adjust_stock(cursor, budget_id, user_id, reverse=False):
    """
    Updates stock for products linked to a budget.
    reverse=False -> Deduct from stock (Approval)
    reverse=True -> Add back to stock (Rejection/Cancellation)
    """
    cursor.execute("""
        SELECT product_id, quantity 
        FROM budget_items 
        WHERE budget_id = %s AND product_id IS NOT NULL
    """, (budget_id,))
    items = cursor.fetchall()
    
    for item in items:
        qty = float(item['quantity'])
        if reverse:
            cursor.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s AND user_id = %s", (qty, item['product_id'], user_id))
        else:
            cursor.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s AND user_id = %s", (qty, item['product_id'], user_id))

budgets_bp = Blueprint('budgets', __name__)


def _resolve_month_window(raw_value=None):
    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    today = date.today()
    default_value = f"{today.year:04d}-{today.month:02d}"
    selected = (raw_value or default_value).strip()
    try:
        start_month = datetime.strptime(selected, '%Y-%m').date()
    except ValueError:
        selected = default_value
        start_month = datetime.strptime(selected, '%Y-%m').date()

    if start_month.year != today.year or start_month.month > today.month:
        selected = default_value
        start_month = datetime.strptime(selected, '%Y-%m').date()

    if start_month.month == 12:
        end_month = date(start_month.year + 1, 1, 1)
    else:
        end_month = date(start_month.year, start_month.month + 1, 1)

    month_options = []
    for m in range(1, today.month + 1):
        value = f"{today.year:04d}-{m:02d}"
        label = f"{months_pt[m]}/{str(today.year)[-2:]}"
        month_options.append({'value': value, 'label': label})

    return selected, start_month, end_month, month_options


def _resolve_budget_datetime(raw_value, fallback=None):
    value = (str(raw_value or '')).strip()
    if not value:
        return fallback
    try:
        base_date = datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return fallback

    if fallback:
        base_time = fallback.time().replace(microsecond=0)
    else:
        base_time = datetime.now().time().replace(microsecond=0)

    return datetime.combine(base_date, base_time)


def _parse_client_id(raw_value):
    value = str(raw_value or '').strip()
    if not value or value.lower() in {'null', 'none', 'undefined'}:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _resolve_selected_client(cursor, user_id, raw_client_id, raw_client_name):
    client_id = _parse_client_id(raw_client_id)
    client_name = (raw_client_name or '').strip()

    if client_id:
        cursor.execute("SELECT id, name FROM clients WHERE id = %s AND user_id = %s", (client_id, user_id))
        client = cursor.fetchone()
        if client:
            return client, None
        return None, 'O cliente selecionado não foi encontrado.'

    if not client_name:
        return None, 'Selecione um cliente cadastrado antes de salvar o orçamento.'

    cursor.execute("SELECT id, name FROM clients WHERE user_id = %s AND name = %s ORDER BY id DESC", (user_id, client_name))
    matches = cursor.fetchall()
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, 'Há mais de um cliente com esse nome. Selecione o cliente pela lista.'
    return None, 'Selecione um cliente já cadastrado. O orçamento não cria cliente automaticamente.'


def _validate_product_stock(cursor, user_id, items):
    for index, item in enumerate(items, start=1):
        product_id = item.get('product_id')
        if not product_id or item.get('is_service'):
            continue

        cursor.execute("SELECT name, quantity FROM products WHERE id = %s AND user_id = %s", (product_id, user_id))
        product = cursor.fetchone()
        if not product:
            return f'O produto do item {index} não foi encontrado.'

        available = float(product.get('quantity') or 0)
        requested = float(item.get('qty') or 0)
        if requested > available:
            return f"Estoque insuficiente para '{product.get('name')}'. Disponível: {available:g}."

    return None


def _normalize_budget_items(items):
    normalized_items = []
    for index, item in enumerate(items or [], start=1):
        desc = (item.get('desc') or '').strip()
        try:
            qty = float(item.get('qty') or 0)
        except (TypeError, ValueError):
            qty = 0
        try:
            price = float(item.get('price') or 0)
        except (TypeError, ValueError):
            price = 0

        if not desc:
            return None, f'Informe a descrição do item {index}.'
        if qty <= 0:
            return None, f'Informe uma quantidade válida para o item {index}.'
        if price <= 0:
            return None, f'Informe um valor unitário válido para o item {index}.'

        product_id = item.get('product_id')
        if not product_id or str(product_id).lower() in ['null', 'undefined', '']:
            product_id = None

        normalized_items.append({
            'desc': desc,
            'qty': qty,
            'price': price,
            'total': float(item.get('total') or (qty * price)),
            'product_id': product_id,
            'is_service': bool(item.get('is_service')),
            'is_takeaway': bool(item.get('is_takeaway')),
        })

    return normalized_items, None


def _resolve_status_transition(current_approval, current_stage, requested_approval, requested_stage):
    allowed_approval = {'sent', 'approved', 'rejected'}
    allowed_stage = {'budget', 'ready_for_pickup', 'delivered'}

    approval_status = requested_approval if requested_approval in allowed_approval else (current_approval or 'sent')
    stage_status = requested_stage if requested_stage in allowed_stage else (current_stage or 'budget')

    if approval_status == 'sent' and stage_status == 'delivered':
        return None, None, 'Defina Aprovado/Reprovado antes de marcar Entregue.'

    if stage_status == 'delivered' and current_stage not in {'ready_for_pickup', 'delivered'}:
        return None, None, 'Marque Retirada antes de marcar Entregue.'

    return approval_status, stage_status, None


def _build_status_update_fields(approval_status, stage_status, now):
    fields = [
        "status = %s",
        "approval_status = %s",
        "stage_status = %s",
        "approved_at = %s",
        "rejected_at = %s",
        "ready_for_pickup_at = %s",
        "delivered_at = %s",
    ]
    params = [
        approval_status,
        approval_status,
        stage_status,
        now if approval_status == 'approved' else None,
        now if approval_status == 'rejected' else None,
        now if stage_status in {'ready_for_pickup', 'delivered'} else None,
        now if stage_status == 'delivered' else None,
    ]
    return fields, params

@budgets_bp.route('/budgets')
def list():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    search = request.args.get('search', '').strip()
    approval_filter = (request.args.get('approval') or 'all').strip().lower()
    if approval_filter not in {'all', 'approved', 'sent'}:
        approval_filter = 'all'

    selected_month, start_month, end_month, month_options = _resolve_month_window(request.args.get('month'))
    month_label = next((opt['label'] for opt in month_options if opt['value'] == selected_month), selected_month)

    query = """
        SELECT b.*, c.name as client_name, v.plate, v.model as vehicle_model
        FROM budgets b
        JOIN clients c ON b.client_id = c.id
        LEFT JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.user_id = %s
          AND b.created_at >= %s
          AND b.created_at < %s
    """
    params = [user_id, start_month, end_month]

    if approval_filter != 'all':
        query += " AND COALESCE(b.approval_status, b.status) = %s"
        params.append(approval_filter)

    if search:
        query += " AND c.name LIKE %s"
        term = f"%{search}%"
        params.append(term)

    query += " ORDER BY b.created_at DESC"
    cursor.execute(query, tuple(params))
    budgets = cursor.fetchall()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN COALESCE(approval_status, status) = 'approved' THEN total_value ELSE 0 END) as approved_value,
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as month_count
        FROM budgets
        WHERE user_id = %s
    """, (user_id,))
    stats_data = cursor.fetchone()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_month,
            SUM(CASE WHEN COALESCE(approval_status, status) = 'approved' THEN 1 ELSE 0 END) AS approved_count,
            SUM(CASE WHEN COALESCE(approval_status, status) = 'sent' THEN 1 ELSE 0 END) AS waiting_count
        FROM budgets
        WHERE user_id = %s AND created_at >= %s AND created_at < %s
    """, (user_id, start_month, end_month))
    filter_counts = cursor.fetchone() or {}

    stats = {
        'total_budgets': stats_data['total_count'] or 0,
        'approved_value': float(stats_data['approved_value'] or 0),
        'month_count': stats_data['month_count'] or 0
    }

    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

    cursor.execute("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month_year, SUM(total_value) as total
        FROM budgets 
        WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY month_year ASC
    """, (user_id,))
    history_results = cursor.fetchall()
    totals_map = {row['month_year']: float(row['total'] or 0) for row in history_results}

    chart_weekly = {'labels': [], 'data': []}
    base = date.today().replace(day=1)
    base_total = base.year * 12 + (base.month - 1)
    for i in range(5, -1, -1):
        total = base_total - i
        y = total // 12
        m = total % 12 + 1
        key = f"{y:04d}-{m:02d}"
        label = f"{months_pt[m]}/{str(y)[-2:]}"
        chart_weekly['labels'].append(label)
        chart_weekly['data'].append(totals_map.get(key, 0))
    
    cursor.execute("""
        SELECT stage_status, COUNT(*) as count
        FROM budgets
        WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
        GROUP BY stage_status
        ORDER BY FIELD(stage_status, 'budget', 'ready_for_pickup', 'delivered')
    """, (user_id,))
    stage_data = cursor.fetchall()

    cursor.execute("""
        SELECT approval_status, COUNT(*) as count
        FROM budgets
        WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
        GROUP BY approval_status
        ORDER BY FIELD(approval_status, 'sent', 'approved', 'rejected')
    """, (user_id,))
    approval_data = cursor.fetchall()

    stage_map = {
        'budget': 'Orçamento',
        'ready_for_pickup': 'Retirada',
        'delivered': 'Entregue',
    }
    stage_colors = {
        'budget': '#6b7280',
        'ready_for_pickup': '#3b82f6',
        'delivered': '#14b8a6',
    }
    approval_map = {
        'sent': 'Aguardando',
        'approved': 'Aprovado',
        'rejected': 'Reprovado',
    }
    approval_colors = {
        'sent': '#eab308',
        'approved': '#10b981',
        'rejected': '#ef4444',
    }

    chart_stage = {
        'labels': [stage_map.get(row['stage_status'], row['stage_status']) for row in stage_data],
        'data': [row['count'] for row in stage_data],
        'colors': [stage_colors.get(row['stage_status'], '#6b7280') for row in stage_data]
    }
    chart_approval = {
        'labels': [approval_map.get(row['approval_status'], row['approval_status']) for row in approval_data],
        'data': [row['count'] for row in approval_data],
        'colors': [approval_colors.get(row['approval_status'], '#6b7280') for row in approval_data]
    }

    conn.close()
    
    return render_template('budgets/index.html', 
                         budgets=budgets, 
                         stats=stats, 
                         chart_weekly=json.dumps(chart_weekly),
                         chart_stage=json.dumps(chart_stage),
                         chart_approval=json.dumps(chart_approval),
                         month_options=month_options,
                         selected_month=selected_month,
                         approval_filter=approval_filter,
                         month_label=month_label,
                         filter_counts={
                             'total': int(filter_counts.get('total_month') or 0),
                             'approved': int(filter_counts.get('approved_count') or 0),
                             'waiting': int(filter_counts.get('waiting_count') or 0),
                         },
                         search=search,
                         active_page='budgets')

@budgets_bp.route('/budgets/charts')
def charts():
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401

    user_id = session['id']
    month_filter = request.args.get('month', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

    # History (Last 6 Months) or Daily for selected month
    if month_filter and month_filter != 'all':
        try:
            start_month = datetime.strptime(month_filter, '%Y-%m').date()
        except ValueError:
            start_month = None
        end_month = None
        if start_month:
            if start_month.month == 12:
                end_month = date(start_month.year + 1, 1, 1)
            else:
                end_month = date(start_month.year, start_month.month + 1, 1)

        chart_history = {'labels': [], 'data': []}
        if start_month and end_month:
            cursor.execute("""
                SELECT DATE(created_at) as date, SUM(total_value) as total
                FROM budgets
                WHERE user_id = %s AND created_at >= %s AND created_at < %s
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """, (user_id, start_month, end_month))
            results = cursor.fetchall()
            totals_map = {str(row['date']): float(row['total'] or 0) for row in results}
            days_in_month = (end_month - start_month).days
            for day in range(1, days_in_month + 1):
                d = date(start_month.year, start_month.month, day)
                chart_history['labels'].append(d.strftime('%d/%m'))
                chart_history['data'].append(totals_map.get(str(d), 0))
    else:
        cursor.execute("""
            SELECT DATE_FORMAT(created_at, '%Y-%m') as month_year, SUM(total_value) as total
            FROM budgets 
            WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month_year ASC
        """, (user_id,))
        results = cursor.fetchall()
        totals_map = {row['month_year']: float(row['total'] or 0) for row in results}
        chart_history = {'labels': [], 'data': []}
        base = date.today().replace(day=1)
        base_total = base.year * 12 + (base.month - 1)
        for i in range(5, -1, -1):
            total = base_total - i
            y = total // 12
            m = total % 12 + 1
            key = f"{y:04d}-{m:02d}"
            label = f"{months_pt[m]}/{str(y)[-2:]}"
            chart_history['labels'].append(label)
            chart_history['data'].append(totals_map.get(key, 0))

    # Stage + approval distributions (month filtered if selected)
    stage_query = """
        SELECT stage_status, COUNT(*) as count
        FROM budgets
        WHERE user_id = %s
    """
    stage_params = [user_id]
    if month_filter and month_filter != 'all' and start_month and end_month:
        stage_query += " AND created_at >= %s AND created_at < %s"
        stage_params.extend([start_month, end_month])
    else:
        stage_query += " AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)"
    stage_query += " GROUP BY stage_status ORDER BY FIELD(stage_status, 'budget', 'ready_for_pickup', 'delivered')"
    cursor.execute(stage_query, tuple(stage_params))
    stage_data = cursor.fetchall()

    approval_query = """
        SELECT approval_status, COUNT(*) as count
        FROM budgets
        WHERE user_id = %s
    """
    approval_params = [user_id]
    if month_filter and month_filter != 'all' and start_month and end_month:
        approval_query += " AND created_at >= %s AND created_at < %s"
        approval_params.extend([start_month, end_month])
    else:
        approval_query += " AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)"
    approval_query += " GROUP BY approval_status ORDER BY FIELD(approval_status, 'sent', 'approved', 'rejected')"
    cursor.execute(approval_query, tuple(approval_params))
    approval_data = cursor.fetchall()

    stage_map = {
        'budget': 'Orçamento',
        'ready_for_pickup': 'Retirada',
        'delivered': 'Entregue',
    }
    stage_colors = {
        'budget': '#6b7280',
        'ready_for_pickup': '#3b82f6',
        'delivered': '#14b8a6',
    }
    approval_map = {
        'sent': 'Aguardando',
        'approved': 'Aprovado',
        'rejected': 'Reprovado',
    }
    approval_colors = {
        'sent': '#eab308',
        'approved': '#10b981',
        'rejected': '#ef4444',
    }

    chart_stage = {
        'labels': [stage_map.get(row['stage_status'], row['stage_status']) for row in stage_data],
        'data': [row['count'] for row in stage_data],
        'colors': [stage_colors.get(row['stage_status'], '#6b7280') for row in stage_data]
    }
    chart_approval = {
        'labels': [approval_map.get(row['approval_status'], row['approval_status']) for row in approval_data],
        'data': [row['count'] for row in approval_data],
        'colors': [approval_colors.get(row['approval_status'], '#6b7280') for row in approval_data]
    }

    conn.close()

    return {'history': chart_history, 'stage': chart_stage, 'approval': chart_approval}


@budgets_bp.route('/budgets/search/clients')
def search_clients():
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401

    user_id = session['id']
    term = (request.args.get('q') or '').strip()
    like_term = f"%{term}%"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, cpf
        FROM clients
        WHERE user_id = %s
          AND (%s = '' OR name LIKE %s OR cpf LIKE %s)
        ORDER BY name
        LIMIT 5
    """, (user_id, term, like_term, like_term))
    clients = cursor.fetchall()
    conn.close()

    return {'results': clients}


@budgets_bp.route('/budgets/search/items')
def search_items():
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401

    user_id = session['id']
    item_type = (request.args.get('type') or 'product').strip().lower()
    term = (request.args.get('q') or '').strip()
    like_term = f"%{term}%"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if item_type == 'service':
        cursor.execute("""
            SELECT id, name, price
            FROM services
            WHERE user_id = %s
              AND (%s = '' OR name LIKE %s OR description LIKE %s)
            ORDER BY name
            LIMIT 5
        """, (user_id, term, like_term, like_term))
        results = cursor.fetchall()
        for item in results:
            item['type'] = 'service'
            item['price'] = float(item.get('price') or 0)
    else:
        cursor.execute("""
            SELECT id, name, sell_price, sku, quantity AS stock_quantity
            FROM products
            WHERE user_id = %s
              AND (%s = '' OR name LIKE %s OR sku LIKE %s)
            ORDER BY name
            LIMIT 5
        """, (user_id, term, like_term, like_term))
        results = cursor.fetchall()
        for item in results:
            item['type'] = 'product'
            item['sell_price'] = float(item.get('sell_price') or 0)
            item['stock_quantity'] = float(item.get('stock_quantity') or 0)

    conn.close()
    return {'results': results}

@budgets_bp.route('/budgets/create', methods=['GET'])
def create():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch employees
    ensure_employees_schema(cursor)
    conn.commit()
    cursor.execute("SELECT id, name FROM employees WHERE user_id = %s AND COALESCE(is_active, 1) = 1 ORDER BY name", (user_id,))
    employees = cursor.fetchall()

    conn.close()
        
    return render_template('budgets/create.html', employees=employees)

@budgets_bp.route('/budgets/save', methods=['POST'])
def save_budget():
    if 'id' not in session:
        return {'error': 'Sessão expirada. Faça login novamente.'}, 401
    
    data = request.get_json() or {}
    user_id = session['id']
    user_role = session.get('role')
    
    # Extract Data
    client_name = (data.get('client_name') or '').strip()
    client_id = _parse_client_id(data.get('client_id'))
    
    plate_raw = (data.get('vehicle_plate') or '').strip()
    plate = plate_raw.upper() if plate_raw else None
    
    brand = (data.get('vehicle_brand') or '').strip() or None
    model = (data.get('vehicle_model') or '').strip() or None

    year_raw = data.get('vehicle_year')
    km_raw = data.get('vehicle_km')

    try:
        year = int(str(year_raw).strip()) if str(year_raw).strip() not in {'', 'None', 'null', 'undefined'} else None
    except (TypeError, ValueError):
        return {'error': 'Informe um ano válido para o veículo.'}, 400

    try:
        km = int(float(str(km_raw).strip())) if str(km_raw).strip() not in {'', 'None', 'null', 'undefined'} else None
    except (TypeError, ValueError):
        return {'error': 'Informe uma quilometragem válida para o veículo.'}, 400

    employee_id = data.get('employee_id') or data.get('mechanic_id')
    if employee_id and (str(employee_id).lower() in ['null', 'none', 'undefined'] or str(employee_id).strip() == ''):
        employee_id = None
    
    notes = data.get('notes')
    items = data.get('items', [])
    approval_status = data.get('approval_status') or data.get('status') or 'sent'  # Default: sent (Aguardando)
    stage_status = data.get('stage_status') or 'budget'  # Default: budget (Orçamento)

    raw_budget_date = data.get('budget_date')
    budget_date = _resolve_budget_datetime(raw_budget_date)
    if raw_budget_date and not budget_date:
        return {'error': 'Informe uma data válida para o orçamento.'}, 400
    budget_date = budget_date or datetime.now().replace(microsecond=0)

    try:
        discount = float(data.get('discount', 0) or 0)
    except (TypeError, ValueError):
        return {'error': 'Informe um desconto válido.'}, 400

    if discount < 0:
        return {'error': 'O desconto não pode ser negativo.'}, 400

    if not client_name and not client_id:
        return {'error': 'Selecione um cliente cadastrado para o orçamento.'}, 400

    if user_role in {'oficina', 'admin'} and not plate:
        return {'error': 'Informe a placa do veículo.'}, 400

    if not items:
        return {'error': 'Adicione pelo menos um item ao orçamento.'}, 400

    normalized_items = []
    for index, item in enumerate(items, start=1):
        desc = (item.get('desc') or '').strip()
        try:
            qty = float(item.get('qty') or 0)
        except (TypeError, ValueError):
            qty = 0
        try:
            price = float(item.get('price') or 0)
        except (TypeError, ValueError):
            price = 0

        if not desc:
            return {'error': f'Informe a descrição do item {index}.'}, 400
        if qty <= 0:
            return {'error': f'Informe uma quantidade válida para o item {index}.'}, 400
        if price <= 0:
            return {'error': f'Informe um valor unitário válido para o item {index}.'}, 400

        item['desc'] = desc
        item['qty'] = qty
        item['price'] = price
        item['total'] = float(item.get('total') or (qty * price))
        normalized_items.append(item)

    items = normalized_items

    allowed_approval = {'sent', 'approved', 'rejected'}
    allowed_stage = {'budget', 'ready_for_pickup', 'delivered'}
    if approval_status not in allowed_approval:
        approval_status = 'sent'
    if stage_status not in allowed_stage:
        stage_status = 'budget'

    items, item_error = _normalize_budget_items(items)
    if item_error:
        return {'error': item_error}, 400

    approval_status, stage_status, status_error = _resolve_status_transition(None, 'budget', approval_status, stage_status)
    if status_error:
        return {'error': status_error}, 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Resolve client from explicit selection
        client, client_error = _resolve_selected_client(cursor, user_id, client_id, client_name)
        if client_error:
            return {'error': client_error}, 400
        client_id = client['id']

        if approval_status == 'approved':
            stock_error = _validate_product_stock(cursor, user_id, items)
            if stock_error:
                return {'error': stock_error}, 400
            
        # 2. Find or Create/Update Vehicle (Optional)
        vehicle_id = None
        if plate:
            cursor.execute("SELECT id FROM vehicles WHERE plate = %s AND client_id = %s", (plate, client_id))
            vehicle = cursor.fetchone()
            
            if vehicle:
                vehicle_id = vehicle['id']
                cursor.execute("UPDATE vehicles SET km = %s, brand = %s, model = %s, year = %s WHERE id = %s", 
                            (km, brand, model, year, vehicle_id))
            else:
                cursor.execute("""
                    INSERT INTO vehicles (user_id, client_id, plate, brand, model, year, km, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """, (user_id, client_id, plate, brand, model, year, km))
                vehicle_id = cursor.lastrowid
            
        # 3. Create Budget Header
        total_items = sum(float(item['total']) for item in items)
        total_value = max(0, total_items - float(discount))
        expiration = (budget_date.date() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        approved_at = budget_date if approval_status == 'approved' else None
        rejected_at = budget_date if approval_status == 'rejected' else None
        ready_for_pickup_at = budget_date if stage_status == 'ready_for_pickup' else None
        delivered_at = budget_date if stage_status == 'delivered' else None

        cursor.execute("""
            INSERT INTO budgets (
                user_id, client_id, vehicle_id, vehicle_km, employee_id,
                status, approval_status, stage_status,
                approved_at, rejected_at, ready_for_pickup_at, delivered_at,
                total_value, discount, notes, expiration_date, created_at
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, (
            user_id, client_id, vehicle_id, km, employee_id,
            approval_status, approval_status, stage_status,
            approved_at, rejected_at, ready_for_pickup_at, delivered_at,
            total_value, discount, notes, expiration, budget_date
        ))
        
        budget_id = cursor.lastrowid
        
        # 4. Insert Items
        for item in items:
            product_id = item.get('product_id')
            if not product_id or str(product_id).lower() in ['null', 'undefined', '']:
                product_id = None
            
            is_service = 1 if item.get('is_service') else 0
            is_takeaway = 1 if item.get('is_takeaway') else 0

            cursor.execute("""
                INSERT INTO budget_items (budget_id, product_id, description, quantity, unit_price, total, is_service, is_takeaway, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (budget_id, product_id, item['desc'], item['qty'], item['price'], item['total'], is_service, is_takeaway))
        
        # 5. Handle Stock Deduction if Approved immediately
        if approval_status == 'approved':
            adjust_stock(cursor, budget_id, user_id, reverse=False)
            
        conn.commit()
        return {'success': True, 'budget_id': budget_id}
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving budget: {e}")
        return {'error': str(e)}, 500
    finally:
        conn.close()

@budgets_bp.route('/budgets/view/<int:id>', methods=['GET'])
def view_budget(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch Budget Header with Client and Vehicle
    cursor.execute("""
        SELECT b.*, c.name as client_name, c.cpf as client_cpf, 
               v.plate as vehicle_plate, v.brand as vehicle_brand, 
               v.model as vehicle_model, v.year as vehicle_year
        FROM budgets b
        JOIN clients c ON b.client_id = c.id
        LEFT JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.id = %s AND b.user_id = %s
    """, (id, user_id))
    budget = cursor.fetchone()
    
    if not budget:
        conn.close()
        flash('Orçamento não encontrado.', 'error')
        return redirect(url_for('budgets.list'))
        
    # Fetch Items
    cursor.execute("SELECT * FROM budget_items WHERE budget_id = %s", (id,))
    items = cursor.fetchall()

    # Fetch Financial Entry (for approved budgets)
    cursor.execute("""
        SELECT id, description, amount, payment_type, entry_date
        FROM financial_income
        WHERE user_id = %s AND budget_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id, id))
    financial = cursor.fetchone()

    if not financial:
        # Fallback for legacy records without budget_id
        cursor.execute("""
            SELECT id, description, amount, payment_type, entry_date
            FROM financial_income
            WHERE user_id = %s AND description LIKE %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, f"Orçamento #{id}%"))
        financial = cursor.fetchone()

    financial_payload = None
    if financial:
        entry_date = financial.get('entry_date')
        financial_payload = {
            'id': financial.get('id'),
            'description': financial.get('description'),
            'amount': float(financial.get('amount') or 0),
            'payment_type': financial.get('payment_type'),
            'entry_date': entry_date.strftime('%Y-%m-%d') if entry_date else ''
        }

    # Fetch Lists for editing
    cursor.execute("SELECT id, name, cpf FROM clients WHERE user_id = %s ORDER BY name", (user_id,))
    clients = cursor.fetchall()
    cursor.execute("SELECT id, name, sell_price, quantity as stock_quantity FROM products WHERE user_id = %s ORDER BY name", (user_id,))
    products = cursor.fetchall()

    cursor.execute("SELECT id, name, price FROM services WHERE user_id = %s ORDER BY name", (user_id,))
    services_list = cursor.fetchall()
    
    # Fetch employees for editing
    ensure_employees_schema(cursor)
    conn.commit()
    cursor.execute("SELECT id, name, is_active FROM employees WHERE user_id = %s AND (COALESCE(is_active, 1) = 1 OR id = %s) ORDER BY COALESCE(is_active, 1) DESC, name", (user_id, budget.get('employee_id') or 0))
    employees = cursor.fetchall()

    conn.close()
    
    return render_template('budgets/view.html', budget=budget, items=items, clients=clients, employees=employees, products=products, services_list=services_list, financial=financial_payload)

@budgets_bp.route('/budgets/update/<int:id>', methods=['POST'])
def update_budget(id):
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401
    
    data = request.get_json()
    user_id = session['id']
    
    # Extract Data (Same logic as create)
    # Ideally should validate user ownership again
    
    notes = data.get('notes')
    discount = data.get('discount', 0)
    items = data.get('items', [])
    approval_status = data.get('approval_status') or data.get('status')
    stage_status = data.get('stage_status')
    vehicle_km_raw = data.get('vehicle_km')
    budget_date_raw = data.get('budget_date')

    try:
        vehicle_km = int(float(str(vehicle_km_raw).strip())) if str(vehicle_km_raw).strip() not in {'', 'None', 'null', 'undefined'} else None
    except (TypeError, ValueError):
        return {'error': 'Informe uma quilometragem válida para o veículo.'}, 400

    employee_id = data.get('employee_id') or data.get('mechanic_id')
    if employee_id and (str(employee_id).lower() in ['null', 'none', 'undefined'] or str(employee_id).strip() == ''):
        employee_id = None
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check ownership
        cursor.execute("SELECT id FROM budgets WHERE id = %s AND user_id = %s", (id, user_id))
        if not cursor.fetchone():
            return {'error': 'Orçamento não encontrado.'}, 404

        cursor.execute("SELECT created_at FROM budgets WHERE id = %s AND user_id = %s", (id, user_id))
        existing_budget = cursor.fetchone() or {}
        budget_date = _resolve_budget_datetime(budget_date_raw, existing_budget.get('created_at')) or existing_budget.get('created_at') or datetime.now().replace(microsecond=0)
            
        items, item_error = _normalize_budget_items(items)
        if item_error:
            return {'error': item_error}, 400

        # Recalculate Total
        total_items = sum(float(item['total']) for item in items)
        total_value = max(0, total_items - float(discount))
        
        # Update Vehicle KM if provided
        cursor.execute("SELECT vehicle_id FROM budgets WHERE id = %s", (id,))
        budget_data = cursor.fetchone()
        if budget_data and budget_data['vehicle_id'] and vehicle_km:
             cursor.execute("UPDATE vehicles SET km = %s WHERE id = %s", (vehicle_km, budget_data['vehicle_id']))

        # Fetch current status fields to set timestamps only when changing.
        cursor.execute("SELECT approval_status, stage_status FROM budgets WHERE id = %s", (id,))
        current_status = cursor.fetchone() or {}
        current_approval = current_status.get('approval_status')
        current_stage = current_status.get('stage_status')

        approval_status, stage_status, status_error = _resolve_status_transition(
            current_approval,
            current_stage,
            approval_status,
            stage_status,
        )
        if status_error:
            return {'error': status_error}, 400

        # Permite "Retirada" mesmo quando ainda estiver aguardando decisão (ex.: cliente vai retirar sem aprovar).
        # But "Entregue" must have a decision to avoid "Entregue + Aguardando" on reports.
        if approval_status == 'approved':
            stock_error = _validate_product_stock(cursor, user_id, items)
            if stock_error:
                return {'error': stock_error}, 400

        status_fields, status_params = _build_status_update_fields(approval_status, stage_status, budget_date)
        fields = status_fields + [
            "created_at = %s",
            "expiration_date = %s",
            "total_value = %s",
            "discount = %s",
            "notes = %s",
            "vehicle_km = %s",
            "employee_id = %s",
        ]
        params = status_params + [
            budget_date,
            (budget_date.date() + timedelta(days=7)).strftime('%Y-%m-%d'),
            total_value,
            discount,
            notes,
            vehicle_km,
            employee_id,
        ]

        params.append(id)
        cursor.execute(f"""
            UPDATE budgets
            SET {', '.join(fields)}
            WHERE id = %s
        """, tuple(params))
        
        # Handle Stock Restoration (if currently approved)
        # Since we are re-inserting items, we must restore stock for old items if they were deducted.
        if current_approval == 'approved':
            adjust_stock(cursor, id, user_id, reverse=True)

        # Update Items (Strategy: Delete All and Re-insert)
        # Simple/Robust strategy for MVP
        cursor.execute("DELETE FROM budget_items WHERE budget_id = %s", (id,))
        
        for item in items:
            is_service = 1 if item.get('is_service') else 0
            is_takeaway = 1 if item.get('is_takeaway') else 0

            cursor.execute("""
                INSERT INTO budget_items (budget_id, product_id, description, quantity, unit_price, total, is_service, is_takeaway, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (id, item['product_id'], item['desc'], item['qty'], item['price'], item['total'], is_service, is_takeaway))

        # Handle Stock Deduction (if newly approved or remains approved)
        if approval_status == 'approved':
            adjust_stock(cursor, id, user_id, reverse=False)
            
        conn.commit()
        return {'success': True}
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating budget: {e}")
        return {'error': str(e)}, 500
    finally:
        conn.close()

@budgets_bp.route('/budgets/quick_status/<int:id>', methods=['POST'])
def quick_status(id):
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401

    user_id = session['id']
    data = request.get_json() or {}
    action = (data.get('action') or '').strip()

    allowed_actions = {'awaiting', 'ready_for_pickup', 'delivered'}
    if action not in allowed_actions:
        return {'error': 'Ação inválida.'}, 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, status, approval_status, stage_status
            FROM budgets
            WHERE id = %s AND user_id = %s
        """, (id, user_id))
        budget = cursor.fetchone()
        if not budget:
            return {'error': 'Orçamento não encontrado.'}, 404

        current_approval = budget.get('approval_status') or budget.get('status') or 'sent'
        current_stage = budget.get('stage_status') or 'budget'

        new_approval = current_approval
        new_stage = current_stage

        if action == 'awaiting':
            new_approval = 'sent'
            new_stage = 'budget'
            if current_approval == 'approved':
                adjust_stock(cursor, id, user_id, reverse=True)
                
        elif action == 'ready_for_pickup':
            if current_stage == 'delivered':
                return {'error': 'Já está Entregue.'}, 400
            new_stage = 'ready_for_pickup'
        elif action == 'delivered':
            if current_approval == 'sent':
                return {'error': 'Defina Aprovado/Reprovado antes de marcar Entregue.'}, 400
            if current_stage != 'ready_for_pickup':
                return {'error': 'Marque Retirada antes de marcar Entregue.'}, 400
            new_stage = 'delivered'

        now = datetime.now()
        fields, params = _build_status_update_fields(new_approval, new_stage, now)

        params.extend([id, user_id])
        cursor.execute(f"""
            UPDATE budgets
            SET {', '.join(fields)}
            WHERE id = %s AND user_id = %s
        """, tuple(params))

        conn.commit()
        return {'success': True}

    except Exception as e:
        conn.rollback()
        print(f"Error quick updating budget: {e}")
        return {'error': str(e)}, 500
    finally:
        conn.close()

@budgets_bp.route('/budgets/print/<int:id>', methods=['GET'])
def print_budget(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch Budget Header (Same as view)
    cursor.execute("""
        SELECT b.*, c.name as client_name, c.cpf as client_cpf, 
               c.phone1 as client_phone,
               v.plate as vehicle_plate, v.brand as vehicle_brand, 
               v.model as vehicle_model, v.year as vehicle_year, v.color as vehicle_color,
               v.km as vehicle_km
        FROM budgets b
        JOIN clients c ON b.client_id = c.id
        LEFT JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.id = %s AND b.user_id = %s
    """, (id, user_id))
    budget = cursor.fetchone()
    
    if not budget:
        conn.close()
        flash('Orçamento não encontrado.', 'error')
        return redirect(url_for('budgets.list'))
        
    # Fetch Items
    cursor.execute("SELECT * FROM budget_items WHERE budget_id = %s", (id,))
    items = cursor.fetchall()
    
    conn.close()
    
    return render_template('budgets/print.html', budget=budget, items=items)

@budgets_bp.route('/budgets/approve_financial/<int:id>', methods=['POST'])
def approve_financial(id):
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401
    
    user_id = session['id']
    data = request.get_json()
    
    # Financial Data
    description = data.get('description')
    amount = data.get('amount')
    payment_type = data.get('payment_type')
    entry_date = data.get('entry_date')
    
    if not description or not amount or not entry_date:
         return {'error': 'Preencha descrição, valor e data de recebimento.'}, 400

    print(f"Approving Budget {id}: Desc={description}, Amount={amount}, Type={payment_type}, Date={entry_date}")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check ownership
        cursor.execute("SELECT id, approval_status FROM budgets WHERE id = %s AND user_id = %s", (id, user_id))
        budget_row = cursor.fetchone()
        if not budget_row:
            return {'error': 'Orçamento não encontrado.'}, 404
            
        current_approval = budget_row['approval_status']
        
        # 1. Update Budget Status
        cursor.execute("""
            UPDATE budgets
            SET status = 'approved', approval_status = 'approved', approved_at = COALESCE(approved_at, NOW())
            WHERE id = %s
        """, (id,))
        
        # Adjust stock if not already approved
        if current_approval != 'approved':
            adjust_stock(cursor, id, user_id, reverse=False)
            
        # 2. Upsert Financial Income linked to budget
        cursor.execute("""
            SELECT id FROM financial_income
            WHERE user_id = %s AND budget_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE financial_income
                SET description = %s, amount = %s, payment_type = %s, entry_date = %s
                WHERE id = %s
            """, (description, amount, payment_type, entry_date, existing['id']))
        else:
            cursor.execute("""
                INSERT INTO financial_income (user_id, budget_id, description, amount, category, payment_type, entry_date, created_at)
                VALUES (%s, %s, %s, %s, 'serviço', %s, %s, NOW())
            """, (user_id, id, description, amount, payment_type, entry_date))
        
        conn.commit()
        return {'success': True}
        
    except Exception as e:
        conn.rollback()
        print(f"Error approving budget: {e}")
        return {'error': str(e)}, 500
    finally:
        conn.close()

@budgets_bp.route('/budgets/update_financial/<int:id>', methods=['POST'])
def update_financial(id):
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401

    user_id = session['id']
    data = request.get_json()

    description = data.get('description')
    amount = data.get('amount')
    payment_type = data.get('payment_type')
    entry_date = data.get('entry_date')

    if not description or not amount or not entry_date:
        return {'error': 'Dados incompletos'}, 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check ownership
        cursor.execute("SELECT id FROM budgets WHERE id = %s AND user_id = %s", (id, user_id))
        if not cursor.fetchone():
            return {'error': 'Orçamento não encontrado.'}, 404

        # Update existing financial entry
        cursor.execute("""
            SELECT id FROM financial_income
            WHERE user_id = %s AND budget_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE financial_income
                SET description = %s, amount = %s, payment_type = %s, entry_date = %s
                WHERE id = %s
            """, (description, amount, payment_type, entry_date, existing['id']))
        else:
            # Fallback: create if missing
            cursor.execute("""
                INSERT INTO financial_income (user_id, budget_id, description, amount, category, payment_type, entry_date, created_at)
                VALUES (%s, %s, %s, %s, 'serviço', %s, %s, NOW())
            """, (user_id, id, description, amount, payment_type, entry_date))

        conn.commit()
        return {'success': True}

    except Exception as e:
        conn.rollback()
        print(f"Error updating financial for budget: {e}")
        return {'error': str(e)}, 500
    finally:
        conn.close()

