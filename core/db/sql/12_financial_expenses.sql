-- Cria tabela de Despesas Financeiras (Payables / Expenses)
CREATE TABLE IF NOT EXISTS financial_expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    payment_type ENUM('pix', 'dinheiro', 'cartao credito', 'cartao debito', 'boleto', 'transferência') NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE NULL,
    status ENUM('pending', 'paid', 'cancelled') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Adicionar colunas na tabela de Receitas
-- Como o migration.py separa por ponto-virgula, nao podemos usar procedures complexas facilmente.
-- Vamos tentar direto com IGNORE ou apenas ALTER se soubermos que eh seguro.
-- Mas para garantir idempotencia sem procedures complexas (que quebram no split), 
-- o ideal eh usar um bloco anonimo ou apenas assumir que vai rodar.
-- Vou usar uma abordagem tolerante a falhas:
-- Tenta adicionar. Se falhar (coluna existe), o script para (mas migration.py captura erro).
-- Porem, queremos que o script continue se a coluna ja existir.

-- Solucao simples: usar PROCEDURE com delimitador padrao, mas compacta.
-- Ou melhor: Se MariaDB >= 10.2, suporta IF NOT EXISTS no ALTER TABLE.
-- Vou assumir suporte a IF NOT EXISTS para simplificar, dado que funcionou no tasks.

ALTER TABLE financial_income ADD COLUMN IF NOT EXISTS status ENUM('pending', 'received', 'cancelled') NOT NULL DEFAULT 'received';
ALTER TABLE financial_income ADD COLUMN IF NOT EXISTS received_date DATE NULL;

-- Atualizar registros antigos
UPDATE financial_income SET status = 'received', received_date = entry_date WHERE status = 'received' AND received_date IS NULL;
