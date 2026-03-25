# Migrations SQL (`sql/`)

Esta pasta guarda scripts SQL para criar/atualizar o schema do banco.

## Convencoes
- A ordem de execucao e pelo nome do arquivo (ordem alfabetica).
- Scripts de seed (dados de exemplo) devem conter `seed` no nome e sao opcionais.
- Evite editar scripts antigos depois que ja foram aplicados em producao.
  - Se precisar mudar algo, crie um novo arquivo `.sql` (migration nova).

## Como saber o que e novo vs antigo
O `migration.py` cria uma tabela `schema_migrations` no banco para registrar:
- `filename`, `checksum`, `kind` (schema/seed) e `applied_at`.

Com isso voce consegue ver:
- **Pendentes (novas)**: arquivos que ainda nao estao na `schema_migrations`
- **Aplicadas (antigas)**: arquivos que ja estao registradas

## Comandos (DEV / PROD)
Ver status:
```bash
python db/migration.py status
```

Aplicar apenas schema (sem seeds):
```bash
python db/migration.py up
```

Aplicar apenas seeds:
```bash
python db/migration.py seed
```

Aplicar schema + seeds:
```bash
python db/migration.py all
```

Bootstrap (banco ja existe, mas ainda nao tinha tracking):
```bash
python db/migration.py stamp
python db/migration.py stamp --include-seeds
```

## Seguranca (importante)
- Em DEV: o `migration.py` bloqueia DB remoto se `APP_ENV != production` (a menos que `ALLOW_REMOTE_DB=1`).
- Em PROD: o `migration.py` pede confirmacao digitando `PRODUCTION` (a menos que `ALLOW_PROD_MIGRATIONS=1`).


