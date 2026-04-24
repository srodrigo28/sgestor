DELETE FROM role_menu_permissions
WHERE role IS NULL OR role = ''
   OR role NOT IN ('admin','oficina','loja','atendimentos','pessoal');

ALTER TABLE role_menu_permissions
MODIFY COLUMN role ENUM('admin','oficina','loja','atendimentos','pessoal') NOT NULL;

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'attendance', 1),
('oficina', 'attendance', 0),
('loja', 'attendance', 0),
('atendimentos', 'attendance', 1),
('pessoal', 'attendance', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'mechanics', 1),
('oficina', 'mechanics', 1),
('loja', 'mechanics', 0),
('atendimentos', 'mechanics', 0),
('pessoal', 'mechanics', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'schedule', 1),
('oficina', 'schedule', 1),
('loja', 'schedule', 0),
('atendimentos', 'schedule', 1),
('pessoal', 'schedule', 1)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'tasks', 1),
('oficina', 'tasks', 1),
('loja', 'tasks', 0),
('atendimentos', 'tasks', 1),
('pessoal', 'tasks', 1)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'financial', 1),
('oficina', 'financial', 1),
('loja', 'financial', 1),
('atendimentos', 'financial', 1),
('pessoal', 'financial', 1)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'clients', 1),
('oficina', 'clients', 1),
('loja', 'clients', 1),
('atendimentos', 'clients', 1),
('pessoal', 'clients', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'products', 1),
('oficina', 'products', 1),
('loja', 'products', 1),
('atendimentos', 'products', 0),
('pessoal', 'products', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'budgets', 1),
('oficina', 'budgets', 1),
('loja', 'budgets', 1),
('atendimentos', 'budgets', 0),
('pessoal', 'budgets', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'services', 1),
('oficina', 'services', 1),
('loja', 'services', 1),
('atendimentos', 'services', 0),
('pessoal', 'services', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'admin_users', 1),
('oficina', 'admin_users', 0),
('loja', 'admin_users', 0),
('atendimentos', 'admin_users', 0),
('pessoal', 'admin_users', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);
