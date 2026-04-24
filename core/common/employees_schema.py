def _fetch_count(cursor, query, params=()):
    cursor.execute(query, params)
    row = cursor.fetchone()
    if isinstance(row, dict):
        return int(next(iter(row.values())) or 0)
    return int((row[0] if row else 0) or 0)


def _table_exists(cursor, table_name):
    return _fetch_count(
        cursor,
        """
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (table_name,),
    ) > 0


def _column_exists(cursor, table_name, column_name):
    return _fetch_count(
        cursor,
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table_name, column_name),
    ) > 0


def _foreign_key_name(cursor, table_name, column_name, referenced_table=None):
    query = """
        SELECT CONSTRAINT_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
          AND REFERENCED_TABLE_NAME IS NOT NULL
    """
    params = [table_name, column_name]
    if referenced_table:
        query += " AND REFERENCED_TABLE_NAME = %s"
        params.append(referenced_table)
    query += " LIMIT 1"

    cursor.execute(query, tuple(params))
    row = cursor.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return row.get("CONSTRAINT_NAME")
    return row[0]


def _execute_ignoring_existing(cursor, statement):
    try:
        cursor.execute(statement)
    except Exception:
        pass


def _add_column_if_missing(cursor, table_name, column_name, definition):
    if not _column_exists(cursor, table_name, column_name):
        _execute_ignoring_existing(cursor, f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _rename_column_if_needed(cursor, table_name, old_name, new_name):
    if _column_exists(cursor, table_name, old_name) and not _column_exists(cursor, table_name, new_name):
        cursor.execute(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")


def ensure_employees_schema(cursor):
    """Bring legacy mechanics schema forward to employees without requiring a manual migration first."""
    if not _table_exists(cursor, "employees"):
        if _table_exists(cursor, "mechanics"):
            fk_name = _foreign_key_name(cursor, "budgets", "mechanic_id", "mechanics")
            if fk_name:
                cursor.execute(f"ALTER TABLE budgets DROP FOREIGN KEY `{fk_name}`")
            cursor.execute("RENAME TABLE mechanics TO employees")
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20),
                    cpf VARCHAR(14),
                    rg VARCHAR(20),
                    rg_issuer VARCHAR(20),
                    rg_state VARCHAR(2),
                    rg_issue_date DATE,
                    pis_pasep VARCHAR(20),
                    ctps_number VARCHAR(20),
                    ctps_series VARCHAR(10),
                    ctps_state VARCHAR(2),
                    birth_date DATE,
                    hiring_date DATE,
                    mother_name VARCHAR(100),
                    father_name VARCHAR(100),
                    education_level VARCHAR(50),
                    marital_status VARCHAR(50),
                    salary DECIMAL(10, 2),
                    num_dependents INT DEFAULT 0,
                    job_title VARCHAR(100),
                    contract_type VARCHAR(50),
                    work_schedule VARCHAR(100),
                    labor_notes TEXT,
                    address_cep VARCHAR(20),
                    address_street VARCHAR(255),
                    address_number VARCHAR(50),
                    address_district VARCHAR(100),
                    address_city VARCHAR(100),
                    address_state VARCHAR(2),
                    address_reference VARCHAR(255),
                    emergency_contact VARCHAR(255),
                    experience_years INT,
                    photo_path VARCHAR(255),
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )

    for column_name, definition in {
        "phone": "VARCHAR(20) AFTER name",
        "cpf": "VARCHAR(14) AFTER phone",
        "rg": "VARCHAR(20) AFTER cpf",
        "rg_issuer": "VARCHAR(20) AFTER rg",
        "rg_state": "VARCHAR(2) AFTER rg_issuer",
        "rg_issue_date": "DATE AFTER rg_state",
        "pis_pasep": "VARCHAR(20) AFTER rg_issue_date",
        "ctps_number": "VARCHAR(20) AFTER pis_pasep",
        "ctps_series": "VARCHAR(10) AFTER ctps_number",
        "ctps_state": "VARCHAR(2) AFTER ctps_series",
        "hiring_date": "DATE AFTER birth_date",
        "mother_name": "VARCHAR(100) AFTER hiring_date",
        "father_name": "VARCHAR(100) AFTER mother_name",
        "education_level": "VARCHAR(50) AFTER father_name",
        "marital_status": "VARCHAR(50) AFTER education_level",
        "salary": "DECIMAL(10, 2) AFTER marital_status",
        "num_dependents": "INT DEFAULT 0 AFTER salary",
        "job_title": "VARCHAR(100) AFTER num_dependents",
        "contract_type": "VARCHAR(50) AFTER job_title",
        "work_schedule": "VARCHAR(100) AFTER contract_type",
        "labor_notes": "TEXT AFTER work_schedule",
        "address_reference": "VARCHAR(255) AFTER address_state",
        "emergency_contact": "VARCHAR(255) AFTER address_reference",
        "is_active": "TINYINT(1) NOT NULL DEFAULT 1",
    }.items():
        _add_column_if_missing(cursor, "employees", column_name, definition)

    _execute_ignoring_existing(cursor, "ALTER TABLE employees MODIFY COLUMN address_state VARCHAR(100)")

    if _table_exists(cursor, "budgets"):
        fk_name = _foreign_key_name(cursor, "budgets", "mechanic_id")
        if fk_name:
            cursor.execute(f"ALTER TABLE budgets DROP FOREIGN KEY `{fk_name}`")
        _rename_column_if_needed(cursor, "budgets", "mechanic_id", "employee_id")
        if _column_exists(cursor, "budgets", "employee_id") and not _foreign_key_name(cursor, "budgets", "employee_id", "employees"):
            _execute_ignoring_existing(
                cursor,
                "ALTER TABLE budgets ADD CONSTRAINT fk_budgets_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL",
            )

    if _table_exists(cursor, "services"):
        _rename_column_if_needed(cursor, "services", "mechanic", "employee")
        _add_column_if_missing(cursor, "services", "employee", "VARCHAR(255)")

    if _table_exists(cursor, "budget_items"):
        _rename_column_if_needed(cursor, "budget_items", "mechanic", "employee")
        _add_column_if_missing(cursor, "budget_items", "employee", "VARCHAR(255)")

    if _table_exists(cursor, "role_menu_permissions"):
        _execute_ignoring_existing(
            cursor,
            """
            INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
            ('admin', 'employees', 1),
            ('oficina', 'employees', 1),
            ('loja', 'employees', 0),
            ('atendimentos', 'employees', 0),
            ('pessoal', 'employees', 0)
            ON DUPLICATE KEY UPDATE can_view = VALUES(can_view)
            """,
        )
