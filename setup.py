import sys
import subprocess
import venv
from pathlib import Path
import os

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
ENV_FILE = BASE_DIR / ".env"


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


def build_env():
    """Monta o ambiente para subprocessos usando o .env da raiz do projeto."""
    env = os.environ.copy()
    if ENV_FILE.exists():
        env["ENV_FILE"] = str(ENV_FILE)
    return env


def run_command(command, cwd=None):
    """Executa um comando e retorna o codigo de saida."""
    try:
        return subprocess.call(command, cwd=str(cwd) if cwd else None, env=build_env())
    except KeyboardInterrupt:
        return 130


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


def run_migrations():
    """Executa as migrations do banco de dados, se disponiveis."""
    print("\nChamando gerenciador de banco de dados (db/migration.py)...")
    try:
        if MIGRATION_FILE.exists():
            exit_code = run_command([sys.executable, str(MIGRATION_FILE), "up"], cwd=CORE_DIR)
            return exit_code == 0
        else:
            print("Arquivo db/migration.py nao encontrado. Pulando etapa de banco.")
            return True
    except Exception as e:
        print(f"Erro ao rodar db/migration.py: {e}")
        return False


def run_app():
    """Inicia a aplicacao Flask."""
    print("\nIniciando a aplicacao (manage.py)...")
    print("---------------------------------------------------")
    try:
        if MAIN_FILE.exists():
            exit_code = run_command([sys.executable, str(MAIN_FILE)], cwd=CORE_DIR)
            if exit_code == 130:
                print("\nAplicacao encerrada com sucesso.")
                print("Servidor finalizado manualmente pelo terminal.")
        else:
            print("Erro: manage.py nao encontrado.")
    except KeyboardInterrupt:
        print("\nAplicacao encerrada com sucesso.")
        print("Servidor finalizado manualmente pelo terminal.")


def get_mode():
    """Define o modo de execucao a partir dos argumentos."""
    if len(sys.argv) <= 1:
        return "all"

    mode = sys.argv[1].lower()
    valid_modes = {"all", "init", "run"}
    if mode in valid_modes:
        return mode

    print(f"Modo invalido: {sys.argv[1]}")
    print("Use: python setup.py [init|run]")
    sys.exit(1)


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

        mode_args = sys.argv[1:]
        print("Reiniciando setup dentro da venv para garantir isolamento...")
        # Re-executa este script usando o Python da venv
        exit_code = run_command([str(venv_python), __file__] + mode_args)
        if exit_code == 130:
            print("\nAplicacao encerrada com sucesso.")
            print("Servidor finalizado manualmente pelo terminal.")
        return

    print("Rodando dentro do ambiente virtual.")
    mode = get_mode()

    if mode in {"all", "init"}:
        # 2. Instalar Bibliotecas (Flask, MySQL)
        install_dependencies()
        # 3. Executar Migrations (Banco de Dados)
        if not run_migrations():
            print("\nSetup interrompido: nao foi possivel preparar o banco de dados.")
            print("Verifique se o MySQL esta rodando e execute novamente.")
            return

    if mode == "init":
        print("\nAmbiente preparado com sucesso.")
        print("Para iniciar a aplicacao depois, use: python setup.py run")
        return

    if mode in {"all", "run"}:
        if mode == "run":
            print("Modo run: iniciando servidor sem reinstalar dependencias.")
        else:
            print("\nSetup finalizado!")
        # 4. Iniciar Aplicacao
        run_app()


if __name__ == "__main__":
    main()


