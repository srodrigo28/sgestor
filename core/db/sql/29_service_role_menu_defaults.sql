-- Renomeio visual do perfil "loja" para "Serviço".
-- A chave interna continua "loja" para preservar usuários e permissões existentes.

DELETE FROM role_menu_permissions
WHERE role IS NULL OR role = ''
   OR role NOT IN ('admin','oficina','loja','atendimentos','pessoal');

ALTER TABLE role_menu_permissions
MODIFY COLUMN role ENUM('admin','oficina','loja','atendimentos','pessoal') NOT NULL;

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('loja', 'services', 1)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);
