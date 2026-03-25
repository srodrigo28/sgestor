-- Criação da tabela de Tarefas (Tasks)
-- Relacionamento 1:N com Users (Um usuário pode ter várias tarefas)

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Status: a_fazer (to do), fazendo (doing), feito (done)
    status ENUM('a_fazer', 'fazendo', 'feito') DEFAULT 'a_fazer',
    
    -- Categorias: ex: Trabalho, Estudo, Pessoal (Opcional, pode ser livre)
    category VARCHAR(50),
    due_date DATE NULL,
    
    -- Datas de Controle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,

    -- Chave Estrangeira: Liga a tarefa ao usuário que a criou
    -- ON DELETE CASCADE: Se o usuário for deletado, suas tarefas também somem.
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
