-- 1. Criar o Banco de Dados (se não existir)
CREATE DATABASE IF NOT EXISTS flask_crud;
USE flask_crud;

-- 2. Criar a Tabela de Usuários (se não existir)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Inserir um admin padrão (somente se não existir ninguém)
-- O IGNORE evita erro se o email já existir
INSERT IGNORE INTO users (name, email, phone, password) 
VALUES ('Administrador', 'admin@sistema.com', '00000000000', 'admin123');
