from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from common.database import get_db_connection
from datetime import datetime, timedelta

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/dashboard')
def dashboard():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Stats Counts
        cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = %s", (user_id,))
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'feito'", (user_id,))
        done = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'fazendo'", (user_id,))
        doing = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'a_fazer'", (user_id,))
        todo = cursor.fetchone()['count']
        
        # Chart Data (Last 7 Days) - Created Tasks
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM tasks 
            WHERE user_id = %s 
              AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY) 
            GROUP BY DATE(created_at) 
            ORDER BY date ASC
        """, (user_id,))
        results = cursor.fetchall()
    finally:
        conn.close()
    
    # Process Chart Data (Fill missing days)
    chart_data = {'dates': [], 'counts': []}
    dates_map = {str(row['date']): row['count'] for row in results}
    
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        display_date = date.strftime('%d/%m')
        
        chart_data['dates'].append(display_date)
        chart_data['counts'].append(dates_map.get(date_str, 0))
    
    stats = {
        'total': total,
        'done': done,
        'doing': doing,
        'todo': todo
    }
        
    return render_template('dashboard.html', stats=stats, chart_data=chart_data)

@tasks_bp.route('/tasks/add', methods=['POST'])
def create_task():
    if 'id' not in session:
        return redirect(url_for('auth.login'))
        
    title = request.form['title']
    description = request.form.get('description', '')
    category = request.form.get('category', 'Pessoal')
    due_date_raw = (request.form.get('due_date') or '').strip()
    due_date = due_date_raw if due_date_raw else None
    user_id = session['id']
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (user_id, title, description, category, due_date) VALUES (%s, %s, %s, %s, %s)',
            (user_id, title, description, category, due_date)
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
    
    category = request.args.get('category')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Base query
    query = 'SELECT * FROM tasks WHERE user_id = %s'
    params = [session['id']]
    
    # Filter by category
    if category and category != 'Todas as Categorias':
        query += ' AND category = %s'
        params.append(category)

    # Filter by search
    if search:
        query += ' AND (title LIKE %s OR description LIKE %s)'
        params.extend([f'%{search}%', f'%{search}%'])
        
    # Count total for pagination
    count_sql = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
    cursor.execute(count_sql, tuple(params))
    total_tasks = cursor.fetchone()['total']
    total_pages = (total_tasks + per_page - 1) // per_page
    
    # Add sorting and pagination
    query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
    params.extend([per_page, offset])
    
    cursor.execute(query, tuple(params))
    tasks = cursor.fetchall()

    # --- Dashboard Integration (Stats & Charts) ---
    
    # 1. Stats Counts
    cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = %s", (session['id'],))
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'feito'", (session['id'],))
    done = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'fazendo'", (session['id'],))
    doing = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'a_fazer'", (session['id'],))
    todo = cursor.fetchone()['count']
    
    stats = {
        'total': total,
        'done': done,
        'doing': doing,
        'todo': todo
    }

    # 2. Chart Data (Last 7 Days) - Created Tasks
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM tasks 
        WHERE user_id = %s 
          AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY) 
        GROUP BY DATE(created_at) 
        ORDER BY date ASC
    """, (session['id'],))
    results = cursor.fetchall()
    
    # Process Chart Data (Fill missing days)
    chart_data = {'dates': [], 'counts': []}
    dates_map = {str(row['date']): row['count'] for row in results}
    
    for i in range(6, -1, -1):
        date_obj = datetime.now() - timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d')
        display_date = date_obj.strftime('%d/%m')
        
        chart_data['dates'].append(display_date)
        chart_data['counts'].append(dates_map.get(date_str, 0))

    conn.close()
    
    # 3. JSON Serialization for Frontend
    import json
    chart_data_json = json.dumps(chart_data)
    stats_json = json.dumps(stats)
    
    return render_template('tasks.html', tasks=tasks, active_category=category if category else 'Todas as Categorias', 
                         page=page, total_pages=total_pages, per_page=per_page, search=search,
                         stats=stats, chart_data_json=chart_data_json, stats_json=stats_json)

@tasks_bp.route('/tasks/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))
        
    title = request.form['title']
    description = request.form.get('description', '')
    category = request.form.get('category', 'Pessoal')
    status = request.form.get('status', 'a_fazer')
    due_date_raw = (request.form.get('due_date') or '').strip()
    due_date = due_date_raw if due_date_raw else None
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT status, completed_at FROM tasks WHERE id = %s AND user_id = %s',
        (task_id, session['id'])
    )
    current_task = cursor.fetchone()

    if not current_task:
        conn.close()
        flash('Tarefa não encontrada ou sem permissão.')
        return redirect(url_for('tasks.list'))

    existing_completed_at = current_task.get('completed_at')

    # Preserve completed_at when remaining "feito". Set when transitioning to "feito". Clear otherwise.
    if status == 'feito':
        final_completed_at = existing_completed_at if existing_completed_at else datetime.now()
    else:
        final_completed_at = None

    cursor.execute(
        'UPDATE tasks SET title = %s, description = %s, category = %s, status = %s, completed_at = %s, due_date = %s WHERE id = %s AND user_id = %s',
        (title, description, category, status, final_completed_at, due_date, task_id, session['id'])
    )
    conn.commit()
    conn.close()
    
    flash('Tarefa atualizada com sucesso!')
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

