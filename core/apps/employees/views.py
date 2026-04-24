from datetime import datetime
import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from common.database import get_db_connection
from common.employees_schema import ensure_employees_schema


employees_bp = Blueprint('employees', __name__)
mechanics_legacy_bp = Blueprint('mechanics', __name__)
ALLOWED_ROLES = {'admin', 'oficina', 'atendimentos'}
LABOR_FIELDS = [
    'cpf',
    'rg',
    'rg_issuer',
    'rg_state',
    'rg_issue_date',
    'pis_pasep',
    'ctps_number',
    'ctps_series',
    'ctps_state',
    'mother_name',
    'father_name',
    'education_level',
    'marital_status',
    'salary',
    'num_dependents',
    'job_title',
    'contract_type',
    'work_schedule',
    'labor_notes',
]


def _optional_text(value, mode='raw'):
    value = (value or '').strip()
    if not value:
        return None
    if mode == 'title':
        return value.title()
    if mode == 'upper':
        return value.upper()
    return value


def _optional_int(value, default=None):
    value = (value or '').strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, parsed)


def _optional_money(value):
    value = (value or '').strip()
    if not value:
        return None
    normalized = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return round(float(normalized), 2)
    except (TypeError, ValueError):
        return None


def _labor_payload(form):
    return {
        'cpf': _optional_text(form.get('cpf')),
        'rg': _optional_text(form.get('rg')),
        'rg_issuer': _optional_text(form.get('rg_issuer'), 'upper'),
        'rg_state': _optional_text(form.get('rg_state'), 'upper'),
        'rg_issue_date': form.get('rg_issue_date') or None,
        'pis_pasep': _optional_text(form.get('pis_pasep')),
        'ctps_number': _optional_text(form.get('ctps_number')),
        'ctps_series': _optional_text(form.get('ctps_series')),
        'ctps_state': _optional_text(form.get('ctps_state'), 'upper'),
        'mother_name': _optional_text(form.get('mother_name'), 'title'),
        'father_name': _optional_text(form.get('father_name'), 'title'),
        'education_level': _optional_text(form.get('education_level')),
        'marital_status': _optional_text(form.get('marital_status')),
        'salary': _optional_money(form.get('salary')),
        'num_dependents': _optional_int(form.get('num_dependents'), 0),
        'job_title': _optional_text(form.get('job_title'), 'title'),
        'contract_type': _optional_text(form.get('contract_type')),
        'work_schedule': _optional_text(form.get('work_schedule')),
        'labor_notes': _optional_text(form.get('labor_notes')),
    }


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


@mechanics_legacy_bp.route('/mechanics')
def list_mechanics_legacy():
    return redirect(url_for('employees.list_employees', **request.args), code=301)


@mechanics_legacy_bp.route('/mechanics/create')
def create_legacy():
    return redirect(url_for('employees.create'), code=301)


@mechanics_legacy_bp.route('/mechanics/edit/<int:id>')
def edit_legacy(id):
    return redirect(url_for('employees.edit', id=id), code=301)


@mechanics_legacy_bp.route('/mechanics/toggle_status/<int:id>', methods=['POST'])
def toggle_status_legacy(id):
    return redirect(url_for('employees.toggle_status', id=id), code=307)


@employees_bp.route('/employees')
def list_employees():
    access_response = _ensure_access()
    if access_response:
        return access_response

    user_id = session['id']
    search = request.args.get('search', '')
    status_filter = _parse_status_filter(request.args.get('status'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_employees_schema(cursor)
    conn.commit()

    query = "SELECT * FROM employees WHERE user_id = %s"
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
    employees = cursor.fetchall()
    conn.close()

    return render_template('employees/index.html', employees=employees, search=search, status_filter=status_filter)


@employees_bp.route('/employees/create', methods=['GET', 'POST'])
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
            addr_state = addr_state.strip().title()

        address_reference = request.form.get('address_reference')
        if address_reference:
            address_reference = address_reference.strip().title()

        emergency_contact = request.form.get('emergency_contact')
        if emergency_contact:
            emergency_contact = emergency_contact.strip().title()

        labor_data = _labor_payload(request.form)

        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(os.getcwd(), 'static', 'uploads', 'employees')
                os.makedirs(upload_folder, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                final_filename = f"{user_id}_{timestamp}_{filename}"

                file.save(os.path.join(upload_folder, final_filename))
                photo_path = f"/static/uploads/employees/{final_filename}"

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            ensure_employees_schema(cursor)
            cursor.execute(
                """
                INSERT INTO employees
                (user_id, name, phone, birth_date, hiring_date, experience_years, photo_path, is_active,
                 address_cep, address_street, address_number, address_reference,
                 address_district, address_city, address_state, emergency_contact,
                 cpf, rg, rg_issuer, rg_state, rg_issue_date, pis_pasep, ctps_number, ctps_series, ctps_state,
                 mother_name, father_name, education_level, marital_status, salary, num_dependents,
                 job_title, contract_type, work_schedule, labor_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    *(labor_data[field] for field in LABOR_FIELDS),
                ),
            )
            conn.commit()
            flash('Funcionário cadastrado com sucesso!', 'success')
            return redirect(url_for('employees.list_employees'))
        except Exception as e:
            flash(f'Erro ao cadastrar funcionário: {str(e)}', 'error')
        finally:
            conn.close()

    return render_template('employees/create.html')


@employees_bp.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    access_response = _ensure_access()
    if access_response:
        return access_response

    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_employees_schema(cursor)
    conn.commit()

    cursor.execute("SELECT * FROM employees WHERE id = %s AND user_id = %s", (id, user_id))
    employee = cursor.fetchone()

    if not employee:
        conn.close()
        flash('Funcionário não encontrado.', 'error')
        return redirect(url_for('employees.list_employees'))

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
            addr_state = addr_state.strip().title()

        address_reference = request.form.get('address_reference')
        if address_reference:
            address_reference = address_reference.strip().title()

        emergency_contact = request.form.get('emergency_contact')
        if emergency_contact:
            emergency_contact = emergency_contact.strip().title()

        labor_data = _labor_payload(request.form)

        new_photo_path = employee['photo_path']
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(os.getcwd(), 'static', 'uploads', 'employees')
                os.makedirs(upload_folder, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                final_filename = f"{user_id}_{timestamp}_{filename}"

                file.save(os.path.join(upload_folder, final_filename))
                new_photo_path = f"/static/uploads/employees/{final_filename}"

        try:
            ensure_employees_schema(cursor)
            cursor.execute(
                """
                UPDATE employees SET
                name=%s, phone=%s, birth_date=%s, hiring_date=%s, experience_years=%s, photo_path=%s,
                address_cep=%s, address_street=%s, address_number=%s, address_reference=%s,
                address_district=%s, address_city=%s, address_state=%s, emergency_contact=%s,
                cpf=%s, rg=%s, rg_issuer=%s, rg_state=%s, rg_issue_date=%s, pis_pasep=%s,
                ctps_number=%s, ctps_series=%s, ctps_state=%s, mother_name=%s, father_name=%s,
                education_level=%s, marital_status=%s, salary=%s, num_dependents=%s,
                job_title=%s, contract_type=%s, work_schedule=%s, labor_notes=%s
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
                    *(labor_data[field] for field in LABOR_FIELDS),
                    id,
                    user_id,
                ),
            )
            conn.commit()
            flash('Funcionário atualizado com sucesso!', 'success')
            return redirect(url_for('employees.list_employees'))
        except Exception as e:
            flash(f'Erro ao atualizar funcionário: {str(e)}', 'error')
        finally:
            conn.close()

    conn.close()
    return render_template('employees/edit.html', employee=employee)


@employees_bp.route('/employees/toggle_status/<int:id>', methods=['POST'])
def toggle_status(id):
    access_response = _ensure_access()
    if access_response:
        return access_response

    user_id = session['id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        ensure_employees_schema(cursor)
        cursor.execute("SELECT id, name, is_active FROM employees WHERE id = %s AND user_id = %s", (id, user_id))
        employee = cursor.fetchone()
        if not employee:
            flash('Funcionário não encontrado.', 'error')
            return redirect(url_for('employees.list_employees'))

        new_status = 0 if int(employee.get('is_active', 1) or 0) == 1 else 1
        cursor.execute("UPDATE employees SET is_active = %s WHERE id = %s AND user_id = %s", (new_status, id, user_id))
        conn.commit()
        flash('Funcionário reativado com sucesso!' if new_status == 1 else 'Funcionário desabilitado com sucesso!', 'success')
    except Exception:
        flash('Erro ao atualizar status do funcionário.', 'error')
    finally:
        conn.close()

    return redirect(url_for('employees.list_employees'))
