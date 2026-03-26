ALTER TABLE financial_income
    MODIFY COLUMN category VARCHAR(100) NOT NULL;

ALTER TABLE financial_expenses
    MODIFY COLUMN category VARCHAR(100) NOT NULL;
