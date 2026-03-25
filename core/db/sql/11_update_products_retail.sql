-- Atualização da Tabela de Produtos para Lojas (Retail Standard)

ALTER TABLE products
ADD COLUMN IF NOT EXISTS sku VARCHAR(50) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS cost_price DECIMAL(10, 2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS min_stock INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS images JSON DEFAULT NULL;

-- Atualizar produtos existentes para ter SKU básico se estiver vazio
UPDATE products SET sku = CONCAT('PROD-', id) WHERE sku IS NULL;
