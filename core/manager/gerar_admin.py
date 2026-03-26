import os
import sys
import mysql.connector
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# --- Configuração de Caminhos ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(root_dir, '.env'))

def criar_admin():
    print("--- Gerador de Admin Manual ---")

    # 1. Configurações da conta
    NOME = os.getenv("ADMIN_DEFAULT_NAME", "Administrador 99Dev")
    EMAIL = os.getenv("ADMIN_DEFAULT_EMAIL", "admin@99dev.pro")
    SENHA_PLAIN = os.getenv("ADMIN_DEFAULT_PASSWORD", "123123")
    ROLE = "admin" # Ajustado para a coluna 'role'

    # 2. Conexão com Banco de Dados
    try:
        cnx = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASS', os.getenv('DB_PASSWORD', '')),
            database=os.getenv('DB_NAME', 'flask_crud')
        )
        cursor = cnx.cursor()
    except Exception as e:
        print(f"❌ Erro ao conectar no banco: {e}")
        return

    # 3. Lógica de Inserção
    try:
        # Verifica se já existe
        check_query = "SELECT id FROM users WHERE email = %s"
        cursor.execute(check_query, (EMAIL,))
        exists = cursor.fetchone()

        if exists:
            print(f"⚠️ O usuário {EMAIL} já existe no banco (ID: {exists[0]}).")
        else:
            # Gera o hash seguro
            senha_hash = generate_password_hash(SENHA_PLAIN)
            
            # Query ajustada para colunas: name, email, password, role
            insert_query = """
            INSERT INTO users (name, email, password, role) 
            VALUES (%s, %s, %s, %s)
            """
            val = (NOME, EMAIL, senha_hash, ROLE)
            
            cursor.execute(insert_query, val)
            cnx.commit()
            print(f"✅ Usuário criado com sucesso!")
            print(f"📧 Login: {EMAIL}")
            print(f"🔑 Senha: {SENHA_PLAIN}")

    except mysql.connector.Error as err:
        print(f"❌ Erro de SQL: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

if __name__ == "__main__":
    criar_admin()
