-- Arquivo: sql/04_products.sql

-- Feature Flag para o usuário (Adiciona se não existir)
-- Nota: Em MySQL 5.7+ não existe 'IF NOT EXISTS' direto em ADD COLUMN, então usar procedure ou ignorar erro é comum.
-- Aqui vamos assumir que pode falhar se já existir, ou rodar manual.
-- ALTER TABLE users ADD COLUMN has_product_module BOOLEAN DEFAULT TRUE;

-- Criação da tabela de Fornecedores
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Criação da tabela de Produtos
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    supplier_id INT,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    barcode VARCHAR(100),
    quantity INT DEFAULT 0,
    min_quantity INT DEFAULT 0,
    cost_price DECIMAL(10, 2) DEFAULT 0.00,
    sell_price DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);
