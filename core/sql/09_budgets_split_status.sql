-- Split budget status into two axes:
--   - approval_status: decision (sent/approved/rejected)
--   - stage_status: operational stage (budget/ready_for_pickup/delivered)
--
-- Also adds timestamp columns for KPI reporting.
-- ENUM values are listed in alphabetical order (requested).

SET @db := DATABASE();

-- Add columns if missing (rerunnable)
SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE budgets ADD COLUMN approval_status ENUM(''approved'', ''rejected'', ''sent'') NOT NULL DEFAULT ''sent'' AFTER status',
        'SELECT ''approval_status already exists'' AS info'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'budgets' AND COLUMN_NAME = 'approval_status'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE budgets ADD COLUMN stage_status ENUM(''budget'', ''delivered'', ''ready_for_pickup'') NOT NULL DEFAULT ''budget'' AFTER approval_status',
        'SELECT ''stage_status already exists'' AS info'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'budgets' AND COLUMN_NAME = 'stage_status'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE budgets ADD COLUMN approved_at DATETIME NULL AFTER stage_status',
        'SELECT ''approved_at already exists'' AS info'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'budgets' AND COLUMN_NAME = 'approved_at'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE budgets ADD COLUMN rejected_at DATETIME NULL AFTER approved_at',
        'SELECT ''rejected_at already exists'' AS info'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'budgets' AND COLUMN_NAME = 'rejected_at'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE budgets ADD COLUMN ready_for_pickup_at DATETIME NULL AFTER rejected_at',
        'SELECT ''ready_for_pickup_at already exists'' AS info'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'budgets' AND COLUMN_NAME = 'ready_for_pickup_at'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE budgets ADD COLUMN delivered_at DATETIME NULL AFTER ready_for_pickup_at',
        'SELECT ''delivered_at already exists'' AS info'
    )
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'budgets' AND COLUMN_NAME = 'delivered_at'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill (best-effort) from legacy `budgets.status`
UPDATE budgets
SET approval_status = CASE
    WHEN status = 'approved' THEN 'approved'
    WHEN status = 'rejected' THEN 'rejected'
    -- Legacy stage values used previously usually imply the budget was approved.
    WHEN status IN ('ready_for_pickup', 'delivered', 'completed') THEN 'approved'
    ELSE 'sent'
END
WHERE id > 0; -- key column (MySQL Workbench safe update mode)

UPDATE budgets
SET stage_status = CASE
    WHEN status = 'ready_for_pickup' THEN 'ready_for_pickup'
    WHEN status IN ('delivered', 'completed') THEN 'delivered'
    ELSE 'budget'
END
WHERE id > 0; -- key column (MySQL Workbench safe update mode)

-- Best-effort timestamps for existing rows (use updated_at as approximation)
UPDATE budgets
SET approved_at = COALESCE(approved_at, updated_at)
WHERE approval_status = 'approved' AND id > 0; -- key column (safe update mode)

UPDATE budgets
SET rejected_at = COALESCE(rejected_at, updated_at)
WHERE approval_status = 'rejected' AND id > 0; -- key column (safe update mode)

UPDATE budgets
SET ready_for_pickup_at = COALESCE(ready_for_pickup_at, updated_at)
WHERE stage_status = 'ready_for_pickup' AND id > 0; -- key column (safe update mode)

UPDATE budgets
SET delivered_at = COALESCE(delivered_at, updated_at)
WHERE stage_status = 'delivered' AND id > 0; -- key column (safe update mode)
