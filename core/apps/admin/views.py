from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from common.database import get_db_connection
from common.financial_categories import (
    add_financial_category,
    delete_financial_category,
    list_financial_categories,
    rename_financial_category,
)
from apps.auth.views import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../../templates/admin')

ROLE_OPTIONS = ['admin', 'oficina', 'loja', 'atendimentos', 'pessoal']
ROLE_LABELS = {
    'admin': 'Administrador',
    'oficina': 'Oficina',
    'loja': 'Serviço',
    'atendimentos': 'Atendimentos',
    'pessoal': 'Pessoal',
}
MENU_OPTIONS = [
    {'key': 'dashboard', 'label': 'Dashboard'},
    {'key': 'attendance', 'label': 'Atendimentos'},
    {'key': 'schedule_list', 'label': 'Lista'},
    {'key': 'tasks', 'label': 'Tarefas'},
    {'key': 'financial', 'label': 'Financeiro'},
    {'key': 'products', 'label': 'Produtos'},
    {'key': 'clients', 'label': 'Clientes'},
    {'key': 'budgets', 'label': 'Orçamentos'},
    {'key': 'employees', 'label': 'Funcionários'},
    {'key': 'services', 'label': 'Serviços'},
    {'key': 'schedule', 'label': 'Agendamentos'},
    {'key': 'admin_users', 'label': 'Usuários'},
]


def admin_required():
    return session.get('role') == 'admin'


def ensure_admin_permission_schema(cursor):
    cursor.execute("""
        DELETE FROM role_menu_permissions
        WHERE role IS NULL OR role = ''
           OR role NOT IN ('admin','oficina','loja','atendimentos','pessoal')
    """)
    cursor.execute("""
        ALTER TABLE role_menu_permissions
        MODIFY COLUMN role ENUM('admin','oficina','loja','atendimentos','pessoal') NOT NULL
    """)


def _financial_table(kind: str) -> str:
    return 'financial_income' if kind == 'income' else 'financial_expenses'


def _financial_label(kind: str) -> str:
    return 'entradas' if kind == 'income' else 'despesas'


def _financial_usage_counts(kind: str) -> dict[str, int]:
    table = _financial_table(kind)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT category, COUNT(*) as total FROM {table} GROUP BY category")
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return {str(row['category']): int(row['total']) for row in rows if row.get('category')}


@admin_bp.route('/users')
@login_required
def users():
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_admin_permission_schema(cursor)
    conn.commit()

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
                           role_labels=ROLE_LABELS,
                           menus=MENU_OPTIONS,
                           permissions=permissions)


@admin_bp.route('/financial-categories')
@login_required
def financial_categories():
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    income_categories = list_financial_categories('income')
    expense_categories = list_financial_categories('expense')
    income_usage = _financial_usage_counts('income')
    expense_usage = _financial_usage_counts('expense')

    return render_template(
        'admin/financial_categories.html',
        income_categories=income_categories,
        expense_categories=expense_categories,
        income_usage=income_usage,
        expense_usage=expense_usage,
    )


@admin_bp.route('/financial-categories/<kind>/add', methods=['POST'])
@login_required
def add_category(kind):
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    ok, result = add_financial_category(kind, request.form.get('name'))
    flash(
        f"Categoria adicionada em {_financial_label(kind)}: {result}" if ok else result,
        'success' if ok else 'error',
    )
    return redirect(url_for('admin.financial_categories'))


@admin_bp.route('/financial-categories/<kind>/update', methods=['POST'])
@login_required
def update_category(kind):
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    current_name = request.form.get('current_name')
    new_name = request.form.get('new_name')
    ok, old_name = rename_financial_category(kind, current_name, new_name)
    if not ok:
        flash(old_name, 'error')
        return redirect(url_for('admin.financial_categories'))

    normalized_new = request.form.get('new_name', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"UPDATE {_financial_table(kind)} SET category = %s WHERE category = %s",
            (normalized_new, old_name),
        )
        conn.commit()
        flash(f"Categoria atualizada em {_financial_label(kind)}.", 'success')
    except Exception as e:
        conn.rollback()
        rename_financial_category(kind, normalized_new, old_name)
        flash(f'Erro ao atualizar categoria: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.financial_categories'))


@admin_bp.route('/financial-categories/<kind>/delete', methods=['POST'])
@login_required
def delete_category(kind):
    if not admin_required():
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('tasks.dashboard'))

    category_name = (request.form.get('name') or '').strip()
    usage = _financial_usage_counts(kind)
    if usage.get(category_name, 0) > 0:
        flash('Não é possível excluir uma categoria já usada em lançamentos.', 'error')
        return redirect(url_for('admin.financial_categories'))

    ok, message = delete_financial_category(kind, category_name)
    flash(message if not ok else f'Categoria removida de {_financial_label(kind)}.', 'success' if ok else 'error')
    return redirect(url_for('admin.financial_categories'))


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
    ensure_admin_permission_schema(cursor)

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

