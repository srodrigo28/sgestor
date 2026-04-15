from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
from common.database import get_db_connection

products_bp = Blueprint('products', __name__)

@products_bp.route('/products')
def list_products():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch Categories (for filter and modal) from new table
    cursor.execute("SELECT id, name FROM categories WHERE user_id = %s ORDER BY name", (user_id,))
    categories = cursor.fetchall()

    # 2. Fetch Products with Supplier and Category Name
    category_filter = request.args.get('category')
    search_query = request.args.get('search')
    
    query = """
        SELECT p.*, s.name as supplier_name, c.name as category_name
        FROM products p 
        LEFT JOIN suppliers s ON p.supplier_id = s.id 
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.user_id = %s 
    """
    params = [user_id]
    
    if category_filter:
        # Filter by Category ID if numeric, else legacy name? 
        # Let's assume filter passes ID now, or we handle both.
        # If the UI sends the category NAME (old behavior), we can match c.name
        if category_filter.isdigit():
             query += " AND p.category_id = %s"
             params.append(category_filter)
        else:
             query += " AND c.name = %s"
             params.append(category_filter)
        
    if search_query:
        query += " AND (p.name LIKE %s OR c.name LIKE %s)"
        term = f"%{search_query}%"
        params.extend([term, term])
        
    query += " ORDER BY p.created_at DESC"
    
    cursor.execute(query, tuple(params))
    products = cursor.fetchall()

    # 3. Fetch Suppliers for Modal
    cursor.execute("SELECT id, name FROM suppliers WHERE user_id = %s ORDER BY name", (user_id,))
    suppliers = cursor.fetchall()

    # 3. Calculate Stats
    total_items = sum(p['quantity'] for p in products)
    total_cost = sum(p['quantity'] * float(p['cost_price'] or 0) for p in products)
    total_sell = sum(p['quantity'] * float(p['sell_price'] or 0) for p in products)
    low_stock = sum(1 for p in products if p['quantity'] <= (p.get('min_quantity') or 0))

    stats = {
        'total_items': total_items,
        'total_cost': total_cost,
        'total_sell': total_sell,
        'low_stock': low_stock
    }

    # 4. Prepare Chart Data (last 6 months by created_at)
    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

    cursor.execute((
        "SELECT DATE_FORMAT(created_at, '%Y-%m') as month_year, COUNT(*) as total "
        "FROM products "
        "WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH) "
        "GROUP BY DATE_FORMAT(created_at, '%Y-%m') "
        "ORDER BY month_year ASC"
    ), (user_id,))
    history_results = cursor.fetchall()
    totals_map = {row['month_year']: int(row['total'] or 0) for row in history_results}

    chart_entries_data = {'dates': [], 'counts': []}
    base = date.today().replace(day=1)
    base_total = base.year * 12 + (base.month - 1)
    for i in range(5, -1, -1):
        total = base_total - i
        y = total // 12
        m = total % 12 + 1
        key = f"{y:04d}-{m:02d}"
        label = f"{months_pt[m]}/{str(y)[-2:]}"
        chart_entries_data['dates'].append(label)
        chart_entries_data['counts'].append(totals_map.get(key, 0))

    # Categories Chart (last 12 months by created_at)
    cursor.execute((
        "SELECT COALESCE(category, 'Sem Categoria') as category, SUM(quantity) as total "
        "FROM products "
        "WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH) "
        "GROUP BY COALESCE(category, 'Sem Categoria') "
        "ORDER BY total DESC "
        "LIMIT 5"
    ), (user_id,))
    categories_results = cursor.fetchall()

    chart_categories_data = {
        'labels': [row['category'] for row in categories_results],
        'values': [int(row['total'] or 0) for row in categories_results],
        'colors': ['#3b82f6', '#eab308', '#22c55e', '#ef4444', '#a855f7']
    }

    # Month options for chart filter (last 6 months)
    month_options = []
    base_total = base.year * 12 + (base.month - 1)
    for i in range(5, -1, -1):
        total = base_total - i
        y = total // 12
        m = total % 12 + 1
        value = f"{y:04d}-{m:02d}"
        label = f"{months_pt[m]}/{str(y)[-2:]}"
        month_options.append({'value': value, 'label': label})

    conn.close()

    return render_template('products/stock.html', 
                         products=products,
                         suppliers=suppliers,
                         stats=stats,
                         categories=categories,
                         active_category=category_filter,
                         active_search=search_query,
                         chart_entries_json=json.dumps(chart_entries_data),
                         chart_categories_json=json.dumps(chart_categories_data),
                         month_options=month_options,
                         active_page='products')

@products_bp.route('/products/charts')
def stock_charts():
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401

    user_id = session['id']
    month_filter = request.args.get('month', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    months_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

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

        # Daily entries for selected month
        chart_entries = {'dates': [], 'counts': []}
        if start_month and end_month:
            cursor.execute((
                "SELECT DATE(created_at) as date, COUNT(*) as total "
                "FROM products "
                "WHERE user_id = %s AND created_at >= %s AND created_at < %s "
                "GROUP BY DATE(created_at) "
                "ORDER BY date ASC"
            ), (user_id, start_month, end_month))
            results = cursor.fetchall()
            totals_map = {str(row['date']): int(row['total'] or 0) for row in results}
            days_in_month = (end_month - start_month).days
            for day in range(1, days_in_month + 1):
                d = date(start_month.year, start_month.month, day)
                chart_entries['dates'].append(d.strftime('%d/%m'))
                chart_entries['counts'].append(totals_map.get(str(d), 0))

            cursor.execute((
                "SELECT COALESCE(category, 'Sem Categoria') as category, SUM(quantity) as total "
                "FROM products "
                "WHERE user_id = %s AND created_at >= %s AND created_at < %s "
                "GROUP BY COALESCE(category, 'Sem Categoria') "
                "ORDER BY total DESC "
                "LIMIT 5"
            ), (user_id, start_month, end_month))
        else:
            chart_entries = {'dates': [], 'counts': []}
            cursor.execute((
                "SELECT COALESCE(category, 'Sem Categoria') as category, SUM(quantity) as total "
                "FROM products "
                "WHERE user_id = %s "
                "GROUP BY COALESCE(category, 'Sem Categoria') "
                "ORDER BY total DESC "
                "LIMIT 5"
            ), (user_id,))
        categories_results = cursor.fetchall()
    else:
        # Last 6 months (monthly)
        cursor.execute((
            "SELECT DATE_FORMAT(created_at, '%Y-%m') as month_year, COUNT(*) as total "
            "FROM products "
            "WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH) "
            "GROUP BY DATE_FORMAT(created_at, '%Y-%m') "
            "ORDER BY month_year ASC "
        ), (user_id,))
        results = cursor.fetchall()
        totals_map = {row['month_year']: int(row['total'] or 0) for row in results}
        chart_entries = {'dates': [], 'counts': []}
        base = date.today().replace(day=1)
        base_total = base.year * 12 + (base.month - 1)
        for i in range(5, -1, -1):
            total = base_total - i
            y = total // 12
            m = total % 12 + 1
            key = f"{y:04d}-{m:02d}"
            label = f"{months_pt[m]}/{str(y)[-2:]}"
            chart_entries['dates'].append(label)
            chart_entries['counts'].append(totals_map.get(key, 0))

        cursor.execute((
            "SELECT COALESCE(category, 'Sem Categoria') as category, SUM(quantity) as total "
            "FROM products "
            "WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH) "
            "GROUP BY COALESCE(category, 'Sem Categoria') "
            "ORDER BY total DESC "
            "LIMIT 5"
        ), (user_id,))
        categories_results = cursor.fetchall()

    chart_categories = {
        'labels': [row['category'] for row in categories_results],
        'values': [int(row['total'] or 0) for row in categories_results],
        'colors': ['#3b82f6', '#eab308', '#22c55e', '#ef4444', '#a855f7']
    }

    cursor.close()
    conn.close()

    return {'entries': chart_entries, 'categories': chart_categories}

@products_bp.route('/products/add', methods=['POST'])
def add_product():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
        
    user_id = session['id']
    name = request.form.get('name')
    if name: name = name.strip().title()
    
    sku = request.form.get('sku')
    category_id = request.form.get('category_id') or None
    supplier_id = request.form.get('supplier_id') or None
    
    # Prices & Stock
    cost_price = request.form.get('cost_price', '0').replace(',', '.')
    sell_price = request.form.get('price', '0').replace(',', '.') 
    stock_quantity = request.form.get('quantity', '0')
    
    # Handle Multiple Images
    images_list = []
    
    # 1. Handle File Uploads
    if 'image_files' in request.files:
        files = request.files.getlist('image_files')
        upload_folder = os.path.join('static', 'uploads', 'products')
        os.makedirs(upload_folder, exist_ok=True)
        
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                name_base, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                final_filename = f"{name_base}_{timestamp}{ext}"
                file_path = os.path.join(upload_folder, final_filename)
                file.save(file_path)
                images_list.append(f"/static/uploads/products/{final_filename}")

    # 2. Handle External URLs
    urls = request.form.getlist('image_urls')
    for url in urls:
        if url.strip():
            images_list.append(url.strip())
            
    # Fallback/Legacy support (single file)
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_folder = os.path.join('static', 'uploads', 'products')
            os.makedirs(upload_folder, exist_ok=True)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            final_filename = f"{name}_{timestamp}{ext}"
            file_path = os.path.join(upload_folder, final_filename)
            file.save(file_path)
            images_list.append(f"/static/uploads/products/{final_filename}")

    # Fallback/Legacy support (single URL)
    single_url = request.form.get('image_url')
    if single_url and single_url.strip():
        images_list.append(single_url.strip())

    images_json = json.dumps(images_list) if images_list else None

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (user_id, name, sku, category_id, supplier_id, cost_price, sell_price, quantity, images, min_quantity) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, name, sku, category_id, supplier_id, cost_price, sell_price, stock_quantity, images_json, request.form.get('min_quantity') or 0)
        )
        conn.commit()
        flash('Produto adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar o produto: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('products.list_products'))

@products_bp.route('/products/supplier/add', methods=['POST'])
def add_supplier():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
        
    user_id = session['id']
    name = request.form.get('name')
    if name: name = name.strip().title()
    
    phone = request.form.get('phone')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json
    
    if not name:
        if is_ajax: return {'error': 'Nome é obrigatório'}, 400
        flash('Informe o nome do fornecedor.', 'error')
        return redirect(url_for('products.list_products'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO suppliers (user_id, name, phone) VALUES (%s, %s, %s)", (user_id, name, phone))
        conn.commit()
        new_id = cursor.lastrowid
        
        if is_ajax:
            return {'success': True, 'id': new_id, 'name': name}

        flash('Fornecedor adicionado com sucesso!', 'success')
    except Exception as e:
        if is_ajax: return {'error': str(e)}, 500
        flash(f'Erro ao adicionar o fornecedor: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('products.list_products'))

# --- CATEGORIES CRUD ---

@products_bp.route('/categories', methods=['GET'])
def list_categories():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM categories WHERE user_id = %s ORDER BY name", (user_id,))
    categories = cursor.fetchall()
    
    conn.close()
    
    return render_template('products/categories.html', categories=categories, active_page='products')

@products_bp.route('/categories/add', methods=['POST'])
def add_category():
    if 'id' not in session:
        return {'error': 'Unauthorized'}, 401
        
    user_id = session['id']
    name = request.form.get('name')
    if name: name = name.strip().title()
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json

    if not name:
        msg = 'Informe o nome da categoria.'
        if is_ajax: return {'error': msg}, 400
        flash(msg)
        return redirect(url_for('products.list_categories'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO categories (user_id, name) VALUES (%s, %s)", (user_id, name))
        conn.commit()
        new_id = cursor.lastrowid
        
        if is_ajax:
            return {'success': True, 'id': new_id, 'name': name}
            
        flash('Categoria adicionada com sucesso!', 'success')
    except Exception as e:
        if is_ajax: return {'error': str(e)}, 500
        flash(f'Erro ao adicionar a categoria: {str(e)}', 'error')
    finally:
        conn.close()

    return redirect(url_for('products.list_categories'))

@products_bp.route('/categories/edit/<int:id>', methods=['POST'])
def edit_category(id):
    if 'id' not in session: return redirect(url_for('auth.home'))
    user_id = session['id']
    name = request.form.get('name')
    if name: name = name.strip().title()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET name = %s WHERE id = %s AND user_id = %s", (name, id, user_id))
    conn.commit()
    conn.close()
    
    flash('Categoria atualizada com sucesso!', 'success')
    return redirect(url_for('products.list_categories'))

@products_bp.route('/categories/delete/<int:id>', methods=['POST'])
def delete_category(id):
    if 'id' not in session: return redirect(url_for('auth.home'))
    user_id = session['id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM categories WHERE id = %s AND user_id = %s", (id, user_id))
        conn.commit()
        flash('Categoria excluída com sucesso!', 'success')
    except Exception as e:
        flash('Erro ao excluir a categoria: ela pode estar em uso.', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('products.list_categories'))

@products_bp.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))
        
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM products WHERE id = %s AND user_id = %s", (id, user_id))
    
    conn.commit()
    conn.close()
    
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('products.list_products'))

@products_bp.route('/products/edit/<int:id>', methods=['POST'])
def edit_product(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))
        
    user_id = session['id']
    name = request.form.get('name')
    if name: name = name.strip().title()
    
    category_id = request.form.get('category_id') or None
    supplier_id = request.form.get('supplier_id') or None
    cost_price = request.form.get('cost_price', '0').replace(',', '.')
    # Form field is named 'price', db column is 'sell_price'
    sell_price = request.form.get('price', '0').replace(',', '.') 
    quantity = request.form.get('quantity') or 0
    min_quantity = request.form.get('min_quantity') or 0
    
    # Handle Multiple Images
    images_list = []
    
    # 1. Handle File Uploads (New files)
    if 'image_files' in request.files:
        files = request.files.getlist('image_files')
        upload_folder = os.path.join('static', 'uploads', 'products')
        os.makedirs(upload_folder, exist_ok=True)
        
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                name_base, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                final_filename = f"{name_base}_{timestamp}{ext}"
                file_path = os.path.join(upload_folder, final_filename)
                file.save(file_path)
                images_list.append(f"/static/uploads/products/{final_filename}")

    # 2. Handle Existing/New URLs
    urls = request.form.getlist('image_urls')
    for url in urls:
        if url.strip():
            images_list.append(url.strip())

    # Fallback to legacy single file
    if 'image_file' in request.files:
         file = request.files['image_file']
         if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_folder = os.path.join('static', 'uploads', 'products')
            os.makedirs(upload_folder, exist_ok=True)
            name_base, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            final_filename = f"{name_base}_{timestamp}{ext}"
            file_path = os.path.join(upload_folder, final_filename)
            file.save(file_path)
            images_list.append(f"/static/uploads/products/{final_filename}")

    # Fallback/Legacy support (single URL from old form if any)
    single_url = request.form.get('image_url')
    if single_url and single_url.strip() and single_url not in images_list:
        images_list.append(single_url.strip())

    # If no images provided at all, we might want to keep existing? 
    # But usually a form submission includes all current state. 
    # If the user cleared all images, images_list will be empty, which is correct (delete all).
    
    images_json = json.dumps(images_list) if images_list else None

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE products SET name = %s, category_id = %s, supplier_id = %s, cost_price = %s, "
        "sell_price = %s, quantity = %s, min_quantity = %s, images = %s "
        "WHERE id = %s AND user_id = %s",
        (name, category_id, supplier_id, cost_price, sell_price, quantity, min_quantity, images_json, id, user_id)
    )
    
    conn.commit()
    conn.close()
    
    flash('Produto atualizado com sucesso!')
    return redirect(url_for('products.list_products'))

