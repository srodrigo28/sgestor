-- Arquivo: sql/10_appointments.sql

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    client_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status ENUM('scheduled', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
);

-- Adicionar permissão padrão para o módulo de agendamento em role_menu_permissions se a tabela existir
-- (Isso pode falhar se a tabela não existir, mas geralmente em MySQL scripts subsequentes rodam ok)
INSERT IGNORE INTO role_menu_permissions (role, menu_key, can_view) VALUES 
('admin', 'schedule', TRUE),
('pessoal', 'schedule', TRUE),
('comercial', 'schedule', TRUE);
