# Plano de Ajustes de Datas em Orçamentos

## Objetivo

Permitir que o fluxo de orçamentos trabalhe corretamente com datas retroativas e datas operacionais reais, sem depender apenas de `NOW()`.

O foco principal e:

- cadastrar orcamentos com data retroativa
- aprovar ou reprovar com data real da decisao
- registrar retirada e entrega com data real
- registrar recebimento financeiro com data correta
- manter relatorios coerentes mesmo com lancamentos retroativos
- evitar quebrar estoque e historico atual

## Diagnostico atual

Hoje o fluxo usa `NOW()` em varios pontos criticos.

### O que acontece hoje

Em [core/apps/budgets/views.py](/c:/prod/sgestor/core/apps/budgets/views.py):

- `save_budget()` grava `created_at` com `NOW()`
- `save_budget()` define `approved_at`, `rejected_at`, `ready_for_pickup_at` e `delivered_at` com `datetime.now()` quando o status inicial ja nasce alterado
- `save_budget()` calcula `expiration_date` sempre a partir de `datetime.now() + 7 dias`
- quando cria cliente e veiculo automaticamente, tambem grava `created_at` com `NOW()`
- `approve_financial()` aprova com `approved_at = COALESCE(approved_at, NOW())`
- `approve_financial()` insere `financial_income.created_at` com `NOW()`, embora `entry_date` seja informado manualmente
- `update_budget()` e `quick_status()` gravam mudancas de etapa/decisao sempre com `datetime.now()` no momento da alteracao
- relatorios usam fortemente `budgets.created_at` como referencia temporal

### Efeito pratico do problema

Isso gera alguns atritos comuns:

- orcamento fechado hoje para representar uma venda da semana passada entra nas metricas de hoje
- aprovacao feita hoje para um orcamento aprovado na semana passada perde a data real da decisao
- retirada e entrega ficam com timestamp do clique e nao do evento real
- financeiro pode ficar com `entry_date` certo, mas o historico do orcamento e os graficos continuam desalinhados
- vencimento fica ligado ao momento de cadastro, nao a data do orcamento

## Principio da melhoria

Separar claramente os tipos de data.

### Datas que precisamos tratar

1. Data do orcamento
Significado: quando o orcamento foi emitido ou passou a existir no mundo real.

2. Data da decisao
Significado: quando foi aprovado ou reprovado.

3. Data de retirada
Significado: quando ficou pronto para retirada ou quando entrou nessa etapa.

4. Data de entrega
Significado: quando foi entregue de fato.

5. Data financeira
Significado: quando o recebimento entrou no caixa.

6. Data de vencimento
Significado: validade comercial do orcamento.

## Estrategia recomendada

## Fase 1: Corrigir a entrada de dados no cadastro

### 1.1 Adicionar campos de data em `budgets/create.html`

Arquivo alvo:
[core/templates/budgets/create.html](/c:/prod/sgestor/core/templates/budgets/create.html)

Adicionar no formulario:

- `budget_date`
  Sugestao: label `Data do Orçamento`
  Default: data atual

- `expiration_date`
  Sugestao: label `Validade`
  Default: `budget_date + 7 dias`, mas editavel

- `approval_date`
  Mostrar quando o usuario clicar em `Aprovar`
  Se vier vazio, usar a mesma data atual por conveniencia

- `rejection_date`
  Mostrar quando clicar em `Reprovar`

### 1.2 Comportamento esperado no cadastro

- Salvar aguardando:
  grava `created_at` baseado em `budget_date`
  grava `approval_status = sent`
  nao grava `approved_at` nem `rejected_at`

- Salvar aprovado:
  grava `created_at` baseado em `budget_date`
  grava `approved_at` com `approval_date`

- Salvar reprovado:
  grava `created_at` baseado em `budget_date`
  grava `rejected_at` com `rejection_date`

### 1.3 Regra de UX

- `expiration_date` deve ser recalculada automaticamente quando `budget_date` mudar, mas apenas se o usuario ainda nao tiver editado manualmente a validade
- mostrar texto de ajuda: `Use a data real em que o orçamento foi feito`

## Fase 2: Corrigir aprovacao e edicao posterior

### 2.1 Aprovar com data real

Arquivo alvo:
[core/templates/budgets/view.html](/c:/prod/sgestor/core/templates/budgets/view.html)

O modal de aprovacao ja possui `financialDate`, mas falta separar melhor os conceitos.

Hoje ele faz duas coisas juntas:

- aprova o orcamento
- gera/atualiza o financeiro

Plano:

- adicionar no modal:
  - `approvalDate`
  - `financialDate`

- regra:
  - `approvalDate` controla `budgets.approved_at`
  - `financialDate` controla `financial_income.entry_date`

Beneficio:

- aprovacao pode ter ocorrido em um dia
- recebimento pode ter entrado em outro

### 2.2 Editar datas apos o cadastro

Em [core/templates/budgets/view.html](/c:/prod/sgestor/core/templates/budgets/view.html), no modo editar, permitir alterar:

- data do orcamento
- validade
- data de aprovacao
- data de reprovacao
- data de retirada
- data de entrega

Com exibicao condicionada ao status atual.

Exemplo:

- se `approval_status = approved`, exibir `Data da Aprovação`
- se `approval_status = rejected`, exibir `Data da Reprovação`
- se `stage_status = ready_for_pickup`, exibir `Data de Retirada`
- se `stage_status = delivered`, exibir `Data de Entrega`

### 2.3 Ajustar backend de update

Em [core/apps/budgets/views.py](/c:/prod/sgestor/core/apps/budgets/views.py):

Hoje `update_budget()` usa `datetime.now()` quando o status muda.

Trocar para:

- usar data enviada pelo frontend quando existir
- usar `now()` apenas como fallback

## Fase 3: Ajustar o modelo de dados para refletir melhor o negocio

### 3.1 Melhoria minima sem grande ruptura

A estrutura atual ja ajuda porque a tabela `budgets` possui:

- `created_at`
- `approved_at`
- `rejected_at`
- `ready_for_pickup_at`
- `delivered_at`
- `expiration_date`

Entao, a melhoria minima pode aproveitar isso sem criar muitas colunas novas.

### 3.2 Melhoria recomendada

Adicionar uma coluna explicita para data do negocio:

- `budget_date DATE NULL`

Motivo:

- `created_at` mistura conceito tecnico e conceito de negocio
- `created_at` idealmente deveria representar insercao no banco
- `budget_date` representa a data real do orcamento

Se quisermos uma modelagem mais robusta:

- `budget_date DATE`
- `approved_at DATETIME`
- `rejected_at DATETIME`
- `ready_for_pickup_at DATETIME`
- `delivered_at DATETIME`
- `expiration_date DATE`

### 3.3 Recomendacao de direcao

Preferencia:

1. manter `created_at` como timestamp tecnico
2. criar `budget_date`
3. migrar telas e relatorios para usar `budget_date` quando o objetivo for analise comercial

Isso evita gambiarra futura.

## Fase 4: Ajustar relatorios e filtros

## Problema atual

Listas e graficos usam muito `created_at`.

Exemplos em [core/apps/budgets/views.py](/c:/prod/sgestor/core/apps/budgets/views.py):

- listagem ordena por `b.created_at DESC`
- estatisticas mensais usam `created_at`
- graficos usam `created_at`
- filtros de distribuicao usam `created_at`

## Melhor abordagem

### 4.1 Para indicadores comerciais

Usar `budget_date`.

Casos:

- total de orcamentos por mes
- volume por periodo
- historico de propostas
- dashboards de performance comercial

### 4.2 Para indicadores operacionais de aprovacao

Usar `approved_at` e `rejected_at`.

Casos:

- aprovados por periodo
- reprovados por periodo
- tempo medio entre orcamento e aprovacao

### 4.3 Para operacao da oficina/logistica

Usar:

- `ready_for_pickup_at`
- `delivered_at`

### 4.4 Para financeiro

Manter:

- `financial_income.entry_date`

## Fase 5: Ajustar regras de negocio

### 5.1 Validacoes importantes

- `approval_date` nao deve ser menor que `budget_date` sem confirmacao explicita
- `rejection_date` nao deve ser menor que `budget_date`
- `ready_for_pickup_at` nao deve ser menor que `budget_date`
- `delivered_at` nao deve ser menor que `ready_for_pickup_at` quando esta existir
- `expiration_date` nao deve ser menor que `budget_date`
- `financialDate` pode ser diferente de `approvalDate`, mas o sistema deve deixar isso claro

### 5.2 Comportamentos inteligentes

- ao aprovar, sugerir `approvalDate = hoje`
- se `budget_date` for retroativa, sugerir `approvalDate = budget_date`
- ao salvar aprovado no cadastro, permitir marcar `approvalDate` sem obrigar o financeiro no mesmo momento, se isso fizer sentido no fluxo

### 5.3 Estoque

Hoje o estoque e ajustado ao aprovar.

Importante:

- manter a regra de ajuste vinculada a mudanca de status, nao a data informada
- a data retroativa nao deve tentar "voltar no tempo" no estoque
- o plano deve deixar claro que retroatividade afeta historico e relatorio, nao reconstrucao temporal de estoque

## Fase 6: Migracao de dados existentes

### 6.1 Se criarmos `budget_date`

Migracao sugerida:

- adicionar coluna `budget_date DATE NULL`
- preencher `budget_date = DATE(created_at)` para registros antigos
- depois tornar `budget_date` obrigatoria em novas gravacoes

### 6.2 Backfill das datas de status

Os scripts atuais em [core/db/sql/09_budgets_split_status.sql](/c:/prod/sgestor/core/db/sql/09_budgets_split_status.sql) ja fazem aproximacao com `updated_at`.

Manter essa logica como historico legado, mas para novos registros usar datas explicitamente informadas.

## Fase 7: Ordem recomendada de implementacao

### Sprint 1

Banco e backend:

- adicionar `budget_date` via migration
- ajustar `save_budget()` para receber datas do frontend
- ajustar `update_budget()` para editar datas
- ajustar `approve_financial()` para receber `approval_date`

### Sprint 2

Frontend de cadastro:

- incluir `Data do Orçamento`
- incluir `Validade`
- incluir `Data da Aprovação` e `Data da Reprovação` conforme acao
- enviar essas datas no payload

### Sprint 3

Frontend de visualizacao/edicao:

- exibir datas atuais do registro
- permitir editar datas de status
- separar `Data da Aprovação` de `Data do Recebimento`

### Sprint 4

Relatorios:

- migrar listagens e graficos principais para `budget_date`
- criar filtros por data de aprovacao quando relevante
- revisar cards e indicadores para nao depender so de `created_at`

## Campos sugeridos no payload

### Cadastro de orçamento

```json
{
  "client_name": "...",
  "vehicle_plate": "...",
  "notes": "...",
  "discount": 0,
  "approval_status": "approved",
  "stage_status": "budget",
  "budget_date": "2026-04-01",
  "expiration_date": "2026-04-08",
  "approval_date": "2026-04-03T14:30",
  "rejection_date": null,
  "items": []
}
```

### Aprovação financeira

```json
{
  "description": "Orçamento #123 - Cliente X",
  "amount": 1500,
  "payment_type": "pix",
  "approval_date": "2026-04-03T14:30",
  "entry_date": "2026-04-05"
}
```

## Ajustes pontuais no codigo atual

### Em `save_budget()`

Trocar:

- `created_at = NOW()`
- `approved_at = datetime.now()`
- `rejected_at = datetime.now()`
- `expiration = datetime.now() + 7 dias`

Por:

- `created_at` derivado de `budget_date` ou `NOW()` como fallback
- `approved_at` derivado de `approval_date`
- `rejected_at` derivado de `rejection_date`
- `expiration_date` vindo do frontend ou calculado a partir de `budget_date`

### Em `update_budget()`

Adicionar leitura de:

- `budget_date`
- `expiration_date`
- `approved_at`
- `rejected_at`
- `ready_for_pickup_at`
- `delivered_at`

### Em `approve_financial()`

Separar claramente:

- aprovacao do orcamento
- data do recebimento financeiro

## Riscos e cuidados

- usar `created_at` como data de negocio vai continuar causando distorcao se nao criarmos `budget_date`
- retroagir datas sem revisar relatorios vai gerar inconsistencias visuais
- mudar datas de status sem proteger ordem cronologica pode produzir fluxos impossiveis
- estoque nao deve ser recalculado historicamente so porque a data foi retroagida
- o financeiro pode ficar coerente enquanto o dashboard continua errado, se a migracao for parcial

## Resultado esperado

Ao final, o sistema deve permitir:

- cadastrar um orcamento hoje com data de uma semana atras
- aprovar hoje um orcamento dizendo que ele foi aprovado ontem ou antes
- registrar recebimento em data diferente da aprovacao
- filtrar e medir desempenho comercial pela data real do orcamento
- manter historico operacional mais fiel ao que aconteceu

## Recomendacao final

A melhor estrategia nao e apenas mudar campos na tela.

A recomendacao mais segura e:

1. criar `budget_date`
2. adaptar cadastro e aprovacao para datas explicitas
3. ajustar relatorios para parar de depender apenas de `created_at`
4. manter `created_at` como trilha tecnica do sistema

## Próximo passo

Comecar pela migration do banco e pelo backend de [core/apps/budgets/views.py](/c:/prod/sgestor/core/apps/budgets/views.py), porque sem isso a interface vai continuar limitada pelo `NOW()`.
