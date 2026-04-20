# Plano 99 - Reorganizacao MVC e Controle de Migracoes SQL

Data: 2026-02-24
Projeto: `flask-crud`

## 1) Objetivo

Organizar o projeto de forma funcional e coesa, com foco em:
- Arquitetura MVC clara.
- Fluxo unico e confiavel de migracoes SQL.
- Estrutura de pastas consistente para codigo, scripts e documentacao.

## 2) Diagnostico Atual (estado real)

1. Migracoes estao com fluxo duplicado e concorrente.
   - Existe `migration.py` com tracking em `schema_migrations`.
   - `main.py` roda migracao automatica no startup (`check_and_migrate_db`).
   - Existem scripts manuais paralelos: `apply_sql_17.py`, `apply_sql_18.py`, `apply_sql_19.py`, `apply_sql_20.py`, `apply_sql_22.py`, `fix_migration.py`, `run_migration_schedule.py`.
   - Resultado: risco de drift entre banco e tracking oficial.

2. Nomeacao de SQL nao esta padronizada.
   - Prefixos repetidos em `sql/` (`02_*`, `03_*`, `04_*`, `07_*`, `08_*`, `10_*`, `12_*`).
   - Seeds e schema estao misturados no mesmo diretorio.
   - Ordem alfabetica pode gerar dependencia fragil entre scripts.

3. MVC esta misturado nas rotas.
   - Arquivos de `modules/` concentram controller + regra de negocio + SQL.
   - Exemplo: `modules/budgets.py` e `modules/financial.py` acumulam muita responsabilidade.
   - `app/__init__.py` nao representa uma app factory real em uso.

4. Estrutura geral esta dispersa.
   - Codigo em `modules/`, `app/routes/`, scripts na raiz, backups e SQL espalhados.
   - Pastas de template com sobreposicao (`templates/admin` e `app/templates/admin`).

5. `docs/` existe, mas sem taxonomia unica.
   - Mistura de markdown, html, preview e SQL de historico no mesmo nivel.
   - Falta indice de navegacao e fluxo oficial de operacao.

## 3) Principios de Reorganizacao

1. Um unico caminho oficial para migracoes.
2. Refatoracao incremental (sem quebrar producao).
3. Separar responsabilidades por camada.
4. Documentacao viva e indexada.
5. Operacao simples: comandos curtos e previsiveis.

## 4) Estrutura Alvo (proposta)

```text
flask-crud/
  app/
    __init__.py
    config.py
    extensions/
      db.py
    controllers/
      auth_controller.py
      tasks_controller.py
      financial_controller.py
      ...
    services/
      auth_service.py
      budget_service.py
      ...
    repositories/
      auth_repository.py
      task_repository.py
      budget_repository.py
      ...
    templates/
    static/
  migrations/
    schema/
      0001__auth.sql
      0002__tasks.sql
      ...
    seed/
      9001__base_seed.sql
  scripts/
    run_dev.ps1
    db/
      backup.ps1
      restore.ps1
      new_migration.ps1
  docs/
    README.md
    architecture/
      mvc.md
      request-flow.md
    database/
      migrations.md
      naming-convention.md
      recovery-playbook.md
    operations/
      local-setup.md
      deploy.md
      backup-restore.md
    changelog/
      2026-02.md
  tests/
    test_migrations.py
    test_auth.py
```

## 5) Plano de Execucao por Fases

## Fase 0 - Contencao de Risco (1 dia)

1. Definir `migration.py` como unico executor oficial.
2. Marcar scripts paralelos como legado:
   - `apply_sql_17.py`, `apply_sql_18.py`, `apply_sql_19.py`, `apply_sql_20.py`, `apply_sql_22.py`, `fix_migration.py`, `run_migration_schedule.py`.
3. Ajustar startup para nao migrar automaticamente por padrao:
   - Em `main.py`, controlar por env (`AUTO_MIGRATE_ON_STARTUP=1` somente quando necessario).
4. Publicar politica: sem SQL manual fora do fluxo oficial.

Criterio de pronto:
- Time usa apenas `python migration.py ...`.
- Nenhum script paralelo de migracao ativo em operacao normal.

## Fase 1 - Governanca de Migracoes (2 a 3 dias)

1. Separar schema e seed em diretorios diferentes:
   - `migrations/schema`
   - `migrations/seed`
2. Padrao de nome de arquivo:
   - `NNNN__descricao_curta.sql` (4 digitos, unico, crescente).
3. Atualizar `migration.py` para:
   - Ler os dois diretorios com ordem deterministica.
   - Validar duplicidade de prefixo.
   - Falhar cedo em arquivo fora do padrao.
4. Garantir transacao por arquivo de migration (schema).
5. Manter checksum obrigatorio e imutabilidade de arquivos aplicados.
6. Criar comando de validacao:
   - `python migration.py validate` (naming, ordem, checksum, conflitos).

Criterio de pronto:
- `status`, `up`, `seed`, `all`, `stamp`, `validate` funcionando e documentados.
- Fluxo de migracao reproduzivel em ambiente limpo.

## Fase 2 - Refatoracao MVC Incremental (4 a 7 dias)

1. Criar app factory real em `app/__init__.py`.
2. Migrar rotas de `modules/` para `app/controllers/` por modulo.
3. Extrair SQL para `repositories/`.
4. Extrair regra de negocio para `services/`.
5. Controllers devem conter apenas:
   - validacao de request
   - chamada de service
   - render/redirect/response
6. Comecar por um modulo piloto de menor risco (`tasks`) e depois expandir.

Criterio de pronto:
- Pelo menos 2 modulos totalmente no padrao novo.
- Camadas separadas e testaveis sem quebrar endpoints atuais.

## Fase 3 - Reorganizacao de Documentacao (1 a 2 dias)

1. Criar `docs/README.md` como indice unico.
2. Mover conteudo para trilhas:
   - `docs/architecture/`
   - `docs/database/`
   - `docs/operations/`
   - `docs/changelog/`
3. Arquivar artefatos antigos/prototipos em:
   - `docs/archive/`
4. Registrar playbook oficial de banco:
   - backup, restore, migracao, rollback operacional.

Criterio de pronto:
- Qualquer pessoa nova no projeto consegue subir ambiente e aplicar migracoes lendo apenas docs.

## Fase 4 - Qualidade e Operacao (2 a 4 dias)

1. Criar testes minimos:
   - migracoes (`status`, `up`, `seed`, `stamp`).
   - rotas criticas (`auth`, `tasks`).
2. Padronizar verificacoes locais e CI:
   - testes automatizados
   - lint basico
3. Definir checklist de release com banco:
   - backup antes de deploy
   - migracao
   - smoke test

Criterio de pronto:
- Pipeline bloqueia merge com migracao invalida ou teste quebrado.

## 6) Fluxo Oficial de Migracoes (novo padrao)

## Desenvolvimento

1. Criar novo arquivo em `migrations/schema/NNNN__descricao.sql`.
2. Rodar `python migration.py validate`.
3. Rodar `python migration.py status`.
4. Rodar `python migration.py up`.
5. Testar funcionalidade relacionada.

## Producao

1. Gerar backup completo antes do deploy.
2. Rodar `python migration.py status`.
3. Rodar `python migration.py up`.
4. Executar smoke test das rotas afetadas.
5. Registrar resultado em `docs/changelog/`.

## 7) Lista de Limpeza de Estrutura

1. Remover scripts de migracao avulsos da raiz apos consolidacao.
2. Mover dumps SQL de backup para `backups/` (fora da raiz).
3. Resolver duplicidade de templates admin e manter apenas uma origem.
4. Centralizar entrypoint da aplicacao (evitar fluxo espalhado entre `setup.py` e `main.py`).

## 8) Entregaveis esperados

1. Arquitetura de pastas reorganizada conforme alvo.
2. `migration.py` endurecido e sem caminhos paralelos.
3. `docs/` com indice e playbooks de operacao.
4. Refatoracao MVC iniciada com modulo piloto completo.
5. Checklist de release e testes minimos automatizados.

## 9) Ordem recomendada de implementacao

1. Fase 0
2. Fase 1
3. Fase 3
4. Fase 2
5. Fase 4

Motivo:
- Primeiro eliminar risco de banco.
- Depois garantir governanca e documentacao.
- Em seguida escalar refatoracao MVC com mais seguranca.
