-- Adiciona a previsao de conclusao (due_date) na tabela de tarefas.
-- Observacao: Tentativa de usar IF NOT EXISTS (MySQL 8.0.29+ / MariaDB 10.2+)
-- Caso falhe, sera necessario usar procedure. Mas como migration 11 usa, vamos tentar aqui.

ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS due_date DATE NULL AFTER category;

