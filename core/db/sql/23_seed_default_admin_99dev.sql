INSERT INTO users (name, email, phone, password, role)
VALUES ('Administrador 99Dev', 'admin@99dev.pro', '', '123123', 'admin')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    password = VALUES(password),
    role = 'admin';
