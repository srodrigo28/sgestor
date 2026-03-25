import os
import argparse
import hashlib
import sys
from pathlib import Path

import mysql.connector
from mysql.connector import Error

# Allow running as script: `python core/db/migration.py`
CORE_DIR = Path(__file__).resolve().parents[1]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from common.env_loader import load_env_file

load_env_file()


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_local_db_host(host: str) -> bool:
    h = (host or "").strip().lower()
    return h in {"localhost", "127.0.0.1", "::1"}


def _is_seed_file(file_path: Path) -> bool:
    # Convention: any file containing 'seed' is treated as optional seed data.
    return "seed" in file_path.name.lower()


def _sha256_file(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_text_with_fallback(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def ensure_migrations_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            checksum CHAR(64) NOT NULL,
            kind ENUM('schema', 'seed') NOT NULL DEFAULT 'schema',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_schema_migrations_filename (filename)
        )
        """.strip()
    )


def get_applied_migrations(cursor) -> dict[str, dict]:
    cursor.execute("SELECT filename, checksum, kind, applied_at FROM schema_migrations ORDER BY id ASC")
    rows = cursor.fetchall()
    applied: dict[str, dict] = {}
    for filename, checksum, kind, applied_at in rows:
        applied[filename] = {
            "checksum": checksum,
            "kind": kind,
            "applied_at": applied_at,
        }
    return applied


def count_tables(cursor, db_name: str) -> int:
    # Exclude our own tracking table so a fresh DB does not look "initialized".
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_type = 'BASE TABLE'
          AND table_name <> 'schema_migrations'
        """.strip(),
        (db_name,),
    )
    return int(cursor.fetchone()[0] or 0)


def run_sql_file(cursor, file_path: Path) -> None:
    """Execute a .sql file. Fails fast on any SQL error."""
    print(f"Executando: {file_path.name}...")

    content = _read_text_with_fallback(file_path)

    try:
        # Fallback for cursors that don't support multi=True (like CMySQLCursor or some versions of MySQLCursor)
        statements = [s.strip() for s in content.split(';') if s.strip()]
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                    # Consume any results to avoid "Unread result found"
                    if cursor.with_rows:
                        cursor.fetchall()
                    # Also consume next sets if any
                    while cursor.nextset():
                       if cursor.with_rows:
                           cursor.fetchall()
                except mysql.connector.Error as err:
                    # 1050: Table exists, 1060: Duplicate column, 1061: Duplicate key name
                    if err.errno in [1050, 1060, 1061]: 
                        print(f"   [AVISO] Ignorando erro de existência ({err.errno}) para permitir reconciliação.")
                    else:
                        raise err

    except Exception as e:
        raise RuntimeError(f"Falha ao executar {file_path.name}: {e}") from e


def print_status(sql_files: list[Path], applied: dict[str, dict]) -> None:
    seed_files = [f for f in sql_files if _is_seed_file(f)]
    schema_files = [f for f in sql_files if not _is_seed_file(f)]

    pending = [f for f in sql_files if f.name not in applied]
    pending_schema = [f for f in pending if not _is_seed_file(f)]
    pending_seed = [f for f in pending if _is_seed_file(f)]

    applied_schema = [k for k, v in applied.items() if v.get("kind") == "schema"]
    applied_seed = [k for k, v in applied.items() if v.get("kind") == "seed"]

    print("\n--- Status das migrations ---")
    print(f"Total arquivos: {len(sql_files)} (schema: {len(schema_files)}, seed: {len(seed_files)})")
    print(f"Aplicadas: {len(applied)} (schema: {len(applied_schema)}, seed: {len(applied_seed)})")
    print(f"Pendentes: {len(pending)} (schema: {len(pending_schema)}, seed: {len(pending_seed)})")

    if pending_schema:
        print("\nPendentes (schema):")
        for f in pending_schema:
            print(f" - {f.name}")

    if pending_seed:
        print("\nPendentes (seed):")
        for f in pending_seed:
            print(f" - {f.name}")

    if applied:
        print("\nAplicadas:")
        for filename, info in applied.items():
            kind = info.get("kind")
            applied_at = info.get("applied_at")
            print(f" - {filename} ({kind}) {applied_at}")


def apply_migrations(conn, cursor, sql_files: list[Path], applied: dict[str, dict], mode: str) -> None:
    """Apply pending migrations.

    mode:
      - 'schema': only schema scripts (default)
      - 'seed': only seed scripts
      - 'all': schema + seed
    """
    pending = [f for f in sql_files if f.name not in applied]

    mode = (mode or "schema").strip().lower()
    if mode == "schema":
        pending = [f for f in pending if not _is_seed_file(f)]
    elif mode == "seed":
        pending = [f for f in pending if _is_seed_file(f)]
    elif mode == "all":
        pass
    else:
        raise ValueError(f"Modo invalido: {mode}")

    if not pending:
        print("\nNenhuma migration pendente para aplicar.")
        return

    for f in pending:
        kind = "seed" if _is_seed_file(f) else "schema"
        checksum = _sha256_file(f)

        # If a migration file changes after being applied, stop.
        if f.name in applied and applied[f.name].get("checksum") != checksum:
            raise RuntimeError(f"Migration {f.name} ja foi aplicada, mas o checksum mudou. Nao continuar.")

        run_sql_file(cursor, f)

        cursor.execute(
            "INSERT INTO schema_migrations (filename, checksum, kind) VALUES (%s, %s, %s)",
            (f.name, checksum, kind),
        )
        conn.commit()

    print("\nMigrations aplicadas com sucesso.")


def stamp_all(conn, cursor, sql_files: list[Path], applied: dict[str, dict], include_seeds: bool) -> None:
    to_stamp = [f for f in sql_files if f.name not in applied]
    if not include_seeds:
        to_stamp = [f for f in to_stamp if not _is_seed_file(f)]

    if not to_stamp:
        print("\nNada para 'stamp'.")
        return

    for f in to_stamp:
        kind = "seed" if _is_seed_file(f) else "schema"
        checksum = _sha256_file(f)
        cursor.execute(
            "INSERT INTO schema_migrations (filename, checksum, kind) VALUES (%s, %s, %s)",
            (f.name, checksum, kind),
        )

    conn.commit()
    print("\nStamp concluido (migrations marcadas como aplicadas, sem executar SQL).")


def check_and_migrate_db(auto_seed: bool = True) -> None:
    """
    Verifica se o banco de dados existe, cria se necessario e roda todas as migrations.
    Funcao projetada para ser chamada no startup da aplicacao (non-interactive).
    """
    print("--- Verificando Banco de Dados e Migrations (Auto) ---")
    load_env_file()

    # Parametros de conexao padrao
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")), 
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
    }
    db_name = os.getenv("DB_NAME", "flask_crud")

    conn = None
    cursor = None
    try:
        # 1. Conecta ao MySQL puramente (sem selecionar DB) para poder criar o DB se nao existir
        conn = mysql.connector.connect(use_pure=True, **config)
        if not conn.is_connected():
            print("Erro: Nao foi possivel conectar ao MySQL.")
            return

        cursor = conn.cursor()

        # Cria database se nao existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        conn.commit()

        # Usa o database
        conn.database = db_name

        # Garante tabela de controle
        ensure_migrations_table(cursor)
        conn.commit()

        # Localiza arquivos SQL
        # Tenta pegar caminho absoluto baseado neste arquivo, caso o CWD esteja diferente
        base_dir = Path(__file__).parent
        sql_dir = base_dir / "sql"
        if not sql_dir.exists():
            # Fallback para CWD padrao atual.
            sql_dir = Path("db/sql")
            if not sql_dir.exists():
                sql_dir = Path("sql")

        if not sql_dir.exists():
            print(f"Erro: Pasta sql nao encontrada em {base_dir}/sql, ./db/sql ou ./sql")
            return

        sql_files = sorted(list(sql_dir.glob("*.sql")))
        if not sql_files:
            print("Aviso: Nenhuma migration encontrada.")
            return

        # 2. Verifica o que ja foi aplicado
        applied = get_applied_migrations(cursor)
        
        # 3. Aplica SCHEMA migrations pendentes
        #    Repara que passamos 'applied' atual. 
        #    O apply_migrations filtra based no que nao esta no 'applied'.
        pending_schema = [f for f in sql_files if f.name not in applied and not _is_seed_file(f)]
        
        if pending_schema:
            print(f"Aplicando {len(pending_schema)} migrations de schema pendentes...")
            apply_migrations(conn, cursor, sql_files, applied, mode="schema")
            # Apos aplicar schema, o estado do banco mudou. 
            # Se formos aplicar seeds, precisamos atualizar 'applied'.

        # 4. Aplica SEEDS pendentes (se auto_seed=True)
        if auto_seed:
            # Re-lê o estado atualizado das migrations aplicadas
            applied = get_applied_migrations(cursor)
            pending_seeds = [f for f in sql_files if f.name not in applied and _is_seed_file(f)]
            
            if pending_seeds:
                print(f"Aplicando {len(pending_seeds)} seeds pendentes...")
                apply_migrations(conn, cursor, sql_files, applied, mode="seed")

        print("Verificacao de banco concluida com sucesso.")

    except Error as e:
        print(f"Erro MySQL durante startup migration: {e.msg}")
        # Nao damos raise para nao derrubar a app, mas logamos erro critico
    except Exception as e:
        print(f"Erro inesperado durante startup migration: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerenciamento de migrations SQL (MySQL/MariaDB).")
    parser.add_argument("command", nargs="?", default="", help="status|up|seed|all|stamp")
    parser.add_argument("--sql-dir", default="db/sql", help="Diretorio com arquivos .sql (default: db/sql)")
    parser.add_argument(
        "--include-seeds",
        action="store_true",
        help="Inclui scripts de seed (arquivo contendo 'seed' no nome)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Permite rodar migrations mesmo com banco ja existente sem tracking (perigoso)",
    )
    args = parser.parse_args()

    print("\n--- Gerenciamento de Banco de Dados e Migrations ---")

    app_env = (os.getenv("APP_ENV") or "development").strip().lower() or "development"

    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
    }
    db_name = os.getenv("DB_NAME", "flask_crud")

    # Safety guards to reduce the chance of running migrations against the client's DB by accident.
    if app_env != "production" and not _is_local_db_host(config["host"]) and not _truthy(os.getenv("ALLOW_REMOTE_DB")):
        print(
            "ABORTADO: DB_HOST nao-local detectado com APP_ENV != 'production'.\n"
            f"   APP_ENV='{app_env}' DB_HOST='{config['host']}'\n"
            "   Use um banco local para desenvolvimento (recomendado) ou set APP_ENV=production / ALLOW_REMOTE_DB=1."
        )
        return

    if app_env == "production" and not _truthy(os.getenv("ALLOW_PROD_MIGRATIONS")):
        confirm = input("APP_ENV=production. Digite PRODUCTION para continuar: ").strip()
        if confirm != "PRODUCTION":
            print("Abortado.")
            return

    cmd = (args.command or "").strip().lower()

    try:
        # Force pure python to ensure 'multi=True' works reliably (C extension might not support it)
        conn = mysql.connector.connect(use_pure=True, **config)
        if not conn.is_connected():
            print("Nao foi possivel conectar ao MySQL.")
            return

        print("Conectado ao MySQL.")
        cursor = conn.cursor()

        try:
            # Ensure DB exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            conn.database = db_name

            ensure_migrations_table(cursor)
            conn.commit()

            sql_dir = Path(args.sql_dir)
            if not sql_dir.exists():
                print(f"Pasta '{sql_dir}/' nao encontrada.")
                return

            sql_files = sorted(list(sql_dir.glob("*.sql")))
            if not sql_files:
                print(f"Nenhum arquivo .sql encontrado em '{sql_dir}/'.")
                return

            applied = get_applied_migrations(cursor)
            table_count = count_tables(cursor, db_name)

            if cmd in {"status", "list"}:
                print_status(sql_files, applied)
                if table_count > 0 and len(applied) == 0:
                    print(
                        "\nATENCAO: o banco ja tem tabelas, mas schema_migrations esta vazio.\n"
                        "   -> Provavelmente este banco ja esta pronto e ainda nao foi 'stampado'.\n"
                        "   -> Use: python migration.py stamp\n"
                        "            python migration.py stamp --include-seeds\n"
                        "   -> Ou rode sem argumentos para escolher interativamente."
                    )
                return

            if cmd == "stamp":
                print_status(sql_files, applied)
                stamp_all(conn, cursor, sql_files, applied, include_seeds=args.include_seeds)
                return

            # Safety: avoid reapplying everything on an existing DB without tracking.
            if cmd in {"up", "seed", "all"} and table_count > 0 and len(applied) == 0 and not args.force:
                print_status(sql_files, applied)
                print(
                    "\nABORTADO: banco ja existente sem tracking de migrations.\n"
                    "   -> Rode um 'stamp' primeiro, ou use --force se tiver certeza (nao recomendado)."
                )
                return

            if cmd == "up":
                print_status(sql_files, applied)
                apply_migrations(conn, cursor, sql_files, applied, mode="schema")
                return

            if cmd == "seed":
                print_status(sql_files, applied)
                apply_migrations(conn, cursor, sql_files, applied, mode="seed")
                return

            if cmd == "all":
                print_status(sql_files, applied)
                apply_migrations(conn, cursor, sql_files, applied, mode="all")
                return

            if cmd:
                print(f"Comando invalido: {cmd}")
                parser.print_help()
                return

            # Interactive mode (default)
            if table_count > 0 and len(applied) == 0:
                print("\nDetectei um banco ja existente, mas sem tracking de migrations.")
                print(f"   Tabelas no banco (excluindo schema_migrations): {table_count}")
                print("Opcoes:")
                print("   [S] Stamp schema (marcar como aplicadas sem executar)")
                print("   [A] Stamp schema + seeds")
                print("   [R] Rodar migrations agora (pode falhar se ja estiver aplicado)")
                print("   [0] Abort")
                ch = input("Escolha: ").strip().lower()
                if ch == "s":
                    stamp_all(conn, cursor, sql_files, applied, include_seeds=False)
                    applied = get_applied_migrations(cursor)
                elif ch == "a":
                    stamp_all(conn, cursor, sql_files, applied, include_seeds=True)
                    applied = get_applied_migrations(cursor)
                elif ch == "r":
                    pass
                else:
                    print("Abortado.")
                    return

            print_status(sql_files, applied)
            print("\nOpcoes:")
            print("   [U] Aplicar pendentes (schema)")
            print("   [S] Aplicar pendentes (schema + seeds)")
            print("   [T] Stamp schema (marcar como aplicadas sem executar)")
            print("   [A] Stamp schema + seeds")
            print("   [0] Sair")
            choice = input("Escolha: ").strip().lower()

            if choice == "0":
                return

            if choice == "u":
                apply_migrations(conn, cursor, sql_files, applied, mode="schema")
                return

            if choice == "s":
                apply_migrations(conn, cursor, sql_files, applied, mode="all")
                return

            if choice == "t":
                stamp_all(conn, cursor, sql_files, applied, include_seeds=False)
                return

            if choice == "a":
                stamp_all(conn, cursor, sql_files, applied, include_seeds=True)
                return

            print("Opcao invalida.")

        finally:
            conn.close()

    except Error as e:
        print(f"Erro MySQL: {e.msg}")
        if e.errno == 2003:
            print("   -> Verifique se o MySQL esta rodando.")
    except ImportError:
        print("Erro: Biblioteca mysql-connector-python nao encontrada.")
    except Exception as e:
        print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()
