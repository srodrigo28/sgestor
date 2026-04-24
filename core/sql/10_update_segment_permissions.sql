-- Atualiza permissões padrão conforme Plano de Gestão Multi-Segmento

-- 1. Pessoal (Foco em Tarefas e Financeiro Simples)
INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('pessoal', 'dashboard', 1),
('pessoal', 'tasks', 1),
('pessoal', 'financial', 1),
('pessoal', 'products', 0),
('pessoal', 'clients', 0),
('pessoal', 'budgets', 0),
('pessoal', 'services', 0),
('pessoal', 'admin_users', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

-- 2. Serviço (perfil historicamente salvo como 'loja')
INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('loja', 'dashboard', 1),
('loja', 'tasks', 0),
('loja', 'financial', 1),
('loja', 'products', 1),
('loja', 'clients', 1),
('loja', 'budgets', 1),
('loja', 'services', 1),
('loja', 'admin_users', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

-- 3. Oficina (Foco Total - OS, Peças, Serviços)
INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('oficina', 'dashboard', 1),
('oficina', 'tasks', 1),      -- Tarefas internas da oficina
('oficina', 'financial', 1),
('oficina', 'products', 1),   -- Peças
('oficina', 'clients', 1),
('oficina', 'budgets', 1),    -- Ordens de Serviço
('oficina', 'services', 1),   -- Mão de Obra
('oficina', 'admin_users', 0)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);

-- 4. Admin (Vê Tudo)
INSERT INTO role_menu_permissions (role, menu_key, can_view) VALUES
('admin', 'dashboard', 1),
('admin', 'tasks', 1),
('admin', 'financial', 1),
('admin', 'products', 1),
('admin', 'clients', 1),
('admin', 'budgets', 1),
('admin', 'services', 1),
('admin', 'admin_users', 1)
ON DUPLICATE KEY UPDATE can_view = VALUES(can_view);
