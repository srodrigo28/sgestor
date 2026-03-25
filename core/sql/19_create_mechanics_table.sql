CREATE TABLE IF NOT EXISTS mechanics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    birth_date DATE,
    address_cep VARCHAR(20),
    address_street VARCHAR(255),
    address_number VARCHAR(50),
    address_district VARCHAR(100),
    address_city VARCHAR(100),
    address_state VARCHAR(2),
    experience_years INT,
    photo_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

ALTER TABLE budgets
ADD COLUMN mechanic_id INT,
ADD CONSTRAINT fk_budgets_mechanic FOREIGN KEY (mechanic_id) REFERENCES mechanics(id) ON DELETE SET NULL;
