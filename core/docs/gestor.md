# SGestor: comandos uteis de administracao

Este arquivo serve como cola rapida para operacao do sistema via terminal.

## Entrar na pasta do projeto

```powershell
cd C:\prod\sgestor\core
```

## Ver configuracao basica do banco

Confira o `.env`:

```powershell
Get-Content .env
```

Teste se o banco responde na porta esperada:

```powershell
Test-NetConnection 127.0.0.1 -Port 3306
```

## Ver usuarios administradores

Se tiver cliente MySQL no ambiente:

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "SELECT id, name, email, role FROM users WHERE role = 'admin' ORDER BY id;"
```

## Ver todos os usuarios

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "SELECT id, name, email, role, created_at FROM users ORDER BY id;"
```

## Verificar como a senha esta armazenada

Atencao: em ambientes antigos pode haver senha em texto puro; em contas novas o sistema pode migrar para hash no login.

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "SELECT id, email, password FROM users WHERE role = 'admin' ORDER BY id;"
```

## Criar ou atualizar o admin padrao da 99dev

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "INSERT INTO users (name, email, phone, password, role) VALUES ('Administrador 99Dev', 'admin@99dev.pro', '', '123123', 'admin') ON DUPLICATE KEY UPDATE name = VALUES(name), phone = VALUES(phone), password = VALUES(password), role = 'admin';"
```

## Promover um usuario existente para admin

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "UPDATE users SET role = 'admin' WHERE email = 'aline@gmail.com';"
```

## Trocar senha de um usuario pelo terminal

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "UPDATE users SET password = '123123' WHERE email = 'admin@99dev.pro';"
```

## Rodar migracoes do projeto

Aplicar schema:

```powershell
python db\migration.py up
```

Aplicar apenas seeds:

```powershell
python db\migration.py seed
```

Aplicar schema e seeds:

```powershell
python db\migration.py all
```

## Gerador manual de admin

Usa os valores do `.env` quando disponiveis:

```powershell
python manager\gerar_admin.py
```

## Ver scripts SQL disponiveis

```powershell
Get-ChildItem .\db\sql
```

## Ver status das migracoes

```powershell
python db\migration.py status
```

## Ver scripts e ferramentas auxiliares

```powershell
Get-ChildItem .\scripts
Get-ChildItem .\manager
```

## Rodar testes rapidos

Todos os testes:

```powershell
python -m pytest
```

Somente testes de um arquivo:

```powershell
python -m pytest tests\test_painel_unit.py
```

Somente um teste com filtro:

```powershell
python -m pytest -k admin
```

## Ver estrutura do projeto

```powershell
Get-ChildItem .
Get-ChildItem .\apps
Get-ChildItem .\templates
Get-ChildItem .\docs
```

## Procurar uma rota, funcao ou texto

Exemplos:

```powershell
rg "financial_categories" .
rg "admin@99dev.pro" .
rg "login_required" .\apps
```

## Validar arquivos Python sem executar a app

```powershell
python -m py_compile .\apps\auth\views.py
python -m py_compile .\apps\admin\views.py
python -m py_compile .\apps\financial\views.py
```

## Rodar a aplicacao localmente

```powershell
python app.py
```

Se o projeto usar outro ponto de entrada, confira os arquivos da raiz antes:

```powershell
Get-ChildItem .\
```

## Logs e diagnostico

Ver processos Python ativos:

```powershell
Get-Process | Where-Object { $_.ProcessName -like '*python*' }
```

Ver portas em uso:

```powershell
netstat -ano | findstr :5000
netstat -ano | findstr :3306
```

Testar se a aplicacao responde:

```powershell
Invoke-WebRequest http://127.0.0.1:5000
```

## Backup e restauracao

Abrir o modulo pelo sistema:

- rota: `/admin/backup`

Ver arquivo de backup temporario:

```powershell
Get-ChildItem .\tmp
```

## Rotinas uteis do dia a dia

Atualizar um usuario para admin:

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "UPDATE users SET role = 'admin' WHERE email = 'usuario@dominio.com';"
```

Listar categorias financeiras no arquivo:

```powershell
Get-Content .\config\financial_categories.json
```

Ver se o usuario padrao da 99dev existe:

```powershell
mysql -h 127.0.0.1 -u root -p -D flask_crud -e "SELECT id, name, email, role FROM users WHERE email = 'admin@99dev.pro';"
```

## Observacoes

- Mudanca feita direto no banco nao exige restart da aplicacao.
- Mudanca de codigo exige novo deploy ou restart.
- Se o login falhar mesmo com o usuario criado, confira primeiro `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS` e `DB_NAME` no `.env`.
