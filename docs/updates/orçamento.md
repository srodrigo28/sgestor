# Plano: Melhorar Fluxo de Orcamento e Aprovacao

## Objetivo
Evoluir o fluxo do modulo de orcamentos para ter um funil claro (status + datas) e permitir indicadores como:
- quantos aprovados por semana
- quantos reprovados por semana
- quantos prontos para retirada por dia ("liberados no dia")
- quantos entregues por dia

SQL (para rodar na VPS): `docs/updates/orcamento-sql-09-split-status.sql`

## O Que Ja Existe Hoje (Funcionalidades)

### Status atuais (DB/UI)
Historicamente o sistema usava apenas `budgets.status` (1 coluna) para representar tudo, o que gerava confusao.

Agora vamos separar em 2 eixos (2 colunas), mantendo poucos valores e permitindo combinacoes:

1) Decisao do orcamento (funil de aprovacao):
- `budgets.approval_status` (ENUM):
  - `sent` (aguardando)
  - `approved` (aprovado)
  - `rejected` (reprovado)

2) Etapa do veiculo (operacao):
- `budgets.stage_status` (ENUM):
  - `budget` (orcamento)
  - `ready_for_pickup` (retirar)
  - `delivered` (entregue)

Mapa simples (como o time fala hoje):
| Negocio | Codigo atual |
| --- | --- |
| aguardando | `approval_status=sent` |
| aprovado | `approval_status=approved` |
| reprovado | `approval_status=rejected` |
| orcamento | `stage_status=budget` |
| retirar | `stage_status=ready_for_pickup` |
| entregue | `stage_status=delivered` |

### Telas e acoes
- Listagem `/budgets`
  - busca por cliente/placa/id
  - cards com estatisticas (total, valor aprovado, ultimos 30 dias, ticket medio)
  - graficos:
    - historico de valor por mes (6 meses) ou por dia (mes selecionado)
    - distribuicao de status (ultimos 12 meses ou mes selecionado)
- Criacao `/budgets/create` + `/budgets/save`
  - cria/atualiza cliente e veiculo automaticamente
  - salva itens e total, desconto, observacoes, expiracao (7 dias)
  - status default: `sent` (aguardando)
- Visualizacao `/budgets/view/<id>`
  - edicao de itens, desconto, observacoes, KM, status (select)
  - botao "Aprovar" abre modal e gera/atualiza registro no financeiro (`financial_income`) e marca `status=approved`
  - impressao `/budgets/print/<id>`

### Integracao com Financeiro
- Ao aprovar via modal (`/budgets/approve_financial/<id>`), o sistema:
  - muda o budget para `approved`
  - cria/atualiza `financial_income` com `budget_id`, `amount`, `payment_type`, `entry_date`

## Problemas do Fluxo Atual (pontos que impedem KPI)
- Misturar decisao (aprovado/reprovado) com etapa (retirar/entregue) em 1 campo impede combinacoes.
- Nao existe um campo dedicado para datas de mudanca de status (ex: `approved_at`, `rejected_at`, etc).
  - Usar `updated_at` nao e confiavel porque ele muda em qualquer edicao (itens/obs/desconto).
- O status pode ser alterado manualmente pelo select, mas nem sempre executa as acoes colaterais esperadas
  - Ex: mudar para `approved` pelo select nao gera financeiro; isso hoje so acontece pelo modal de aprovar.
- Nao existe log/historico de mudancas (auditoria) para saber "quem mudou" e "quando mudou".

## Status Necessarios (minimo possivel)
O conjunto total de status (na operacao) fica pequeno e claro:
- Aguardando / Aprovado / Reprovado (decisao)
- Orcamento / Retirar / Entregue (etapa)

## Definicao do Fluxo (estado e transicoes)
Fluxo minimo (proposto):
- Decisao:
  - `approval_status=sent` -> `approved` ou `rejected`
- Etapa:
  - `stage_status=budget` -> `ready_for_pickup` -> `delivered`

Regras importantes (para evitar bagunca nos numeros):
- Definir transicoes permitidas (state machine) e bloquear o restante no backend.
- Sempre registrar a data do evento quando o status muda.

## Dados Necessarios Para Relatorios
Opcoes (escolher 1):

### Opcao 1 (simples): colunas de data no budgets
Adicionar campos (DATETIME ou TIMESTAMP) na tabela `budgets`:
- `approved_at`
- `rejected_at`
- `ready_for_pickup_at`
- `delivered_at`

Vantagens:
- Queries simples para KPI diario/semanal.

Desvantagens:
- Se alguem "voltar status" e aprovar de novo, pode sobrescrever datas e distorcer metricas.

### Opcao 2 (robusta): tabela de historico de status
Criar tabela `budget_status_history`:
- `id`
- `budget_id`
- `from_status`
- `to_status`
- `changed_by_user_id`
- `changed_at`
- `notes` (motivo, opcional)

Vantagens:
- Auditoria completa e metricas por evento (mais correto).

Desvantagens:
- Mais trabalho e mais queries.

Recomendacao: Opcao 2 para longo prazo. Opcao 1 da velocidade para comecar.

## KPI / Relatorios (definicoes)
Definir os indicadores usando a data do evento (nao `created_at`, nao `updated_at`):
- Aprovados por semana: contar eventos `approved` por `YEARWEEK(approved_at)` (ou history).
- Reprovados por semana: contar eventos `rejected` por semana.
- Prontos para retirada por dia: contar eventos `ready_for_pickup` por `DATE(ready_for_pickup_at)`.
- Entregues por dia: contar eventos `delivered` por `DATE(delivered_at)`.

## Plano de Implementacao (passos)
1. Definir nomes finais dos status (codigo e label):
   - Decisao: `sent`, `approved`, `rejected`
   - Etapa: `budget`, `ready_for_pickup`, `delivered`
2. Banco de dados:
   - adicionar colunas `approval_status` + `stage_status`
   - criar colunas de datas (Opcao 1) ou tabela de historico (Opcao 2)
3. Backend:
   - centralizar alteracao de status em um unico endpoint/funcao
   - validar transicoes permitidas
   - ao mudar status, gravar a data do evento (e inserir no historico, se existir)
4. Frontend (telas):
   - badge e cores para novos status
   - botoes rapidos para avancar no fluxo (ex: "Pronto p/ retirada", "Entregue")
   - filtro por status na listagem
5. Dashboard / relatorios:
   - cards/relatorios com os KPIs solicitados (dia/semana)
6. Backfill (dados antigos):
   - decidir como preencher `*_at` para budgets ja existentes (ex: usar `updated_at` como aproximacao apenas uma vez)
7. Teste e rollout:
   - testar no DEV com banco local (XAMPP)
   - deploy controlado na VPS (backup antes de migracao)
