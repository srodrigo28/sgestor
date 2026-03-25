-- Add CLT fields to mechanics table
ALTER TABLE mechanics ADD COLUMN cpf VARCHAR(14) AFTER phone;
ALTER TABLE mechanics ADD COLUMN rg VARCHAR(20) AFTER cpf;
ALTER TABLE mechanics ADD COLUMN pis_pasep VARCHAR(20) AFTER rg;
ALTER TABLE mechanics ADD COLUMN ctps_number VARCHAR(20) AFTER pis_pasep;
ALTER TABLE mechanics ADD COLUMN ctps_series VARCHAR(10) AFTER ctps_number;
ALTER TABLE mechanics ADD COLUMN mother_name VARCHAR(100) AFTER ctps_series;
ALTER TABLE mechanics ADD COLUMN father_name VARCHAR(100) AFTER mother_name;
ALTER TABLE mechanics ADD COLUMN education_level ENUM('Fundamental Incompleto', 'Fundamental Completo', 'Médio Incompleto', 'Médio Completo', 'Superior Incompleto', 'Superior Completo', 'Pós-graduação') AFTER father_name;
ALTER TABLE mechanics ADD COLUMN marital_status ENUM('Solteiro(a)', 'Casado(a)', 'Divorciado(a)', 'Viúvo(a)', 'União Estável') AFTER education_level;
ALTER TABLE mechanics ADD COLUMN salary DECIMAL(10, 2) AFTER marital_status;
ALTER TABLE mechanics ADD COLUMN num_dependents INT DEFAULT 0 AFTER salary;
