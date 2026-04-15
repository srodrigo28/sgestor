from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import json
from common.database import get_db_connection

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/schedule')
def index():
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    selected_client_id = request.args.get('client_id', type=int)
    open_schedule_modal = request.args.get('open') == '1'
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM clients WHERE user_id = %s ORDER BY name", (user_id,))
    clients = cursor.fetchall()
    preselected_client = next((client for client in clients if client['id'] == selected_client_id), None)

    cursor.execute("""
        SELECT a.*, c.name as client_name
        FROM appointments a
        LEFT JOIN clients c ON a.client_id = c.id
        WHERE a.user_id = %s
        ORDER BY a.start_time ASC
    """, (user_id,))
    appointments_db = cursor.fetchall()

    events = []
    for appt in appointments_db:
        color = '#3b82f6'
        if appt['status'] == 'completed':
            color = '#22c55e'
        elif appt['status'] == 'cancelled':
            color = '#ef4444'
        elif appt['status'] == 'no_show':
            color = '#f59e0b'

        display_title = f"{appt['client_name']} - {appt['title']}" if appt['client_name'] else appt['title']
        time_str = appt['start_time'].strftime('%H:%M')
        display_title = f"{time_str} {display_title}"

        events.append({
            'id': appt['id'],
            'title': display_title,
            'start': appt['start_time'].isoformat(),
            'end': appt['end_time'].isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'raw_title': appt['title'],
                'description': appt['description'],
                'client_id': appt['client_id'],
                'status': appt['status']
            }
        })

    conn.close()

    return render_template(
        'schedule/index.html',
        clients=clients,
        events_json=json.dumps(events),
        active_page='schedule',
        preselected_client_id=preselected_client['id'] if preselected_client else '',
        preselected_client_name=preselected_client['name'] if preselected_client else '',
        open_schedule_modal=open_schedule_modal,
    )

@schedule_bp.route('/schedule/add', methods=['POST'])
def add_appointment():
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    client_id = request.form.get('client_id') or None
    title = request.form.get('title')
    description = request.form.get('description')
    start_date = request.form.get('start_date')
    start_time = request.form.get('start_time')
    end_time_val = request.form.get('end_time')

    try:
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        if end_time_val:
             end_dt = datetime.strptime(f"{start_date} {end_time_val}", "%Y-%m-%d %H:%M")
             if end_dt < start_dt:
                 end_dt = end_dt.replace(day=end_dt.day + 1)
        else:
             from datetime import timedelta
             end_dt = start_dt + timedelta(hours=1)

    except ValueError:
        flash('Erro no formato de data/hora.')
        return redirect(url_for('schedule.index'))

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (user_id, client_id, title, description, start_time, end_time, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'scheduled')
        """, (user_id, client_id, title, description, start_dt, end_dt))
        conn.commit()
        flash('Agendamento criado com sucesso!')
    except Exception as e:
        flash(f'Erro ao criar agendamento: {str(e)}')
    finally:
        conn.close()

    return redirect(url_for('schedule.index'))

@schedule_bp.route('/schedule/edit/<int:id>', methods=['POST'])
def edit_appointment(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    client_id = request.form.get('client_id') or None
    title = request.form.get('title')
    description = request.form.get('description')
    status = request.form.get('status')
    start_date = request.form.get('start_date')
    start_time = request.form.get('start_time')
    end_time_val = request.form.get('end_time')

    try:
        start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        if end_time_val:
             end_dt = datetime.strptime(f"{start_date} {end_time_val}", "%Y-%m-%d %H:%M")
        else:
             from datetime import timedelta
             end_dt = start_dt + timedelta(hours=1)
    except ValueError:
        flash('Erro no formato de data/hora.')
        return redirect(url_for('schedule.index'))

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments
            SET client_id=%s, title=%s, description=%s, start_time=%s, end_time=%s, status=%s
            WHERE id=%s AND user_id=%s
        """, (client_id, title, description, start_dt, end_dt, status, id, user_id))
        conn.commit()
        flash('Agendamento atualizado!')
    except Exception as e:
        flash(f'Erro ao atualizar: {str(e)}')
    finally:
        conn.close()

    return redirect(url_for('schedule.index'))

@schedule_bp.route('/schedule/delete/<int:id>', methods=['POST'])
def delete_appointment(id):
    if 'id' not in session:
        return redirect(url_for('auth.home'))

    user_id = session['id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id=%s AND user_id=%s", (id, user_id))
    conn.commit()
    conn.close()
    flash('Agendamento removido!')
    return redirect(url_for('schedule.index'))
