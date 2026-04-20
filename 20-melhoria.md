# Plano de 20 Melhorias

## Objetivo

Organizar a evolução do projeto em duas frentes:

1. Primeiro: cadastro de clientes e fluxo de OS/orçamento.
2. Depois: dashboard com cards e filtro por período (`Dia`, `Semana`, `Mês`).

Este plano foi montado com base no código atual em `core/apps/clients/views.py`, `core/apps/budgets/views.py`, `core/apps/tasks/views.py`, `core/templates/clients/index.html`, `core/templates/budgets/create.html` e `core/templates/dashboard.html`.

---

## Diagnóstico Atual

### O que já existe

- O módulo de clientes já possui listagem, busca, filtro por setor, cadastro, edição e exclusão.
- O módulo de orçamento/OS já possui criação, edição, aprovação, rejeição, etapas de retirada/entrega e vínculo com cliente, veículo, itens, mecânico e financeiro.
- O dashboard já possui os 4 cards pedidos:
  - Número de Orçamentos
  - Número de Aguardando
  - Número de Aprovados
  - Número de Clientes
- O dashboard já possui o filtro visual `Dia`, `Semana` e `Mês`, e o back-end já prepara `stats_by_period` e `chart_data_by_period`.

### Principais pontos frágeis encontrados

- O fluxo de orçamento ainda cria cliente automaticamente só com o nome quando não encontra correspondência, o que favorece duplicidade e cadastro incompleto.
- A seleção de cliente no orçamento depende de texto livre no formato `Nome | CPF`, o que é frágil quando há nomes repetidos.
- A tela de orçamento possui trechos JS que referenciam elementos que não aparecem no HTML atual, como `itemTypeInput`, `itemTakeawayInput`, `stockIndicator` e `stockValue`.
- A busca de placa está simulada por mock na interface, então o fluxo parece pronto visualmente, mas não está concluído funcionalmente.
- O cadastro de cliente ainda tem pouca validação de CPF/CNPJ, duplicidade, normalização e consistência antes de gravar no banco.
- O dashboard já troca os dados pelos períodos, mas precisa passar por revisão de consistência semântica para garantir que todos os cards respeitem exatamente o mesmo recorte esperado pelo usuário.
- Há textos com problema de encoding em algumas telas, principalmente em dashboard e orçamento.

---

## Prioridade de Execução

### Fase 1

Foco total em:

- cadastro de cliente
- fluxo de OS/orçamento
- consistência dos status
- integridade dos dados entre cliente, orçamento, veículo e financeiro

### Fase 2

Foco em:

- dashboard
- confiabilidade dos cards
- resposta do filtro `Dia`, `Semana`, `Mês`
- refinamento visual e semântico

---

## As 20 Melhorias

## Bloco A: Cadastro de Cliente

### 1. Validar CPF/CNPJ no back-end

Adicionar validação real no servidor para impedir documento inválido ou mal formatado. Hoje o front mascara, mas o back-end praticamente aceita qualquer valor.

### 2. Bloquear duplicidade de cliente por documento

Antes de inserir ou editar, verificar se já existe cliente com o mesmo CPF/CNPJ para o mesmo usuário. Isso evita base duplicada e conflito no orçamento.

### 3. Padronizar normalização de dados do cliente

Centralizar limpeza de nome, telefones, CPF/CNPJ, CEP, cidade e UF para garantir consistência entre cadastro manual, edição e criação indireta via orçamento.

### 4. Melhorar mensagens de validação no cadastro

Exibir erros objetivos por campo obrigatório ou inválido, em vez de mensagens genéricas de exceção.

### 5. Impedir exclusão de cliente com vínculo operacional sem tratamento

Se o cliente tiver orçamento, veículo, OS ou agendamento vinculado, tratar isso com aviso claro e política definida, em vez de depender apenas do banco retornar erro.

### 6. Adicionar busca por telefone e nome fantasia

Hoje a busca está concentrada em nome, CPF e alguns campos opcionais. Vale ampliar para telefone principal e nome fantasia para uso comercial diário.

### 7. Criar indicador de qualidade do cadastro

Mostrar se o cliente está com cadastro completo, parcial ou crítico, com base em documento, contato e endereço. Isso ajuda muito antes de gerar orçamento/OS.

---

## Bloco B: Fluxo de OS / Orçamento

### 8. Trocar seleção textual de cliente por ID real

O orçamento deve gravar e enviar `client_id` de forma confiável. O nome pode continuar visível, mas a operação não deve depender de string digitada no campo.

### 9. Parar de criar cliente automático apenas pelo nome

Se o cliente não existir, o sistema deve oferecer:

- selecionar um já existente
- cadastrar um novo cliente corretamente

Evitar `INSERT INTO clients (user_id, name, created_at)` sem dados mínimos.

### 10. Definir claramente o que é Orçamento e o que é OS

Hoje o fluxo está concentrado em `budgets`, mas funcionalmente já mistura orçamento, aprovação, retirada e entrega. Precisamos formalizar a regra:

- orçamento enviado
- aguardando decisão
- aprovado/reprovado
- pronto para retirada
- entregue

### 11. Revisar transições de status e timestamps

Padronizar quando preencher:

- `approved_at`
- `rejected_at`
- `ready_for_pickup_at`
- `delivered_at`

Assim relatórios e dashboard não ficam inconsistentes.

### 12. Corrigir os elementos JS faltantes na tela de orçamento

Resolver a diferença entre HTML e JavaScript na criação de itens, principalmente nos controles de tipo do item e indicador de estoque.

### 13. Melhorar o cadastro de veículo no fluxo da OS

Garantir regra clara para placa, marca, modelo, ano e KM, inclusive quando a placa não existe ou quando o orçamento é retroativo.

### 14. Substituir mock de placa por integração real ou fluxo manual honesto

Hoje o botão parece funcional, mas está simulando retorno. Melhor decidir entre:

- integração real
- remoção do mock
- fallback manual explícito

### 15. Validar estoque antes de aprovar itens de produto

Hoje o sistema ajusta estoque ao aprovar, mas o ideal é validar saldo antes da aprovação e sinalizar item com estoque insuficiente.

### 16. Criar número/identificador operacional mais claro para OS

Melhorar a leitura operacional na listagem e impressão com um identificador amigável para atendimento e acompanhamento interno.

---

## Bloco C: Dashboard e Cards

### 17. Revisar a regra exata do filtro `Dia`, `Semana`, `Mês`

Definir semanticamente:

- `Dia`: hoje
- `Semana`: semana corrente ou últimos 7 dias
- `Mês`: mês corrente ou últimos 30 dias

Hoje essa decisão precisa ser fechada de forma explícita para evitar divergência entre expectativa e cálculo.

### 18. Garantir que os 4 cards mudem juntos pelo mesmo período

Os cards já têm estrutura pronta, mas a prioridade é garantir coerência total entre:

- Orçamentos
- Aguardando
- Aprovados
- Clientes

Sem misturar `created_at` com `approved_at` de forma confusa para o usuário final.

### 19. Criar endpoint dedicado para métricas do dashboard

Separar a lógica de métricas em uma camada ou endpoint próprio facilita manutenção, testes e futura expansão dos cards.

### 20. Corrigir encoding e polir a leitura visual dos cards

Há textos com caracteres quebrados em algumas telas. Corrigir encoding e revisar rótulos para deixar os cards mais profissionais e fáceis de entender.

---

## Ordem Recomendada de Implementação

1. Cliente por ID no orçamento e bloqueio de criação automática incompleta.
2. Validação de CPF/CNPJ, duplicidade e consistência de cadastro.
3. Revisão completa dos status de orçamento/OS e regras de transição.
4. Correção dos bugs da tela de criação de orçamento.
5. Ajuste do dashboard para refletir exatamente o filtro `Dia`, `Semana`, `Mês`.
6. Refino visual, textos e testes.

---

## Entregável da Próxima Etapa

Na próxima etapa, recomendo implementarmos primeiro este pacote:

- cliente por `id` no fluxo de orçamento
- bloqueio de cliente duplicado por documento
- criação de cliente completo sem cadastro automático incompleto
- revisão dos status da OS/orçamento
- correção dos elementos quebrados na tela de orçamento

Depois disso, partimos para o dashboard e fechamos a lógica dos 4 cards com o filtro superior.
