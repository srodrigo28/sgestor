# Rotina Segura (Desenvolvimento x Producao)

Objetivo: desenvolver localmente sem risco de alterar o banco/ambiente do cliente.

## 1) Separar arquivos de ambiente

- Desenvolvimento (local): `.env.dev` (nao versionado)
  - Base: `.env.dev.example`
  - Deve apontar para o MySQL do XAMPP (`127.0.0.1`)

- Producao (VPS): `.env.prod` (nao versionado)
  - Base: `.env.prod.example`
  - Deve apontar para o MySQL da VPS

O projeto suporta selecionar o arquivo via variavel `ENV_FILE`.

## 2) Como rodar com o env correto

### Windows (PowerShell)

- Rodar em DEV (local):
```powershell
$env:ENV_FILE = ".env.dev"
python main.py
```

- Rodar apontando para PROD (so se for intencional):
```powershell
$env:ENV_FILE = ".env.prod"
python main.py
```

### Linux (VPS)

- Exemplo com gunicorn:
```bash
export ENV_FILE=.env.prod
gunicorn -w 2 -b 127.0.0.1:5050 main:app
```

## 3) Protecoes implementadas

- `database.py` bloqueia conexao com `DB_HOST` nao-local quando `APP_ENV != production`.
  - Para permitir conscientemente, set `ALLOW_REMOTE_DB=1` (nao recomendado no dia a dia).

- `migration.py`:
  - Bloqueia migracao em host remoto quando `APP_ENV != production` (mesma regra).
  - Quando `APP_ENV=production`, pede confirmacao digitando `PRODUCTION` (a menos que `ALLOW_PROD_MIGRATIONS=1`).

## 4) Sincronizar dados (VPS -> XAMPP)

Fluxo recomendado: sempre puxar dados de PROD para DEV (nunca o contrario).

```powershell
.\scripts\sync_vps_to_xampp.ps1 -SourceEnvFile .\.env.prod -Force
```

## 5) Rotina para mudancas sem quebrar o cliente

1. Desenvolver e testar sempre em DEV (local).
2. Se precisar de dados reais, sincronizar PROD -> DEV.
3. Para mudancas de schema:
   - criar/atualizar scripts em `sql/`
   - rodar no DEV primeiro
   - fazer backup do banco de PROD antes de aplicar
4. Deploy:
   - subir codigo
   - aplicar migrations (com janela/backup)
   - validar endpoints/telas principais

## 6) Automatizando deploy (opcional)
Veja `docs/cicd.md` para um script bash controlado e um exemplo de GitHub Actions (CI/CD).
