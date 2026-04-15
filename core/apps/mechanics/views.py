from datetime import datetime
import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from common.database import get_db_connection


mechanics_bp = Blueprint('mechanics', __name__)
ALLOWED_ROLES = {'admin', 'oficina', 'atendimentos'}


def _ensure_mechanics_schema(cursor):
    try:
        cursor.execute("ALTER TABLE mechanics ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1")
    except Exception:
        pass


def _parse_status_filter(raw_value):
    value = (raw_value or 'active').strip().lower()
    return value if value in {'active', 'inactive', 'all'} else 'active'


def _access_denied():
    flash('Esse cadastro de equipe está disponível apenas para oficina, atendimento e administração.', 'error')
    return redirect(url_for('tasks.dashboard'))


def _ensure_access():
    if 'id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') not in ALLOWED_ROLES:
        return _access_denied()
    return None


@mechanics_bp.route('/mechanics')
def list_mechanics():
    access_response = _ensure_access()
    if access_response:
        return access_response

    user_id = session['id']
    search = request.args.get('search', '')
    status_filter = _parse_status_filter(request.args.get('status'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    _ensure_mechanics_schema(cursor)

    query = "SELECT * FROM mechanics WHERE user_id = %s"
    params = [user_id]

    if status_filter == 'active':
        query += " AND COALESCE(is_active, 1) = 1"
    elif status_filter == 'inactive':
        query += " AND COALESCE(is_active, 1) = 0"

    if search:
        query += " AND name LIKE %s"
        params.append(f"%{search}%")

    query += " ORDER BY name ASC"

    cursor.execute(query, tuple(params))
    mechanics = cursor.fetchall()
    conn.close()

    return render_template('mechanics/index.html', mechanics=mechanics, search=search, status_filter=status_filter)


@mechanics_bp.route('/mechanics/create', methods=['GET', 'POST'])
def create():
    access_response = _ensure_access()
    if access_response:
        return access_response

    if request.method == 'POST':
        user_id = session['id']
        name = request.form['name'].strip().title()
        phone = request.form.get('phone')
        birth_date = request.form.get('birth_date') or None
        hiring_date = request.form.get('hiring_date') or None
        experience_years = request.form.get('experience_years') or 0

        addr_cep = request.form.get('addr_cep')

        addr_street = request.form.get('addr_street')
        if addr_street:
            addr_street = addr_street.strip().title()

        addr_number = request.form.get('addr_number')

        addr_district = request.form.get('addr_district')
        if addr_district:
            addr_district = addr_district.strip().title()

        addr_city = request.form.get('addr_city')
        if addr_city:
            addr_city = addr_city.strip().title()

        addr_state = request.form.get('addr_state')
        if addr_state:
            addr_state = addr_state.strip().upper()

        address_reference = request.form.get('address_reference')
        if address_reference:
            address_reference = address_reference.strip().title()

        emergency_contact = request.form.get('emergency_contact')
        if emergency_contact:
            emergency_contact = emergency_contact.strip().title()

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
            _ensure_mechanics_schema(cursor)
            cursor.execute(
                """
                INSERT INTO mechanics
                (user_id, name, phone, birth_date, hiring_date, experience_years, photo_path, is_active,
                 address_cep, address_street, address_number, address_reference,
                 address_district, address_city, address_state, emergency_contact)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    name,
                    phone,
                    birth_date,
                    hiring_date,
                    experience_years,
                    photo_path,
                    1,
                    addr_cep,
                    addr_street,
                    addr_number,
                    address_reference,
                    addr_district,
                    addr_city,
                    addr_state,
                    emergency_contact,
                ),
            )
            conn.commit()
            flash('Funcionário cadastrado com sucesso!', 'success')
            return redirect(url_for('mechanics.list_mechanics'))
        except Exception as e:
            flash(f'Erro ao cadastrar funcionário: {str(e)}', 'error')
        finally:
            conn.close()

    return render_template('mechanics/create.html')


@mechanics_bp.route('/mechanics/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    access_response = _ensure_access()
    if access_response:
        return access_response

    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM mechanics WHERE id = %s AND user_id = %s", (id, user_id))
    mechanic = cursor.fetchone()

    if not mechanic:
        conn.close()
        flash('Funcionário não encontrado.', 'error')
        return redirect(url_for('mechanics.list_mechanics'))

    if request.method == 'POST':
        name = request.form['name'].strip().title()
        phone = request.form.get('phone')
        birth_date = request.form.get('birth_date') or None
        hiring_date = request.form.get('hiring_date') or None
        experience_years = request.form.get('experience_years') or 0

        addr_cep = request.form.get('addr_cep')

        addr_street = request.form.get('addr_street')
        if addr_street:
            addr_street = addr_street.strip().title()

        addr_number = request.form.get('addr_number')

        addr_district = request.form.get('addr_district')
        if addr_district:
            addr_district = addr_district.strip().title()

        addr_city = request.form.get('addr_city')
        if addr_city:
            addr_city = addr_city.strip().title()

        addr_state = request.form.get('addr_state')
        if addr_state:
            addr_state = addr_state.strip().upper()

        address_reference = request.form.get('address_reference')
        if address_reference:
            address_reference = address_reference.strip().title()

        emergency_contact = request.form.get('emergency_contact')
        if emergency_contact:
            emergency_contact = emergency_contact.strip().title()

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
            _ensure_mechanics_schema(cursor)
            cursor.execute(
                """
                UPDATE mechanics SET
                name=%s, phone=%s, birth_date=%s, hiring_date=%s, experience_years=%s, photo_path=%s,
                address_cep=%s, address_street=%s, address_number=%s, address_reference=%s,
                address_district=%s, address_city=%s, address_state=%s, emergency_contact=%s
                WHERE id=%s AND user_id=%s
                """,
                (
                    name,
                    phone,
                    birth_date,
                    hiring_date,
                    experience_years,
                    new_photo_path,
                    addr_cep,
                    addr_street,
                    addr_number,
                    address_reference,
                    addr_district,
                    addr_city,
                    addr_state,
                    emergency_contact,
                    id,
                    user_id,
                ),
            )
            conn.commit()
            flash('Funcionário atualizado com sucesso!', 'success')
            return redirect(url_for('mechanics.list_mechanics'))
        except Exception as e:
            flash(f'Erro ao atualizar funcionário: {str(e)}', 'error')
        finally:
            conn.close()

    conn.close()
    return render_template('mechanics/edit.html', mechanic=mechanic)


@mechanics_bp.route('/mechanics/toggle_status/<int:id>', methods=['POST'])
def toggle_status(id):
    access_response = _ensure_access()
    if access_response:
        return access_response

    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        _ensure_mechanics_schema(cursor)
        cursor.execute("SELECT id, name, is_active FROM mechanics WHERE id = %s AND user_id = %s", (id, user_id))
        mechanic = cursor.fetchone()
        if not mechanic:
            flash('Funcionário não encontrado.', 'error')
            return redirect(url_for('mechanics.list_mechanics'))

        new_status = 0 if int(mechanic.get('is_active', 1) or 0) == 1 else 1
        cursor.execute("UPDATE mechanics SET is_active = %s WHERE id = %s AND user_id = %s", (new_status, id, user_id))
        conn.commit()
        flash('Funcionário reativado com sucesso!' if new_status == 1 else 'Funcionário desabilitado com sucesso!', 'success')
    except Exception:
        flash('Erro ao atualizar status do funcionário.', 'error')
    finally:
        conn.close()

    return redirect(url_for('mechanics.list_mechanics'))
