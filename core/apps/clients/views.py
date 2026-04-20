from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
import re
from datetime import datetime, timedelta
from common.database import get_db_connection

clients_bp = Blueprint('clients', __name__)
OPTIONAL_CLIENT_COLUMNS = {'legal_name', 'trade_name', 'contract_start_date'}
OPTIONAL_ADDRESS_COLUMNS = {'cep', 'complement'}


def _get_client_columns(cursor):
    cursor.execute("SHOW COLUMNS FROM clients")
    return {row['Field'] for row in cursor.fetchall()}


def _normalize_text(value, mode='title'):
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if mode == 'upper':
        return value.upper()
    if mode == 'raw':
        return value
    return value.title()


def _base_client_payload(form):
    return {
        'name': _normalize_text(form.get('name')),
        'legal_name': _normalize_text(form.get('legal_name')),
        'trade_name': _normalize_text(form.get('trade_name')),
        'sector': _normalize_text(form.get('sector')),
        'contract_start_date': form.get('contract_start_date') or None,
        'cpf': _normalize_text(form.get('cpf'), 'raw'),
        'phone1': _normalize_text(form.get('phone1'), 'raw'),
        'phone2': _normalize_text(form.get('phone2'), 'raw'),
        'cep': _normalize_text(form.get('cep'), 'raw'),
        'address': _normalize_text(form.get('address')),
        'address_number': _normalize_text(form.get('address_number'), 'raw'),
        'complement': _normalize_text(form.get('complement')),
        'neighborhood': _normalize_text(form.get('neighborhood')),
        'city': _normalize_text(form.get('city')),
        'state': _normalize_text(form.get('state'), 'upper'),
    }


def _filter_payload(payload, available_columns):
    return {key: value for key, value in payload.items() if key in available_columns}


def _document_digits(value):
    raw_value = str(value or '').strip()
    if raw_value.lower() in {'null', 'none', 'undefined', ''}:
        return ''
    return re.sub(r'\D', '', raw_value)


def _is_repeated_digits(value):
    return bool(value) and len(set(value)) == 1


def _is_valid_cpf(value):
    digits = _document_digits(value)
    if len(digits) != 11 or _is_repeated_digits(digits):
        return False

    total = sum(int(digits[i]) * (10 - i) for i in range(9))
    remainder = (total * 10) % 11
    first_digit = 0 if remainder == 10 else remainder
    if first_digit != int(digits[9]):
        return False

    total = sum(int(digits[i]) * (11 - i) for i in range(10))
    remainder = (total * 10) % 11
    second_digit = 0 if remainder == 10 else remainder
    return second_digit == int(digits[10])


def _is_valid_cnpj(value):
    digits = _document_digits(value)
    if len(digits) != 14 or _is_repeated_digits(digits):
        return False

    def calc_digit(base, weights):
        total = sum(int(num) * weight for num, weight in zip(base, weights))
        remainder = total % 11
        return '0' if remainder < 2 else str(11 - remainder)

    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first_digit = calc_digit(digits[:12], first_weights)
    second_digit = calc_digit(digits[:12] + first_digit, second_weights)
    return digits[-2:] == first_digit + second_digit


def _validate_document(value):
    digits = _document_digits(value)
    if not digits:
        return None
    if len(digits) == 11 and _is_valid_cpf(digits):
        return None
    if len(digits) == 14 and _is_valid_cnpj(digits):
        return None
    return 'Informe um CPF ou CNPJ válido.'


def _find_duplicate_client_by_document(cursor, user_id, document_value, current_id=None):
    digits = _document_digits(document_value)
    if not digits:
        return None

    cursor.execute(
        """
        SELECT id, name, cpf
        FROM clients
        WHERE user_id = %s
          AND REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(cpf, ''), '.', ''), '-', ''), '/', ''), ' ', '') = %s
        ORDER BY id DESC
        """,
        (user_id, digits),
    )
    for row in cursor.fetchall():
        if current_id and int(row['id']) == int(current_id):
            continue
        return row
    return None


def _validate_client_payload(cursor, user_id, payload, current_id=None):
    if not payload.get('name'):
        return 'Informe o nome do cliente.'

    document_error = _validate_document(payload.get('cpf'))
    if document_error:
        return document_error

    duplicate = _find_duplicate_client_by_document(cursor, user_id, payload.get('cpf'), current_id=current_id)
    if duplicate:
        return f"Já existe um cliente cadastrado com este CPF/CNPJ: {duplicate['name']}."

    return None


@clients_bp.route('/clients')
def list():
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        client_columns = _get_client_columns(cursor)

        search_query = request.args.get('search')
        sector_filter = request.args.get('sector')

        select_fields = ['*']
        for column in sorted(OPTIONAL_CLIENT_COLUMNS | OPTIONAL_ADDRESS_COLUMNS):
            if column not in client_columns:
                select_fields.append(f"NULL AS {column}")

        query = f"SELECT {', '.join(select_fields)} FROM clients WHERE user_id = %s"
        params = [user_id]

        if search_query:
            search_parts = ["name LIKE %s", "cpf LIKE %s"]
            term = f"%{search_query}%"
            params.extend([term, term])
            if 'legal_name' in client_columns:
                search_parts.append("legal_name LIKE %s")
                params.append(term)
            if 'trade_name' in client_columns:
                search_parts.append("trade_name LIKE %s")
                params.append(term)
            query += " AND (" + " OR ".join(search_parts) + ")"

        if sector_filter:
            query += " AND sector = %s"
            params.append(sector_filter)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, tuple(params))
        clients = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) as total FROM clients WHERE user_id = %s", (user_id,))
        total_clients = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM clients WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)", (user_id,))
        new_weekly = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM clients WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)", (user_id,))
        new_monthly = cursor.fetchone()['total']

        stats = {
            'total_clients': total_clients,
            'new_weekly': new_weekly,
            'new_monthly': new_monthly
        }

        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM clients
            WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (user_id,))
        growth_results = cursor.fetchall()

        today = datetime.now().date()
        last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        chart_growth_data = {'dates': [], 'counts': []}
        growth_map = {row['date']: row['count'] for row in growth_results if row['date']}

        for day in last_7_days:
            chart_growth_data['dates'].append(day.strftime('%d/%m'))
            chart_growth_data['counts'].append(growth_map.get(day, 0))

        cursor.execute("""
            SELECT sector, COUNT(*) as count
            FROM clients
            WHERE user_id = %s
            GROUP BY sector
        """, (user_id,))
        sector_results = cursor.fetchall()

        chart_sectors_data = {
            'labels': [row['sector'] for row in sector_results],
            'values': [row['count'] for row in sector_results],
            'colors': ['#3b82f6', '#eab308', '#22c55e', '#ef4444', '#8b5cf6', '#ec4899']
        }

        cursor.execute("SELECT DISTINCT sector FROM clients WHERE user_id = %s ORDER BY sector", (user_id,))
        sectors = [row['sector'] for row in cursor.fetchall() if row['sector']]

    finally:
        conn.close()

    return render_template('clients/index.html',
                         clients=clients,
                         stats=stats,
                         sectors=sectors,
                         active_search=search_query,
                         active_sector=sector_filter,
                         chart_growth_json=json.dumps(chart_growth_data),
                         chart_sectors_json=json.dumps(chart_sectors_data),
                         active_page='clients')


@clients_bp.route('/clients/add', methods=['POST'])
def add_client():
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        client_columns = _get_client_columns(cursor)
        payload = _filter_payload(_base_client_payload(request.form), client_columns)
        validation_error = _validate_client_payload(cursor, user_id, payload)
        if validation_error:
            flash(validation_error)
            return redirect(url_for('clients.list'))

        columns = ['user_id'] + list(payload.keys()) + ['created_at']
        values = [user_id] + list(payload.values()) + [datetime.now()]
        placeholders = ', '.join(['%s'] * len(columns))

        query = f"INSERT INTO clients ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(query, tuple(values))
        conn.commit()
        flash('Cliente adicionado com sucesso!')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao adicionar cliente: {e}')
    finally:
        conn.close()

    return redirect(url_for('clients.list'))


@clients_bp.route('/clients/edit/<int:id>', methods=['POST'])
def edit_client(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        client_columns = _get_client_columns(cursor)
        payload = _filter_payload(_base_client_payload(request.form), client_columns)

        cursor.execute("SELECT user_id FROM clients WHERE id = %s", (id,))
        client = cursor.fetchone()

        if client and client['user_id'] == user_id:
            validation_error = _validate_client_payload(cursor, user_id, payload, current_id=id)
            if validation_error:
                flash(validation_error)
                return redirect(url_for('clients.list'))

            assignments = [f"{column} = %s" for column in payload.keys()]
            assignments.append("updated_at = %s")
            values = list(payload.values()) + [datetime.now(), id]
            query = f"UPDATE clients SET {', '.join(assignments)} WHERE id = %s"
            cursor.execute(query, tuple(values))
            conn.commit()
            flash('Cliente atualizado com sucesso!')
        else:
            flash('Cliente não encontrado ou permissão negada.')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao atualizar cliente: {e}')
    finally:
        conn.close()

    return redirect(url_for('clients.list'))


@clients_bp.route('/clients/delete/<int:id>', methods=['POST'])
def delete_client(id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM clients WHERE id = %s", (id,))
    client = cursor.fetchone()

    if client and client[0] == user_id:
        try:
            cursor.execute("DELETE FROM clients WHERE id = %s", (id,))
            conn.commit()
            flash('Cliente excluído com sucesso!')
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao excluir cliente: {e}')
    else:
        flash('Cliente não encontrado.')

    conn.close()
    return redirect(url_for('clients.list'))
