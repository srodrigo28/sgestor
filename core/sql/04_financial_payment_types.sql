ALTER TABLE financial_income
    MODIFY COLUMN payment_type ENUM(
        'pix',
        'dinheiro',
        'cartao credito',
        'cartao debito',
        'boleto',
        'transferência'
    ) NOT NULL;
