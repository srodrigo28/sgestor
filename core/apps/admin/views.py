from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from common.database import get_db_connection
from apps.auth.views import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../../templates/admin')

ROLE_OPTIONS = ['admin', 'oficina', 'loja', 'pessoal']
MENU_OPTIONS = [
    {'key': 'dashboard', 'label': 'Dashboard'},
    {'key': 'tasks', 'label': 'Tarefas'},
    {'key': 'financial', 'label': 'Financeiro'},
    {'key': 'products', 'label': 'Produtos'},
    {'key': 'clients', 'label': 'Clientes'},
    {'key': 'budgets', 'label': 'Orçamentos'},
    {'key': 'mechanics', 'label': 'Mecânicos'},
    {'key': 'services', 'label': 'Serviços'},
    {'key': 'schedule', 'label': 'Agendamentos'},
    {'key': 'admin_users', 'label': 'Usuários'},
]


def admin_required():
    return session.get('role') == 'admin'


@admin_bp.route('/users')
@login_required
def users():
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email, phone, role FROM users ORDER BY id DESC")
    users_list = cursor.fetchall()

    cursor.execute("SELECT role, menu_key, can_view FROM role_menu_permissions")
    rows = cursor.fetchall()
    conn.close()

    permissions = {role: {} for role in ROLE_OPTIONS}
    for row in rows:
        role = row['role']
        if role not in permissions:
            permissions[role] = {}
        permissions[role][row['menu_key']] = bool(row['can_view'])

    return render_template('admin/users.html',
                           users=users_list,
                           roles=ROLE_OPTIONS,
                           menus=MENU_OPTIONS,
                           permissions=permissions)


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    new_role = request.form.get('role', 'pessoal')
    if new_role not in ROLE_OPTIONS:
        flash('Perfil inválido.')
        return redirect(url_for('admin.users'))

    if user_id == session.get('id') and new_role != 'admin':
        flash('Você não pode remover seu próprio perfil de administrador.')
        return redirect(url_for('admin.users'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
    conn.commit()
    conn.close()

    flash('Perfil atualizado com sucesso!')
    return redirect(url_for('admin.users'))


@admin_bp.route('/permissions', methods=['POST'])
@login_required
def update_permissions():
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    for role in ROLE_OPTIONS:
        for menu in MENU_OPTIONS:
            key = f"perm_{role}_{menu['key']}"
            can_view = 1 if key in request.form else 0
            if role == 'admin':
                can_view = 1
            cursor.execute("""
                INSERT INTO role_menu_permissions (role, menu_key, can_view)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE can_view = VALUES(can_view)
            """, (role, menu['key'], can_view))

    conn.commit()
    conn.close()

    flash('Permissões atualizadas com sucesso!')
    return redirect(url_for('admin.users'))

