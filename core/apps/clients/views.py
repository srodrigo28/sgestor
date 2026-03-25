from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
from datetime import datetime, timedelta
from common.database import get_db_connection

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients')
def list():
    if 'id' not in session:
        return redirect(url_for('auth.home'))
    
    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Filters
        search_query = request.args.get('search')
        sector_filter = request.args.get('sector')
        
        # 1. Fetch Clients
        query = "SELECT * FROM clients WHERE user_id = %s"
        params = [user_id]
        
        if search_query:
            query += " AND (name LIKE %s OR cpf LIKE %s)"
            term = f"%{search_query}%"
            params.extend([term, term])
            
        if sector_filter:
            query += " AND sector = %s"
            params.append(sector_filter)
            
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, tuple(params))
        clients = cursor.fetchall()
        
        # 2. Fetch Stats
        # Total
        cursor.execute("SELECT COUNT(*) as total FROM clients WHERE user_id = %s", (user_id,))
        total_clients = cursor.fetchone()['total']
        
        # Weekly
        cursor.execute("SELECT COUNT(*) as total FROM clients WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)", (user_id,))
        new_weekly = cursor.fetchone()['total']
        
        # Monthly
        cursor.execute("SELECT COUNT(*) as total FROM clients WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)", (user_id,))
        new_monthly = cursor.fetchone()['total']
        
        stats = {
            'total_clients': total_clients,
            'new_weekly': new_weekly,
            'new_monthly': new_monthly
        }

        # 3. Chart Data: Growth (Last 7 Days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM clients 
            WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (user_id,))
        growth_results = cursor.fetchall()
        
        # Post-process to ensure all last 7 days exist
        today = datetime.now().date()
        last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        chart_growth_data = {'dates': [], 'counts': []}
        
        # Convert DB results to dict for easy lookup
        growth_map = {row['date']: row['count'] for row in growth_results if row['date']}
        
        for day in last_7_days:
            chart_growth_data['dates'].append(day.strftime('%d/%m'))
            chart_growth_data['counts'].append(growth_map.get(day, 0))

        # 4. Chart Data: Sectors
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
        
        # 5. Distinct Sectors for Filter
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
    
    # 1. Sanitize Inputs (Title Case)
    name = request.form.get('name')
    if name: name = name.strip().title()
    
    sector = request.form.get('sector')
    if sector: sector = sector.strip().title()
    
    cpf = request.form.get('cpf')
    phone1 = request.form.get('phone1')
    phone2 = request.form.get('phone2') or None
    
    # Address fields
    cep = request.form.get('cep')
    
    address = request.form.get('address')
    if address: address = address.strip().title()
    
    address_number = request.form.get('address_number')
    
    complement = request.form.get('complement')
    if complement: complement = complement.strip().title()
    
    neighborhood = request.form.get('neighborhood')
    if neighborhood: neighborhood = neighborhood.strip().title()
    
    city = request.form.get('city')
    if city: city = city.strip().title()
    
    state = request.form.get('state')
    if state: state = state.strip().upper()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO clients (
            user_id, name, sector, cpf, phone1, phone2, 
            cep, address, address_number, complement, neighborhood, city, state,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        cursor.execute(query, (
            user_id, name, sector, cpf, phone1, phone2, 
            cep, address, address_number, complement, neighborhood, city, state,
            datetime.now()
        ))
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
    
    # 1. Sanitize Inputs (Title Case)
    name = request.form.get('name')
    if name: name = name.strip().title()
    
    sector = request.form.get('sector')
    if sector: sector = sector.strip().title()
    
    cpf = request.form.get('cpf')
    phone1 = request.form.get('phone1')
    phone2 = request.form.get('phone2') or None
    
    # Address fields
    cep = request.form.get('cep')
    
    address = request.form.get('address')
    if address: address = address.strip().title()
    
    address_number = request.form.get('address_number')
    
    complement = request.form.get('complement')
    if complement: complement = complement.strip().title()
    
    neighborhood = request.form.get('neighborhood')
    if neighborhood: neighborhood = neighborhood.strip().title()
    
    city = request.form.get('city')
    if city: city = city.strip().title()
    
    state = request.form.get('state')
    if state: state = state.strip().upper()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check ownership
    cursor.execute("SELECT user_id FROM clients WHERE id = %s", (id,))
    client = cursor.fetchone()
    
    if client and client[0] == user_id:
        query = """
            UPDATE clients 
            SET name = %s, sector = %s, cpf = %s, phone1 = %s, phone2 = %s, 
                cep = %s, address = %s, address_number = %s, complement = %s, 
                neighborhood = %s, city = %s, state = %s,
                updated_at = %s
            WHERE id = %s
        """
        try:
            cursor.execute(query, (
                name, sector, cpf, phone1, phone2, 
                cep, address, address_number, complement, neighborhood, city, state,
                datetime.now(), id
            ))
            conn.commit()
            flash('Cliente atualizado com sucesso!')
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar cliente: {e}')
    else:
        flash('Cliente não encontrado ou permissão negada.')
        
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

