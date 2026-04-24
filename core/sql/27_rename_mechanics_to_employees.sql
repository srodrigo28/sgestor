-- Rename the old mechanic domain to the broader employee domain.
-- This is intentionally defensive so a partially migrated database can still start.

SET @old_budget_fk = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'budgets'
      AND COLUMN_NAME = 'mechanic_id'
      AND REFERENCED_TABLE_NAME = 'mechanics'
    LIMIT 1
);

SET @sql = IF(@old_budget_fk IS NULL, 'SELECT 1', CONCAT('ALTER TABLE budgets DROP FOREIGN KEY ', @old_budget_fk));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_mechanics = (
    SELECT COUNT(*)
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'mechanics'
);

SET @has_employees = (
    SELECT COUNT(*)
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'employees'
);

SET @sql = IF(@has_mechanics = 1 AND @has_employees = 0, 'RENAME TABLE mechanics TO employees', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_budget_mechanic = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'budgets'
      AND COLUMN_NAME = 'mechanic_id'
);

SET @has_budget_employee = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'budgets'
      AND COLUMN_NAME = 'employee_id'
);

SET @sql = IF(@has_budget_mechanic = 1 AND @has_budget_employee = 0, 'ALTER TABLE budgets RENAME COLUMN mechanic_id TO employee_id', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @employee_fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'budgets'
      AND COLUMN_NAME = 'employee_id'
      AND REFERENCED_TABLE_NAME = 'employees'
);

SET @sql = IF(@employee_fk_exists = 0, 'ALTER TABLE budgets ADD CONSTRAINT fk_budgets_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_services_mechanic = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'services'
      AND COLUMN_NAME = 'mechanic'
);

SET @has_services_employee = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'services'
      AND COLUMN_NAME = 'employee'
);

SET @sql = IF(@has_services_mechanic = 1 AND @has_services_employee = 0, 'ALTER TABLE services RENAME COLUMN mechanic TO employee', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_items_mechanic = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'budget_items'
      AND COLUMN_NAME = 'mechanic'
);

SET @has_items_employee = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'budget_items'
      AND COLUMN_NAME = 'employee'
);

SET @sql = IF(@has_items_mechanic = 1 AND @has_items_employee = 0, 'ALTER TABLE budget_items RENAME COLUMN mechanic TO employee', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'employees', 1),
('oficina', 'employees', 1),
('loja', 'employees', 0),
('atendimentos', 'employees', 0),
('pessoal', 'employees', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);
