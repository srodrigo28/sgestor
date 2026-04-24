from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from common.database import get_db_connection
from common.employees_schema import ensure_employees_schema

services_bp = Blueprint('services', __name__)

@services_bp.route('/services')
def list():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_employees_schema(cursor)
    conn.commit()
    
    # Fetch Services
    search = request.args.get('search', '')
    query = "SELECT * FROM services WHERE user_id = %s"
    params = [user_id]
    
    if search:
        query += " AND (name LIKE %s OR description LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term])
        
    query += " ORDER BY name"
    
    cursor.execute(query, tuple(params))
    services = cursor.fetchall()
    
    conn.close()
    
    return render_template('budgets/services.html', services=services, active_page='services')

@services_bp.route('/services/add', methods=['POST'])
def add():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
        
    user_id = session['id']
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    employee = request.form.get('employee')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    ensure_employees_schema(cursor)
    conn.commit()
    
    try:
        cursor.execute("""
            INSERT INTO services (user_id, name, description, price, employee)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, name, description, price, employee))
        conn.commit()
        flash('Serviço cadastrado com sucesso!')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao cadastrar serviço: {e}')
    finally:
        conn.close()
        
    return redirect(url_for('services.list'))

@services_bp.route('/services/edit/<int:id>', methods=['POST'])
def edit(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    employee = request.form.get('employee')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    ensure_employees_schema(cursor)
    conn.commit()
    
    try:
        # Verify ownership
        cursor.execute("SELECT id FROM services WHERE id = %s AND user_id = %s", (id, user_id))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE services 
                SET name = %s, description = %s, price = %s, employee = %s
                WHERE id = %s
            """, (name, description, price, employee, id))
            conn.commit()
            flash('Serviço atualizado com sucesso!')
        else:
            flash('Serviço não encontrado ou sem permissão.')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao atualizar serviço: {e}')
    finally:
        conn.close()
        
    return redirect(url_for('services.list'))

@services_bp.route('/services/delete/<int:id>', methods=['POST'])
def delete(id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verify ownership and delete
        cursor.execute("DELETE FROM services WHERE id = %s AND user_id = %s", (id, user_id))
        conn.commit()
        if cursor.rowcount > 0:
            flash('Serviço excluído com sucesso!')
        else:
            flash('Serviço não encontrado.')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao excluir serviço: {e}')
    finally:
        conn.close()
        
    return redirect(url_for('services.list'))

