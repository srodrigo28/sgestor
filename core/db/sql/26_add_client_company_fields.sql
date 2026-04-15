ALTER TABLE clients
ADD COLUMN legal_name VARCHAR(150) NULL AFTER name,
ADD COLUMN trade_name VARCHAR(150) NULL AFTER legal_name,
ADD COLUMN contract_start_date DATE NULL AFTER sector;
