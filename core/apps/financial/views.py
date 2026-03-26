from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from common.database import get_db_connection
from common.financial_categories import is_valid_financial_category, list_financial_categories
from apps.auth.views import login_required
from datetime import datetime, date

financial_bp = Blueprint('financial', __name__, 
                        template_folder='../../templates/financial',
                        url_prefix='/financial')

@financial_bp.route('/income')
@login_required
def income_list():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    income_categories = list_financial_categories('income')
    if category_filter and category_filter not in income_categories:
        category_filter = ''
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    user_id = session['id']
    offset = (page - 1) * per_page
    
    # Base query
    query = "SELECT * FROM financial_income WHERE user_id = %s"
    params = [user_id]
    
    if search_query:
        query += " AND (description LIKE %s OR category LIKE %s OR CAST(amount AS CHAR) LIKE %s)"
        term = f"%{search_query}%"
        params.extend([term, term, term])
    
    if category_filter and category_filter != 'Todas':
        query += " AND category = %s"
        params.append(category_filter)
        
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
    
    # Count total for pagination
    count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
    cursor.execute(count_query, tuple(params))
    total_records = cursor.fetchone()['total']
    total_pages = (total_records + per_page - 1) // per_page
    
    # Calculate Statistics
    if status_filter == 'pending':
        # FUTURE STATS (Projections)
        stats_query = """
            SELECT 
                COALESCE(SUM(CASE WHEN entry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN amount ELSE 0 END), 0) as total_7d,
                COALESCE(SUM(CASE WHEN entry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN amount ELSE 0 END), 0) as total_30d,
                COALESCE(SUM(CASE WHEN entry_date > CURDATE() THEN amount ELSE 0 END), 0) as total_future
            FROM financial_income 
            WHERE user_id = %s AND status = 'pending'
        """
    else:
        # PAST/RECEIVED STATS (History) - Default behavior (mixed if no filter, or received only)
        # Note: If status='received', we strictly look at received. If 'all', we look at everything? 
        # Usually stats for "Incomes" imply realized gains, but if 'all' is selected, maybe realized?
        # Let's keep original logic for 'all' and 'received' but maybe filter by status if provided.
        
        base_stats_condition = "user_id = %s"
        stats_params = [user_id]
        if status_filter == 'received':
            base_stats_condition += " AND status = 'received'"

        stats_query = f"""
            SELECT 
                COALESCE(SUM(CASE WHEN entry_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND CURDATE() THEN amount ELSE 0 END), 0) as total_7d,
                COALESCE(SUM(CASE WHEN entry_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE() THEN amount ELSE 0 END), 0) as total_30d,
                COALESCE(SUM(CASE WHEN entry_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 12 MONTH) AND CURDATE() THEN amount ELSE 0 END), 0) as total_12m,
                COALESCE(SUM(CASE WHEN status='pending' OR entry_date > CURDATE() THEN amount ELSE 0 END), 0) as total_future
            FROM financial_income 
            WHERE {base_stats_condition}
        """
    
    if status_filter == 'pending':
        stats_params = [user_id]

    cursor.execute(stats_query, tuple(stats_params))
    stats_data = cursor.fetchone()
    
    total_7d = stats_data['total_7d']
    total_30d = stats_data.get('total_30d', 0)
    total_future = stats_data.get('total_future', 0)
    
    today = date.today()
    current_day = today.day
    
    if status_filter == 'pending':
        # Projected daily average for next 30 days
        avg_daily_30d = total_30d / 30
    else:
        # Realized daily average
        if current_day > 0:
            avg_daily_30d = total_30d / current_day
        else:
            avg_daily_30d = 0
    
    stats = {
        'total_7d': total_7d,
        'total_30d': total_30d,
        'avg_daily_30d': avg_daily_30d,
        'total_future': total_future
    }
    
    # Fetch data for list (latest launch first)
    query += " ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    cursor.execute(query, tuple(params))
    incomes = cursor.fetchall()
    
    # --- Chart Data Preparation ---
    
    # 1. Income History (Last 6 Months)
    # Filter for charts should match the table filters ideally
    chart_history_where = "user_id = %s"
    chart_history_params = [user_id]
    
    if category_filter and category_filter != 'Todas':
        chart_history_where += " AND category = %s"
        chart_history_params.append(category_filter)
        
    if status_filter:
        chart_history_where += " AND status = %s"
        chart_history_params.append(status_filter)
        
    chart_history_query = f"""
        SELECT DATE_FORMAT(entry_date, '%Y-%m') as month_year, SUM(amount) as total
        FROM financial_income
        WHERE {chart_history_where} 
          AND entry_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(entry_date, '%Y-%m')
        ORDER BY month_year ASC
    """
    cursor.execute(chart_history_query, tuple(chart_history_params))
    history_results = cursor.fetchall()
    
    # Process into labels (Mon/Year) and data
    chart_history = {'labels': [], 'values': []}
    for row in history_results:
        # Format label as 'Jan/24'
        if row['month_year']:
            try:
                date_obj = datetime.strptime(str(row['month_year']), '%Y-%m')
                # PT-BR Month Map
                months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                             7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                month_label = f"{months_pt[date_obj.month]}/{date_obj.strftime('%y')}"
                chart_history['labels'].append(str(month_label))
            except Exception:
                chart_history['labels'].append(str(row['month_year']))
        else:
            chart_history['labels'].append("Unknown")
            
        chart_history['values'].append(float(row['total']) if row['total'] is not None else 0.0)
        
    # 2. Category Distribution (Last 12 Months by entry_date)
    chart_category_query = f"""
        SELECT category, SUM(amount) as total
        FROM financial_income
        WHERE {chart_history_where}
          AND entry_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY category
    """
    cursor.execute(chart_category_query, tuple(chart_history_params))
    category_results = cursor.fetchall()
    
    chart_category = {'labels': [], 'values': []}
    for row in category_results:
        cat_name = row['category']
        if cat_name is None:
            cat_name = "Sem Categoria"
        
        # Ensure it's a string and capitalize found 'title' issue potential
        chart_category['labels'].append(str(cat_name).title())
        chart_category['values'].append(float(row['total']) if row['total'] is not None else 0.0)

    cursor.close()
    conn.close()

    # Pre-serialize to strict JSON to avoid Template errors
    import json
    chart_history_json = json.dumps(chart_history)
    chart_category_json = json.dumps(chart_category)
    
    # Month options for chart filter (last 6 months)
    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    month_options = []
    base = date.today().replace(day=1)
    base_total = base.year * 12 + (base.month - 1)
    for i in range(5, -1, -1):
        total = base_total - i
        year = total // 12
        month = total % 12 + 1
        value = f"{year:04d}-{month:02d}"
        label = f"{months_pt[month]}/{str(year)[-2:]}"
        month_options.append({'value': value, 'label': label})

    return render_template('income.html', 
                         incomes=incomes, 
                         page=page, 
                         total_pages=total_pages, 
                         search=search_query,
                         stats=stats,
                         category_filter=category_filter,
                         status_filter=status_filter,
                         today=date.today(),
                         chart_history_json=chart_history_json,
                         chart_category_json=chart_category_json,
                         month_options=month_options,
                         income_categories=income_categories)

@financial_bp.route('/charts')
@login_required
def charts():
    category_filter = request.args.get('category', '')
    month_filter = request.args.get('month', '')
    status_filter = request.args.get('status', '')
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

    # History (Last 6 Months) by entry_date, or Daily for selected month
    chart_history_params = [user_id]
    base_history_where = "user_id = %s"
    
    if status_filter:
        base_history_where += " AND status = %s"
        chart_history_params.append(status_filter)

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

        chart_history_query = f"""
            SELECT DATE(entry_date) as date, SUM(amount) as total
            FROM financial_income
            WHERE {base_history_where}
        """
        if start_month and end_month:
            chart_history_query += " AND entry_date >= %s AND entry_date < %s"
            chart_history_params.extend([start_month, end_month])
        if category_filter and category_filter != 'Todas':
            chart_history_query += " AND category = %s"
            chart_history_params.append(category_filter)
        chart_history_query += " GROUP BY DATE(entry_date) ORDER BY date ASC"
        cursor.execute(chart_history_query, tuple(chart_history_params))
        history_results = cursor.fetchall()

        # Build daily labels for the month
        if start_month and end_month:
            days_in_month = (end_month - start_month).days
        else:
            days_in_month = 0

        totals_map = {str(row['date']): float(row['total'] or 0) for row in history_results}
        chart_history = {'labels': [], 'values': []}
        if start_month:
            for day in range(1, days_in_month + 1):
                d = date(start_month.year, start_month.month, day)
                chart_history['labels'].append(d.strftime('%d/%m'))
                chart_history['values'].append(totals_map.get(str(d), 0.0))
    else:
        chart_history_query = f"""
            SELECT DATE_FORMAT(entry_date, '%Y-%m') as month_year, SUM(amount) as total
            FROM financial_income
            WHERE {base_history_where}
              AND entry_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        """
        # Note: params already has user_id and status (if set)
        
        if category_filter and category_filter != 'Todas':
            chart_history_query += " AND category = %s"
            chart_history_params.append(category_filter)
        chart_history_query += " GROUP BY DATE_FORMAT(entry_date, '%Y-%m') ORDER BY month_year ASC"
        cursor.execute(chart_history_query, tuple(chart_history_params))
        history_results = cursor.fetchall()

        totals_map = {row['month_year']: float(row['total'] or 0) for row in history_results}
        chart_history = {'labels': [], 'values': []}

        # Build last 6 months labels
        base = date.today().replace(day=1)
        base_total = base.year * 12 + (base.month - 1)
        for i in range(5, -1, -1):
            total = base_total - i
            y = total // 12
            m = total % 12 + 1
            key = f"{y:04d}-{m:02d}"
            label = f"{months_pt[m]}/{str(y)[-2:]}"
            chart_history['labels'].append(label)
            chart_history['values'].append(totals_map.get(key, 0.0))

    # Category Distribution (Last 12 Months) by entry_date
    chart_category_query = f"""
        SELECT category, SUM(amount) as total
        FROM financial_income
        WHERE {base_history_where}
    """
    chart_category_params = list(chart_history_params[:1 if not status_filter else 2]) # Reuse base params (user_id, status?)
    # Re-build params carefully
    chart_category_params = [user_id]
    if status_filter:
        chart_category_params.append(status_filter)

    if category_filter and category_filter != 'Todas':
        chart_category_query += " AND category = %s"
        chart_category_params.append(category_filter)
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
        if start_month and end_month:
            chart_category_query += " AND entry_date >= %s AND entry_date < %s"
            chart_category_params.extend([start_month, end_month])
    else:
        chart_category_query += " AND entry_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)"
    chart_category_query += " GROUP BY category"
    cursor.execute(chart_category_query, tuple(chart_category_params))
    category_results = cursor.fetchall()

    chart_category = {'labels': [], 'values': []}
    for row in category_results:
        cat_name = row['category'] if row['category'] is not None else "Sem Categoria"
        chart_category['labels'].append(str(cat_name).title())
        chart_category['values'].append(float(row['total']) if row['total'] is not None else 0.0)

    cursor.close()
    conn.close()

    return jsonify({'history': chart_history, 'category': chart_category})


@financial_bp.route('/income/add', methods=['POST'])
@login_required
def add_income():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        category = request.form['category']
        payment_type = request.form['payment_type']
        entry_date = request.form['entry_date']

        if not is_valid_financial_category('income', category):
            flash('Categoria de entrada inválida.', 'error')
            return redirect(url_for('financial.income_list'))
        status = request.form.get('status', 'received')
        user_id = session['id']

        if not description or not amount or not entry_date:
            flash('Preencha campos (desc, valor, data)', 'error')
            return redirect(url_for('financial.income_list'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # If status is received, set received_date. Else None.
            received_date = entry_date if status == 'received' else None

            query = """
                INSERT INTO financial_income (user_id, description, amount, category, payment_type, entry_date, status, received_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, description, amount, category, payment_type, entry_date, status, received_date))
            conn.commit()
            flash('Receita registrada!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Erro: {str(e)}', 'error')
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
        # Atomic delete ensuring user ownership
        delete_query = "DELETE FROM financial_income WHERE id = %s AND user_id = %s"
        cursor.execute(delete_query, (id, session['id']))
        
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
    category = request.form['category']
    payment_type = request.form['payment_type']
    entry_date = request.form['entry_date']

    if not is_valid_financial_category('income', category):
        flash('Categoria de entrada inválida.', 'error')
        return redirect(url_for('financial.income_list'))
    status = request.form.get('status', 'received')
    user_id = session['id']

    if not description or not amount or not entry_date:
        flash('Preencha campos (desc, valor, data)', 'error')
        return redirect(url_for('financial.income_list'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        check_query = "SELECT id FROM financial_income WHERE id=%s AND user_id=%s"
        cursor.execute(check_query, (id, user_id))
        if not cursor.fetchone():
            flash('Não encontrado/sem permissão.', 'error')
            return redirect(url_for('financial.income_list'))

        received_date = entry_date if status == 'received' else None
        
        update_query = """
            UPDATE financial_income
            SET description=%s, amount=%s, category=%s, payment_type=%s, entry_date=%s, status=%s, received_date=%s
            WHERE id=%s
        """

        cursor.execute(update_query, (description, amount, category, payment_type, entry_date, status, received_date, id))
        conn.commit()
        flash('Receita atualizada!', 'success')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('financial.income_list'))

# --- EXPENSES (Despesas / Contas a Pagar) ---

@financial_bp.route('/expenses')
@login_required
def expenses_list():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    search_query = request.args.get('search', '')
    expense_categories = list_financial_categories('expense')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    user_id = session['id']
    offset = (page - 1) * per_page
    
    query = "SELECT * FROM financial_expenses WHERE user_id = %s"
    params = [user_id]
    
    if search_query:
        query += " AND (description LIKE %s OR category LIKE %s OR CAST(amount AS CHAR) LIKE %s)"
        term = f"%{search_query}%"
        params.extend([term, term, term])
        
    count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
    cursor.execute(count_query, tuple(params))
    res = cursor.fetchone()
    total_records = res['total'] if res else 0
    total_pages = (total_records + per_page - 1) // per_page
    
    stats_query = """
        SELECT 
            COALESCE(SUM(CASE WHEN status='pending' AND due_date < CURDATE() THEN amount ELSE 0 END), 0) as overdue,
            COALESCE(SUM(CASE WHEN status='pending' AND due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN amount ELSE 0 END), 0) as due_7d,
            COALESCE(SUM(CASE WHEN status='pending' AND due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN amount ELSE 0 END), 0) as due_30d,
            COALESCE(SUM(CASE WHEN status='pending' THEN amount ELSE 0 END), 0) as total_pending
        FROM financial_expenses 
        WHERE user_id = %s
    """
    cursor.execute(stats_query, (user_id,))
    stats = cursor.fetchone()
    if not stats:
        stats = {'overdue': 0, 'due_7d': 0, 'due_30d': 0, 'total_pending': 0}
    
    query += " ORDER BY due_date ASC, id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    cursor.execute(query, tuple(params))
    expenses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('financial/expenses.html', expenses=expenses, page=page, total_pages=total_pages, search=search_query, stats=stats, today=date.today(), expense_categories=expense_categories)

@financial_bp.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        category = request.form['category']
        payment_type = request.form['payment_type']
        due_date = request.form['due_date']

        if not is_valid_financial_category('expense', category):
            flash('Categoria de despesa inválida.', 'error')
            return redirect(url_for('financial.expenses_list'))
        status = request.form.get('status', 'pending')
        user_id = session['id']

        if not description or not amount or not due_date:
            flash('Preencha campos (desc, valor, data)', 'error')
            return redirect(url_for('financial.expenses_list'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            paid_date = due_date if status == 'paid' else None
            query = "INSERT INTO financial_expenses (user_id, description, amount, category, payment_type, due_date, status, paid_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (user_id, description, amount, category, payment_type, due_date, status, paid_date))
            conn.commit()
            flash('Despesa registrada!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Erro: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('financial.expenses_list'))

@financial_bp.route('/expenses/update/<int:id>', methods=['POST'])
@login_required
def update_expense(id):
    description = request.form['description']
    amount = request.form['amount']
    category = request.form['category']
    payment_type = request.form['payment_type']
    due_date = request.form['due_date']

    if not is_valid_financial_category('expense', category):
        flash('Categoria de despesa inválida.', 'error')
        return redirect(url_for('financial.expenses_list'))
    status = request.form.get('status', 'pending')
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        paid_date = due_date if status == 'paid' else None
        q = "UPDATE financial_expenses SET description=%s, amount=%s, category=%s, payment_type=%s, due_date=%s, status=%s, paid_date=%s WHERE id=%s AND user_id=%s"
        cursor.execute(q, (description, amount, category, payment_type, due_date, status, paid_date, id, user_id))
        conn.commit()
        flash('Despesa atualizada!', 'success')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
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
        flash('Despesa removida!', 'success')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('financial.expenses_list'))


