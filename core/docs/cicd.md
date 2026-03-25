# Deploy Controlado (VPS) com Script Bash e/ou GitHub Actions

Este projeto funciona melhor com este modelo:
- Codigo vai via Git (push/pull).
- Configuracao de producao fica na VPS (arquivo `.env`), fora do Git.

Assim voce atualiza o app sem risco de "subir senha" para o GitHub e sem apontar DEV para o banco do cliente.

## Opcao A: Script Bash na VPS (manual, 1 comando)

### 1) Pre-requisitos (uma vez)
- Repo clonado na VPS (ex: `/var/www/curso-flask`).
- Arquivo `/var/www/curso-flask/.env` com:
  - `APP_ENV=production`
  - `APP_DEBUG=0`
  - `DB_HOST/DB_PORT/DB_USER/DB_PASS/DB_NAME`
  - `SECRET_KEY` (nao pode ficar vazio)
- Um servico para rodar o app (recomendado: systemd + gunicorn), ou Docker Compose.

### 2) Script de deploy (exemplo)
Crie um arquivo na VPS, por exemplo: `/var/www/curso-flask/deploy.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/curso-flask}"
BRANCH="${BRANCH:-main}"
ENV_FILE="${ENV_FILE:-.env}"
SERVICE_NAME="${SERVICE_NAME:-curso-flask}"
PORT="${PORT:-5050}"

cd "$APP_DIR"

# Evita dois deploys ao mesmo tempo
exec 200>/tmp/flask-crud-deploy.lock
flock -n 200 || { echo "Deploy ja esta em execucao. Saindo."; exit 1; }

echo "==> Atualizando codigo ($BRANCH)"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "==> Checando ENV"
test -f "$ENV_FILE" || { echo "Arquivo $ENV_FILE nao encontrado em $APP_DIR"; exit 1; }
grep -q '^APP_ENV=production' "$ENV_FILE" || { echo "APP_ENV nao esta como production em $ENV_FILE"; exit 1; }
grep -qE '^SECRET_KEY=.+$' "$ENV_FILE" || { echo "SECRET_KEY vazio/ausente em $ENV_FILE"; exit 1; }

echo "==> Dependencias (venv)"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

echo "==> Restart do servico"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl is-active --quiet "$SERVICE_NAME"

echo "==> Healthcheck simples"
code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/" || true)"
echo "HTTP status: $code"

echo "DEPLOY OK"
```

Permissao:
```bash
chmod +x /var/www/curso-flask/deploy.sh
```

Executar:
```bash
/var/www/curso-flask/deploy.sh
```

Notas:
- `git pull --ff-only` evita merge acidental.
- Migrations: este projeto tem `migration.py` interativo. Em producao, faca manualmente com backup antes.

## Opcao B: GitHub Actions (CI/CD) chamando o script da VPS

Modelo simples e seguro: o GitHub Actions faz SSH na VPS e roda `deploy.sh`.

### 1) Secrets no GitHub
No repo: Settings -> Secrets and variables -> Actions -> New repository secret

Crie:
- `VPS_HOST` (IP/DNS)
- `VPS_USER` (usuario de deploy)
- `VPS_SSH_KEY` (chave privada)
- `VPS_PORT` (opcional, ex: 22)
- `VPS_APP_DIR` (ex: `/var/www/curso-flask`)

### 2) Workflow exemplo
Crie `.github/workflows/deploy.yml` no repo (exemplo):

```yaml
name: Deploy VPS

on:
  workflow_dispatch:
  push:
    branches: [ "main" ]

concurrency:
  group: deploy-vps
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: SSH deploy
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_PORT }}
          script: |
            cd "${{ secrets.VPS_APP_DIR }}"
            ./deploy.sh
```

Notas:
- Recomendo manter o deploy manual tambem (`workflow_dispatch`) para quando precisar controlar janela/backup.
- O Action nao envia `.env` para a VPS. O `.env` deve existir no servidor.

## Checklist rapido (na pratica)
- DEV (seu PC): `.env` aponta para XAMPP e `APP_ENV=development`.
- PROD (VPS): `.env` aponta para VPS e `APP_ENV=production` + `SECRET_KEY`.
- Atualizar PROD: `git push` -> na VPS `git pull` (ou Action) -> restart do servico.

