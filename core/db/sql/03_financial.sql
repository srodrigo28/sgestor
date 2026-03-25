CREATE TABLE IF NOT EXISTS financial_income (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    category ENUM('serviço', 'contrato', 'salario mensal', 'bico') NOT NULL,
    payment_type ENUM('pix', 'dinheiro', 'cartao credito', 'cartao debito', 'boleto', 'transferência') NOT NULL,
    entry_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
