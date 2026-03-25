ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'pessoal';

UPDATE users SET role = 'admin' WHERE email = 'admin@sistema.com';
UPDATE users SET role = 'oficina' WHERE email LIKE '%oficina%';
UPDATE users SET role = 'loja' WHERE email LIKE '%loja%';
