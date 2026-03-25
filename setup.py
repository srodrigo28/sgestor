import sys
import subprocess
import venv
from pathlib import Path

# Configuracoes
BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR / "core"
VENV_DIR = CORE_DIR / "venv"
REQUIREMENTS = [
    "flask",
    "mysql-connector-python",
    "gunicorn",
    "python-dotenv",
    "werkzeug"
]
REQUIREMENTS_FILE = CORE_DIR / "requirements.txt"
MIGRATION_FILE = CORE_DIR / "db" / "migration.py"
MAIN_FILE = CORE_DIR / "manage.py"

def is_venv():
    """Verifica se o script esta rodando dentro de um ambiente virtual."""
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )

def get_venv_python():
    """Retorna o caminho do executavel Python do venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def install_dependencies():
    """Instala as dependencias listadas."""
    print("Verificando dependencias do Python...")

    if REQUIREMENTS_FILE.exists():
        print(f"Instalando dependencias de {REQUIREMENTS_FILE}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
        )
        print("Instalacao concluida.")
        return

    try:
        import flask  # noqa: F401
        import mysql.connector  # noqa: F401
        print("Bibliotecas ja instaladas.")
    except ImportError:
        print(f"Instalando: {', '.join(REQUIREMENTS)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + REQUIREMENTS)
        print("Instalacao concluida.")

def main():
    print("Iniciando setup do ambiente Flask...\n")
    if not CORE_DIR.exists():
        print(f"Erro: pasta core nao encontrada em {CORE_DIR}")
        return

    # 1. Garantir Venv (Ambiente Virtual)
    if not is_venv():
        print("Ambiente virtual NAO detectado/ativo.")

        if not VENV_DIR.exists():
            print(f"Criando venv em: {VENV_DIR}")
            venv.create(VENV_DIR, with_pip=True)

        venv_python = get_venv_python()
        if not venv_python.exists():
            print(f"Erro critico: Python da venv nao encontrado em {venv_python}")
            return

        print("Reiniciando setup dentro da venv para garantir isolamento...")
        # Re-executa este script usando o Python da venv
        subprocess.call([str(venv_python), __file__] + sys.argv[1:])
        return

    print("Rodando dentro do ambiente virtual.")

    # 2. Instalar Bibliotecas (Flask, MySQL)
    install_dependencies()

    # 3. Executar Migrations (Banco de Dados)
    print("\nChamando gerenciador de banco de dados (db/migration.py)...")
    try:
        if MIGRATION_FILE.exists():
            subprocess.call([sys.executable, str(MIGRATION_FILE), "up"], cwd=str(CORE_DIR))
        else:
            print("Arquivo db/migration.py nao encontrado. Pulando etapa de banco.")
    except Exception as e:
        print(f"Erro ao rodar db/migration.py: {e}")

    # 4. Iniciar Aplicacao
    print("\nSetup finalizado! Iniciando a aplicacao (manage.py)...")
    print("---------------------------------------------------")
    try:
        if MAIN_FILE.exists():
            subprocess.call([sys.executable, str(MAIN_FILE)], cwd=str(CORE_DIR))
        else:
            print("Erro: manage.py nao encontrado.")
    except KeyboardInterrupt:
        print("\nAplicacao interrompida pelo usuario.")

if __name__ == "__main__":
    main()
