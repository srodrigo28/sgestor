# Memoria do Projeto

Atualizado em: 2026-02-14

## Objetivo
- Verificar conectividade com o MySQL na VPS usando as variaveis do `.env`.
- Sincronizar o banco da VPS para o MySQL local (XAMPP) com tabelas e registros.
- Separar configuracao de desenvolvimento e producao para trabalhar com seguranca.
- Melhorar o fluxo de Orçamentos para permitir métricas confiáveis (Aguardando/Aprovado/Reprovado + Orçamento/Retirar/Entregue).

## Estado Atual
- Conexao com MySQL na VPS validada (TCP + auth + `SELECT 1`).
- Banco local (XAMPP) sincronizado com a VPS: tabelas e registros importados.

## O Que Foi Feito
- Teste de rede: conexao TCP com `DB_HOST`:`DB_PORT` (porta 3306) OK.
- Teste de banco: login MySQL com `DB_USER`/`DB_PASS` e query `SELECT 1` OK.
- Dump do banco da VPS via `mysqldump` e import no MySQL do XAMPP via `mysql`.
- Validacao: quantidade de tabelas e contagem de registros por tabela conferem entre VPS e local.
- Criado script `scripts/sync_vps_to_xampp.ps1` para repetir a sincronizacao.
- Implementado selecao de arquivo de ambiente via `ENV_FILE` (ver `env_loader.py`).
- Criados exemplos `.env.dev.example` e `.env.prod.example`.
- Adicionado guard-rail em `database.py` para evitar conectar DEV em DB remoto sem intencao (`ALLOW_REMOTE_DB=1` para override).
- `migration.py` ganhou protecao extra (confirmacao quando `APP_ENV=production`).
- Documentado fluxo seguro em `docs/rotina.md` e criado `scripts/run_dev.ps1`.

## Decisoes / Combinados
- Nao registrar segredos na pasta `agente/` (ex: nao escrever `DB_PASS`).

## Proximos Passos
1. Criar `.env.dev` (local/XAMPP) e `.env.prod` (VPS) a partir dos exemplos.
2. Rodar o app em DEV com `ENV_FILE=.env.dev` (ou `scripts/run_dev.ps1`).
3. Quando precisar atualizar o banco local, rodar `scripts/sync_vps_to_xampp.ps1 -SourceEnvFile .\\.env.prod`.

## Observacoes Tecnicas
- Variaveis relevantes: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME`.

## Atualizações (Orçamentos)
Atualizado em: 2026-02-14

### Mudanças de Status (2 eixos)
- Status antigo `budgets.status` ficou limitado para compatibilidade, mas o fluxo passou a usar:
  - `approval_status`: `sent` (Aguardando), `approved` (Aprovado), `rejected` (Reprovado)
  - `stage_status`: `budget` (Orçamento), `ready_for_pickup` (Retirar), `delivered` (Entregue)
- Criados timestamps para métricas: `approved_at`, `rejected_at`, `ready_for_pickup_at`, `delivered_at`.
- Migração:
  - `sql/09_budgets_split_status.sql`
  - Lembrete manual para rodar na VPS/PROD: `docs/updates/orcamento-sql-09-split-status.sql`

### Regras de Negócio (combinadas)
- Pode existir `Aguardando + Retirar` (cliente pode retirar sem aprovar).
- Não permitimos `Aguardando + Entregue` (Entregue exige decisão Aprovado/Reprovado).
- Entregue exige ordem: primeiro Retirar, depois Entregue.

### UI/UX (lista e gráficos)
- Lista de orçamentos: agora mostra 2 badges (Etapa + Decisão) e um modal "Status Rápido" no ícone de raio (evita scroll horizontal).
- Gráficos: pizza virou 1 só com seletor (Etapa/Decisão) para não poluir a tela.
- Arquivos principais:
  - Backend: `modules/budgets.py`
  - Frontend: `templates/budgets/index.html`, `templates/budgets/view.html`, `templates/budgets/create.html`
