# Deploy

## 1. Lista de arquivos para excluir (raiz)
Remova se **nao** forem usados em producao:
- venv/
- __pycache__/
- preview/
- test_budget_actions.py
- debug_db.py
- check_data.py
- check_migration.py
- check_schema.py
- apply_migration_simple.py
- force_migration.py
- migration_script.py
- plano-sistema.md
- plano2.md
- estoque.md

Arquivos/pastas que normalmente ficam:
- main.py
- routes.py
- database.py
- templates/
- modules/
- sql/
- README.md (opcional)
- setup.py (se o app for instalado como pacote)

## 2. Fazer dump do banco (MySQL/MariaDB)
Dados informados:
- HOST: 76.13.225.77
- PORTA: 3306
- USER: rodrigo
- DB: flask_crud

Com senha solicitada no terminal:
- mysqldump -h 76.13.225.77 -P 3306 -u rodrigo -p flask_crud > backup.sql

Opcional (nao expor a senha no historico):
- set "MYSQL_PWD=SUASENHA" && mysqldump -h 76.13.225.77 -P 3306 -u rodrigo flask_crud > backup.sql

## 3. Clonar na VPS Ubuntu
- git clone https://github.com/srodrigo28/flask-crud.git /var/www/curso-flask
- cd /var/www/curso-flask
- instalar Python e venv (se faltar):
  - sudo apt update
  - sudo apt install -y python3 python3-venv python3-pip
- criar venv e instalar deps:
  - python3 -m venv venv
  - source venv/bin/activate
  - pip install -r requirements.txt

## 4. Subir o banco no clone (MySQL/MariaDB)
Com senha solicitada no terminal:
- mysql -h 76.13.225.77 -P 3306 -u rodrigo -p flask_crud < backup.sql

Opcional (nao expor a senha no historico):
- export MYSQL_PWD='SUASENHA'
- mysql -h 76.13.225.77 -P 3306 -u rodrigo flask_crud < backup.sql

## 5. Gunicorn (resumo)
Gunicorn eh o servidor WSGI recomendado para rodar Flask em producao.

Seu app Flask esta em `main.py` e se chama `app`.
Comando sugerido:
- gunicorn -w 2 -b 127.0.0.1:5050 main:app

### Variaveis de ambiente (recomendado)
- Defina `APP_ENV=production`
- Defina `SECRET_KEY` (nao usar o fallback)
- Para usar um arquivo separado, defina `ENV_FILE=.env.prod` e mantenha esse arquivo apenas no servidor (nao versionar)

## 6. Mapear no Nginx
Exemplo de site:
- /etc/nginx/sites-available/curso-flask

server {
    listen 80;
    server_name <DOMINIO>;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

- ln -s /etc/nginx/sites-available/curso-flask /etc/nginx/sites-enabled/
- nginx -t
- systemctl reload nginx

## 7. Mapear porta na VPS Hostinger
- Liberar a porta do app (5050) no firewall/UFW e no painel da Hostinger.

UFW (exemplo):
- sudo ufw allow 5050/tcp
- sudo ufw reload

## Observacoes
- Substitua <DOMINIO> conforme seu ambiente.
- Para producao, usar gunicorn + systemd para manter o app em execucao.
- Atualize `app.secret_key` para um valor seguro em producao.
