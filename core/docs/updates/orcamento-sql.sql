-- Atualiza o ENUM de status do orcamento para suportar o novo fluxo.
-- Observacao: precisa listar todos os valores do ENUM.

ALTER TABLE budgets
    MODIFY COLUMN status ENUM(
        'draft',
        'sent',
        'approved',
        'rejected',
        'ready_for_pickup',
        'delivered',
        'completed'
    ) NOT NULL DEFAULT 'draft';

