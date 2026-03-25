from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from common.database import get_db_connection
from werkzeug.utils import secure_filename
import os
from datetime import datetime

mechanics_bp = Blueprint('mechanics', __name__)

@mechanics_bp.route('/mechanics')
def list_mechanics():
    if 'id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['id']
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM mechanics WHERE user_id = %s"
    params = [user_id]
    
    if search:
        query += " AND name LIKE %s"
        params.append(f"%{search}%")
        
    query += " ORDER BY name ASC"
    
    cursor.execute(query, tuple(params))
    mechanics = cursor.fetchall()
    conn.close()
    
    return render_template('mechanics/index.html', mechanics=mechanics, search=search)

@mechanics_bp.route('/mechanics/create', methods=['GET', 'POST'])
def create():
    if 'id' not in session:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        user_id = session['id']
        name = request.form['name'].strip().title()
        phone = request.form.get('phone')
        birth_date = request.form.get('birth_date') or None
        hiring_date = request.form.get('hiring_date') or None
        experience_years = request.form.get('experience_years') or 0
        
        # Address & Contact
        addr_cep = request.form.get('addr_cep')
        
        addr_street = request.form.get('addr_street')
        if addr_street: addr_street = addr_street.strip().title()
        
        addr_number = request.form.get('addr_number')
        
        addr_district = request.form.get('addr_district')
        if addr_district: addr_district = addr_district.strip().title()
        
        addr_city = request.form.get('addr_city')
        if addr_city: addr_city = addr_city.strip().title()
        
        addr_state = request.form.get('addr_state')
        if addr_state: addr_state = addr_state.strip().upper()
        
        address_reference = request.form.get('address_reference')
        if address_reference: address_reference = address_reference.strip().title()
        
        emergency_contact = request.form.get('emergency_contact')
        if emergency_contact: emergency_contact = emergency_contact.strip().title()
        
        # Photo
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(os.getcwd(), 'static', 'uploads', 'mechanics')
                os.makedirs(upload_folder, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                final_filename = f"{user_id}_{timestamp}_{filename}"
                
                file.save(os.path.join(upload_folder, final_filename))
                photo_path = f"/static/uploads/mechanics/{final_filename}"
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mechanics 
                (user_id, name, phone, birth_date, hiring_date, experience_years, photo_path, 
                 address_cep, address_street, address_number, address_reference, 
                 address_district, address_city, address_state, emergency_contact)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, phone, birth_date, hiring_date, experience_years, photo_path,
                  addr_cep, addr_street, addr_number, address_reference,
                  addr_district, addr_city, addr_state, emergency_contact))
            conn.commit()
            flash('Mecânico cadastrado com sucesso!', 'success')
            return redirect(url_for('mechanics.list_mechanics'))
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'error')
        finally:
            conn.close()
            
    return render_template('mechanics/create.html')

@mechanics_bp.route('/mechanics/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check ownership
    cursor.execute("SELECT * FROM mechanics WHERE id = %s AND user_id = %s", (id, user_id))
    mechanic = cursor.fetchone()
    
    if not mechanic:
        conn.close()
        flash('Mecânico não encontrado.', 'error')
        return redirect(url_for('mechanics.list_mechanics'))
        
    if request.method == 'POST':
        name = request.form['name'].strip().title()
        phone = request.form.get('phone')
        birth_date = request.form.get('birth_date') or None
        hiring_date = request.form.get('hiring_date') or None
        experience_years = request.form.get('experience_years') or 0
        
        # Address & Contact
        addr_cep = request.form.get('addr_cep')
        
        addr_street = request.form.get('addr_street')
        if addr_street: addr_street = addr_street.strip().title()
        
        addr_number = request.form.get('addr_number')
        
        addr_district = request.form.get('addr_district')
        if addr_district: addr_district = addr_district.strip().title()
        
        addr_city = request.form.get('addr_city')
        if addr_city: addr_city = addr_city.strip().title()
        
        addr_state = request.form.get('addr_state')
        if addr_state: addr_state = addr_state.strip().upper()
        
        address_reference = request.form.get('address_reference')
        if address_reference: address_reference = address_reference.strip().title()
        
        emergency_contact = request.form.get('emergency_contact')
        if emergency_contact: emergency_contact = emergency_contact.strip().title()
        
        new_photo_path = mechanic['photo_path']
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(os.getcwd(), 'static', 'uploads', 'mechanics')
                os.makedirs(upload_folder, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                final_filename = f"{user_id}_{timestamp}_{filename}"
                
                file.save(os.path.join(upload_folder, final_filename))
                new_photo_path = f"/static/uploads/mechanics/{final_filename}"
        
        try:
            cursor.execute("""
                UPDATE mechanics SET
                name=%s, phone=%s, birth_date=%s, hiring_date=%s, experience_years=%s, photo_path=%s,
                address_cep=%s, address_street=%s, address_number=%s, address_reference=%s,
                address_district=%s, address_city=%s, address_state=%s, emergency_contact=%s
                WHERE id=%s AND user_id=%s
            """, (name, phone, birth_date, hiring_date, experience_years, new_photo_path,
                  addr_cep, addr_street, addr_number, address_reference, 
                  addr_district, addr_city, addr_state, emergency_contact,
                  id, user_id))
            conn.commit()
            flash('Mecânico atualizado com sucesso!', 'success')
            return redirect(url_for('mechanics.list_mechanics'))
        except Exception as e:
            flash(f'Erro ao atualizar: {str(e)}', 'error')
        finally:
            conn.close()
            
    conn.close()
    return render_template('mechanics/edit.html', mechanic=mechanic)

@mechanics_bp.route('/mechanics/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    if 'id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mechanics WHERE id = %s AND user_id = %s", (id, user_id))
        conn.commit()
        flash('Mecânico removido com sucesso!', 'success')
    except Exception as e:
        flash('Erro ao remover mecânico. Verifique se existem orçamentos vinculados.', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('mechanics.list_mechanics'))

