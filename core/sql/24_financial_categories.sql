CREATE TABLE IF NOT EXISTS financial_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    kind ENUM('income', 'expense') NOT NULL,
    name VARCHAR(80) NOT NULL,
    icon VARCHAR(16) DEFAULT '🏷️',
    color VARCHAR(16) DEFAULT '#6b7280',
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_financial_categories_user_kind_name (user_id, kind, name),
    CONSTRAINT fk_financial_categories_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

ALTER TABLE financial_income
    MODIFY COLUMN category VARCHAR(80) NOT NULL;

ALTER TABLE financial_expenses
    MODIFY COLUMN category VARCHAR(80) NOT NULL;
