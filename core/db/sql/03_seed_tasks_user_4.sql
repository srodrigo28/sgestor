-- Inserir 20 tarefas para o usuário 4
-- Distribuição para testar gráficos (últimos 7 dias)

-- Cria usuario 4 se nao existir (para garantir fk)
INSERT IGNORE INTO users (id, name, email, password, phone, created_at) VALUES 
(4, 'Usuario Oficina', 'oficina@teste.com', '123456', '11999999999', NOW());

-- Tarefas Concluídas (Feito) - Variando os dias para o gráfico de linha
INSERT INTO tasks (user_id, title, description, category, status, created_at, completed_at) VALUES
(4, 'Revisar documentação', 'Verificar erros de português', 'Trabalho', 'feito', NOW() - INTERVAL 7 DAY, NOW() - INTERVAL 7 DAY),
(4, 'Backup do banco', 'Gerar dump completo', 'Trabalho', 'feito', NOW() - INTERVAL 6 DAY, NOW() - INTERVAL 6 DAY),
(4, 'Atualizar libs', 'Pip upgrade', 'Estudo', 'feito', NOW() - INTERVAL 6 DAY, NOW() - INTERVAL 6 DAY),
(4, 'Reunião cliente', 'Alinhamento de expectativas', 'Trabalho', 'feito', NOW() - INTERVAL 5 DAY, NOW() - INTERVAL 5 DAY),
(4, 'Comprar café', 'Acabou o estoque', 'Pessoal', 'feito', NOW() - INTERVAL 4 DAY, NOW() - INTERVAL 4 DAY),
(4, 'Estudar Flask', 'Ler sobre Blueprints', 'Estudo', 'feito', NOW() - INTERVAL 4 DAY, NOW() - INTERVAL 4 DAY),
(4, 'Exercício físico', 'Corrida 5km', 'Saúde', 'feito', NOW() - INTERVAL 3 DAY, NOW() - INTERVAL 3 DAY),
(4, 'Pagar contas', 'Luz e Internet', 'Pessoal', 'feito', NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 2 DAY),
(4, 'Deploy homologação', 'Subir versão v1.2', 'Trabalho', 'feito', NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 1 DAY),
(4, 'Escrever relatório', 'Resultados do mês', 'Trabalho', 'feito', NOW(), NOW());

-- Tarefas Fazendo
INSERT INTO tasks (user_id, title, description, category, status, created_at) VALUES
(4, 'Desenvolver API', 'Criar endpoints REST', 'Trabalho', 'fazendo', NOW()),
(4, 'Ler livro Clean Code', 'Capítulo 3', 'Estudo', 'fazendo', NOW()),
(4, 'Planejar viagem', 'Ver passagem aérea', 'Pessoal', 'fazendo', NOW()),
(4, 'Dieta da semana', 'Comprar legumes', 'Saúde', 'fazendo', NOW());

-- Tarefas A Fazer
INSERT INTO tasks (user_id, title, description, category, status, created_at) VALUES
(4, 'Format PC', 'Instalar Windows 11', 'Pessoal', 'a_fazer', NOW()),
(4, 'Curso de React', 'Comprar na Udemy', 'Estudo', 'a_fazer', NOW()),
(4, 'Dentista', 'Marcar limpeza', 'Saúde', 'a_fazer', NOW()),
(4, 'Trocar óleo carro', 'Revisão 50k', 'Pessoal', 'a_fazer', NOW()),
(4, 'Atualizar LinkedIn', 'Adicionar projetos', 'Trabalho', 'a_fazer', NOW()),
(4, 'Organizar arquivos', 'Limpar área de trabalho', 'Pessoal', 'a_fazer', NOW());
