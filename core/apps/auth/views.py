from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from common.database import get_db_connection
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/')
def home():
    if 'id' in session:
        return redirect(url_for('tasks.dashboard'))
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # User lookup by email only
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        valid = False
        if user:
            stored_password = user['password']
            # 1. Check if it's a known hash format (Werkzeug default hashes start with scrypt: or pbkdf2:)
            if stored_password.startswith(('scrypt:', 'pbkdf2:')):
                if check_password_hash(stored_password, password):
                    valid = True
            # 2. Legacy fallback for plain text
            elif stored_password == password:
                valid = True
                # Auto-migrate to hash
                new_hash = generate_password_hash(password)
                cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_hash, user['id']))
                conn.commit()

        if valid:
            session['id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user.get('role', 'pessoal')
            session['phone'] = user.get('phone', '')
            session['store_name'] = user.get('store_name', '')
            session['logo'] = user.get('logo') or None
            session['cnpj'] = user.get('cnpj') or None
            session['address'] = user.get('address') or None
            
            # Load detailed address
            session['addr_cep'] = user.get('address_cep', '')
            session['addr_street'] = user.get('address_street', '')
            session['addr_number'] = user.get('address_number', '')
            session['addr_district'] = user.get('address_district', '')
            session['addr_city'] = user.get('address_city', '')
            session['addr_state'] = user.get('address_state', '')
            
            return redirect(url_for('tasks.dashboard'))
        else:
            flash("Login inválido. Verifique suas credenciais.", "error")
            return redirect(url_for('auth.home'))
            
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@auth_bp.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    phone = request.form.get('phone', '')
    role = request.form.get('role', 'pessoal')

    # Validate role
    if role not in ['pessoal', 'loja', 'oficina', 'atendimentos']:
        role = 'pessoal'
    
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, password, phone, role) VALUES (%s, %s, %s, %s, %s)',
            (name, email, hashed_password, phone, role)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        session['id'] = user_id
        session['name'] = name
        session['email'] = email
        session['role'] = role
        return redirect(url_for('tasks.dashboard'))
        
    except mysql.connector.IntegrityError:
        flash("Email já cadastrado. Tente fazer login.", "error")
        return redirect(url_for('auth.home'))
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['id']
    name = request.form['name']
    email = request.form['email']
    phone = request.form.get('phone', '')
    cnpj = request.form.get('cnpj', '')
    store_name = request.form.get('store_name', '')
    
    # Detailed Address Fields
    addr_cep = request.form.get('addr_cep', '')
    addr_street = request.form.get('addr_street', '')
    addr_number = request.form.get('addr_number', '')
    addr_district = request.form.get('addr_district', '')
    addr_city = request.form.get('addr_city', '')
    addr_state = request.form.get('addr_state', '')
    
    # Construct Full Address for backward compatibility and display
    address_parts = []
    if addr_street: address_parts.append(addr_street)
    if addr_number: address_parts.append(addr_number)
    if addr_district: address_parts.append(addr_district)
    if addr_city and addr_state: address_parts.append(f"{addr_city}/{addr_state}")
    if addr_cep: address_parts.append(f"CEP: {addr_cep}")
    
    full_address = " - ".join(address_parts)
    
    password = request.form.get('password')
    
    # Handle Logo Upload
    logo_path = None
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(os.getcwd(), 'static', 'uploads', 'logos')
            os.makedirs(upload_folder, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            final_filename = f"{user_id}_{timestamp}_{filename}"
            
            file.save(os.path.join(upload_folder, final_filename))
            logo_path = f"/static/uploads/logos/{final_filename}"
            
            # Update Session Logo immediately
            session['logo'] = logo_path
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Build Query Dynamically based on logo presence and password
        fields = [
            "name = %s", "email = %s", "phone = %s", "cnpj = %s", "store_name = %s", "address = %s",
            "address_cep = %s", "address_street = %s", "address_number = %s",
            "address_district = %s", "address_city = %s", "address_state = %s"
        ]
        params = [
            name, email, phone, cnpj, store_name, full_address,
            addr_cep, addr_street, addr_number, addr_district, addr_city, addr_state
        ]
        
        if password:
            fields.append("password = %s")
            params.append(generate_password_hash(password))
            
        if logo_path:
            fields.append("logo = %s")
            params.append(logo_path)
            
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(query, tuple(params))
            
        conn.commit()
        
        # Update session
        session['name'] = name
        session['email'] = email
        session['phone'] = phone
        session['cnpj'] = cnpj
        session['store_name'] = store_name
        session['address'] = full_address
        
        # Update detailed address in session
        session['addr_cep'] = addr_cep
        session['addr_street'] = addr_street
        session['addr_number'] = addr_number
        session['addr_district'] = addr_district
        session['addr_city'] = addr_city
        session['addr_state'] = addr_state
        
        if logo_path:
            session['logo'] = logo_path
        
        flash('Perfil atualizado com sucesso!')
        
    except mysql.connector.IntegrityError:
        flash('Erro: Este email já está em uso por outro usuário.')
    finally:
        conn.close()
        
    # Redirect back to previous page or dashboard
    return redirect(request.referrer or url_for('tasks.dashboard'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.home'))


