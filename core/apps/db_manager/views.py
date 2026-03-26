import os
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, current_app, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from apps.auth.views import login_required

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

db_bp = Blueprint('db_manager', __name__)

# Configurações vindas do .env
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', os.getenv('DB_PASSWORD', ''))
DB_NAME = os.getenv('DB_NAME', 'flask_crud')
DB_HOST = os.getenv('DB_HOST', 'localhost')

# Tenta encontrar o executavel do MySQL/Mariadb
def get_mysql_executable(cmd_name):
    # 1. Se definido no .env, usa ele
    if os.getenv(f'{cmd_name.upper()}_PATH'):
        return os.getenv(f'{cmd_name.upper()}_PATH')
    
    # 2. Caminhos padroes comuns no Windows
    possible_paths = [
        f"C:\\xampp\\mysql\\bin\\{cmd_name}.exe",
        f"C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\{cmd_name}.exe",
        f"C:\\Program Files\\MariaDB 10.6\\bin\\{cmd_name}.exe",
        f".\\{cmd_name}.exe" # Na raiz do projeto
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
             return f'"{path}"' # Retorna com aspas por causa dos espaços
             
    # 3. Tenta o comando global (assumindo que esta no PATH)
    return cmd_name


def admin_required():
    return session.get('role') == 'admin'

# Rota Principal da Página de Backup
@db_bp.route('/admin/backup', methods=['GET', 'POST'])
@login_required
def index():
    if not admin_required():
        flash('Acesso restrito ao administrador.', 'error')
        return redirect(url_for('tasks.dashboard'))

    preview_content = None
    filename_preview = None

    # Lógica de Upload para Importação
    if request.method == 'POST' and 'file_upload' in request.files:
        file = request.files['file_upload']
        if file.filename != '':
            filename = secure_filename(file.filename)
            upload_path = os.path.join(str(BASE_DIR), 'tmp')
            os.makedirs(upload_path, exist_ok=True)
            
            filepath = os.path.join(upload_path, filename)
            file.save(filepath)
            
            # Lê o começo do arquivo para mostrar preview
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    preview_content = "".join([next(f) for x in range(15)])
                filename_preview = filename
                flash('Arquivo carregado. Confira abaixo e confirme a restauração.', 'info')
            except Exception as e:
                flash(f'Erro ao ler arquivo: {e}', 'danger')

    return render_template('admin/backup.html', preview=preview_content, filename=filename_preview)

# Rota de Exportação (Download)
@db_bp.route('/admin/backup/download/<type>')
@login_required
def download(type):
    if not admin_required():
        flash('Acesso restrito ao administrador.', 'error')
        return redirect(url_for('tasks.dashboard'))
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f"backup_{type}_{timestamp}.sql"
        folder = os.path.join(str(BASE_DIR), 'tmp')
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        
        # Recupera executavel. Remove aspas se houver.
        mysqldump_exe = get_mysql_executable('mysqldump').replace('"', '')

        # Monta argumentos para subprocess.run (lista)
        # mysqldump -hHOST -uUSER -pPASS DBNAME
        command = [mysqldump_exe, f"-h{DB_HOST}", f"-u{DB_USER}"]
        
        if DB_PASS:
            command.append(f"-p{DB_PASS}")

        if type == 'data':
            command.extend(["--no-create-info", "--complete-insert"])
            
        command.append(DB_NAME)

        # Executa com redirecionamento de saida
        with open(filepath, 'w', encoding='utf-8') as outfile:
            # shell=False e seguro e evita problemas de aspas no Windows
            result = subprocess.run(command, stdout=outfile, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "Erro desconhecido"
            flash(f"Erro no mysqldump (Code {result.returncode}): {error_msg}", "danger")
            return redirect(url_for('db_manager.index'))
            
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
             flash("Arquivo de backup foi criado vazio ou falhou.", "danger")
             return redirect(url_for('db_manager.index'))

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        flash(f"Erro ao gerar backup: {str(e)}", "danger")
        return redirect(url_for('db_manager.index'))

# Rota que Executa a Importação Real
@db_bp.route('/admin/backup/confirm', methods=['POST'])
@login_required
def confirm_restore():
    if not admin_required():
        flash('Acesso restrito ao administrador.', 'error')
        return redirect(url_for('tasks.dashboard'))
    filename = request.form.get('filename')
    filepath = os.path.join(str(BASE_DIR), 'tmp', filename)
    
    if not os.path.exists(filepath):
        flash('Arquivo perdido. Faça upload novamente.', 'danger')
        return redirect(url_for('db_manager.index'))

    password_part = f"-p{DB_PASS}" if DB_PASS else ""
    
    mysql_cmd = get_mysql_executable('mysql')
    
    # Importa ignorando chaves estrangeiras temporariamente para evitar erros de ordem
    # cmd = f"{mysql_cmd} -h {DB_HOST} -u {DB_USER} {password_part} {DB_NAME} < \"{filepath}\""
    
    try:
        # Recupera executavel. Remove aspas se houver.
        mysql_exe = get_mysql_executable('mysql').replace('"', '')

        # Monta comando
        command = [mysql_exe, f"-h{DB_HOST}", f"-u{DB_USER}"]
        
        if DB_PASS:
            command.append(f"-p{DB_PASS}")
            
        command.append(DB_NAME)

        # Executa usando input redirection via Python (mais seguro que shell <)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
             result = subprocess.run(command, stdin=infile, capture_output=True, text=True)

        if result.returncode == 0:
            flash('✅ Banco de dados restaurado com sucesso!', 'success')
        else:
            error_msg = result.stderr if result.stderr else "Erro desconhecido"
            # Tenta pegar apenas as ultimas linhas se for muito grande
            short_error = error_msg[-300:] if len(error_msg) > 300 else error_msg
            flash(f'❌ Falha na importação (Code {result.returncode}): {short_error}', 'danger')

    except Exception as e:
        flash(f'Erro crítico: {str(e)}', 'danger')

    return redirect(url_for('db_manager.index'))

# Rota para Sincronizar com VPS (Usa script powershell)
@db_bp.route('/admin/backup/sync_vps', methods=['POST'])
@login_required
def sync_vps():
    if not admin_required():
        flash('Acesso restrito ao administrador.', 'error')
        return redirect(url_for('tasks.dashboard'))
    # Caminho do script PS1 - relativo a raiz do projeto
    script_path = os.path.join(str(BASE_DIR), 'scripts', 'sync_vps_to_xampp.ps1')
    env_path = os.path.join(str(BASE_DIR), '.env.prod')
    
    if not os.path.exists(script_path):
        flash('Script de sincronização (scripts/sync_vps_to_xampp.ps1) não encontrado.', 'danger')
        return redirect(url_for('db_manager.index'))

    if not os.path.exists(env_path):
        flash('Arquivo .env.prod não encontrado. Necessário para conectar na VPS.', 'danger')
        return redirect(url_for('db_manager.index'))

    try:
        # Monta o comando do PowerShell
        # powershell -ExecutionPolicy Bypass -File "scripts/sync_vps_to_xampp.ps1" -SourceEnvFile ".env.prod" -Force
        cmd = [
            "powershell", 
            "-ExecutionPolicy", "Bypass", 
            "-File", script_path, 
            "-SourceEnvFile", env_path, 
            "-Force"
        ]
        
        # Executa o processo
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR))
        
        if result.returncode == 0:
            # SUCESSO NO SYNC. AGORA RODAR MIGRATIONS PARA GARANTIR COMPATIBILIDADE
            try:
                # Importante: Precisamos rodar o migration.py up para criar tabelas novas que 
                # existam no codigo local mas ainda nao na VPS (ex: mechanics)
                migration_cmd = [sys.executable, str(BASE_DIR / "db" / "migration.py"), "up"]
                mig_result = subprocess.run(migration_cmd, capture_output=True, text=True, cwd=str(BASE_DIR))
                
                if mig_result.returncode == 0:
                     flash('✅ Sincronização e Migrations realizadas com sucesso! Banco atualizado e compatível.', 'success')
                else:
                     flash('⚠️ Sincronização OK, mas erro nas Migrations. Verifique o console.', 'warning')
            except Exception as emig:
                flash(f'⚠️ Sincronização OK, mas falha ao chamar migration.py: {emig}', 'warning')

        else:
            # Pega as ultimas linhas do erro para nao poluir demais
            error_output = result.stderr if result.stderr else result.stdout
            short_error = error_output[-300:] if len(error_output) > 300 else error_output
            flash(f'❌ Falha na sincronização: {short_error}', 'danger')
            
    except Exception as e:
        flash(f'Erro ao tentar executar o script: {str(e)}', 'danger')

    return redirect(url_for('db_manager.index'))

