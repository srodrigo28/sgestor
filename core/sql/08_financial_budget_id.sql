-- Adiciona coluna budget_id na tabela financial_income (receitas) se não existir.
-- Utiliza procedimento armazenado temporário para compatibilidade e verificação.

SET @dbname = DATABASE();
SET @tablename = "financial_income";
SET @columnname = "budget_id";

SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 1",
  CONCAT("ALTER TABLE ", @tablename, " ADD COLUMN ", @columnname, " INT NULL AFTER user_id, ADD CONSTRAINT fk_financial_income_budget FOREIGN KEY (", @columnname, ") REFERENCES budgets(id) ON DELETE SET NULL")
));

PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;
