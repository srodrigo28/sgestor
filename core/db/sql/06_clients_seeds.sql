-- Arquivo: sql/06_clients_seeds.sql

-- Inserindo dados de teste (Seeds)
-- Assume que existe o user_id = 1 (Admin padrão)

INSERT INTO clients (user_id, name, phone1, phone2, cpf, sector) VALUES
(1, 'João da Silva', '(11) 99999-1234', '(11) 3333-0000', '123.456.789-00', 'Varejo'),
(1, 'Maria Oliveira', '(21) 98888-5555', NULL, '987.654.321-99', 'Serviços'),
(1, 'Tech Solutions Ltda', '(31) 97777-8888', '(31) 3222-1111', '12.345.678/0001-90', 'Atacado'),
(1, 'Padaria do Joaquim', '(11) 95555-4444', NULL, '11.222.333/0001-55', 'Varejo'),
(1, 'Consultoria ABC', '(41) 96666-7777', NULL, '55.666.777/0001-88', 'Serviços');
