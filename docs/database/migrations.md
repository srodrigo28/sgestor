# Politica de Migrations SQL

Data de vigencia: 2026-02-24

## Fluxo oficial

O unico fluxo oficial de migracao e via:

```bash
python db/migration.py <comando>
```

Comandos principais:
- `python db/migration.py status`
- `python db/migration.py up`
- `python db/migration.py seed`
- `python db/migration.py all`
- `python db/migration.py stamp`

## Regras operacionais

1. Nao editar migration antiga ja aplicada em producao.
2. Nao executar SQL manual por scripts avulsos.
3. Sempre rodar `status` antes de `up` em deploy.
4. Fazer backup antes de migrar em producao.

## Scripts legados

Os scripts abaixo estao marcados como legados e so redirecionam para `db/migration.py`:
- `apply_sql_17.py`
- `apply_sql_18.py`
- `apply_sql_19.py`
- `apply_sql_20.py`
- `apply_sql_22.py`
- `fix_migration.py`
- `run_migration_schedule.py`

## Startup da aplicacao

`manage.py` (via create_app) nao roda migration automaticamente por padrao.

Para habilitar explicitamente:

```bash
AUTO_MIGRATE_ON_STARTUP=1
```


