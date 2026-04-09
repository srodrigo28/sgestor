# Plano de Responsividade Mobile

## Objetivo

Melhorar a responsividade geral do sistema com foco em usabilidade real no celular, priorizando:

- navegacao mobile com `menu-drawer`
- header/topbar adaptado para telas pequenas
- paginas com tabelas densas
- formularios longos e modais
- telas com calendario e graficos
- padronizacao visual e tecnica para futuras telas

## Diagnostico rapido do projeto

Pontos observados no estado atual:

- O layout base em [core/templates/base.html](/c:/prod/sgestor/core/templates/base.html) ja possui `mobileDrawer`, `mobileOverlay` e botao hamburguer.
- O menu desktop e o menu mobile estao duplicados no mesmo arquivo, o que aumenta custo de manutencao.
- Existem paginas com boa base de grid responsivo, mas sem um padrao unico entre listas, formularios, cards e modais.
- Algumas telas usam `overflow-x-auto` como contencao, mas ainda nao existe estrategia mobile consistente para tabelas.
- Formularios longos como [core/templates/budgets/create.html](/c:/prod/sgestor/core/templates/budgets/create.html) ainda concentram muita densidade horizontal.
- Listagens como [core/templates/clients/index.html](/c:/prod/sgestor/core/templates/clients/index.html) dependem de tabela tradicional, o que no celular tende a piorar leitura e acoes.
- A agenda em [core/templates/schedule/index.html](/c:/prod/sgestor/core/templates/schedule/index.html) usa `FullCalendar`, que precisa de tratamento especifico para mobile.

## Estrategia

Vamos atacar em 3 camadas:

1. infraestrutura responsiva global no layout base
2. componentes reutilizaveis mobile-first
3. refino tela a tela por prioridade

## Fase 1: Base responsiva global

### 1.1 Consolidar navegacao mobile

Objetivo:
deixar o `menu-drawer` estavel, acessivel e facil de manter.

Acoes:

- extrair os links do menu para um partial reutilizavel, evitando duplicacao entre sidebar desktop e drawer mobile
- padronizar estados de abertura/fechamento do drawer
- fechar drawer ao navegar, ao clicar no overlay e ao pressionar `Esc`
- travar scroll do `body` apenas quando o drawer estiver aberto
- adicionar foco inicial no drawer ao abrir
- devolver foco ao botao hamburguer ao fechar
- revisar largura do drawer para algo como `w-[280px] max-w-[85vw]`
- garantir area de toque confortavel nos itens do menu

Criterio de aceite:

- o menu mobile funciona bem entre `320px` e `767px`
- nao ha duplicacao de markup do menu
- a navegacao continua funcional para admin e perfis com permissoes diferentes

### 1.2 Revisar header mobile

Objetivo:
melhorar topo das paginas no celular.

Acoes:

- padronizar um header mobile simples com botao menu, titulo truncado e acoes opcionais
- reduzir ruido visual em telas pequenas
- revisar espacamentos `p-4`, `gap-3`, `text-sm` e altura dos botoes
- decidir quais acoes ficam visiveis no mobile e quais vao para drawer ou menu secundario

Criterio de aceite:

- o topo nao quebra em telas pequenas
- titulos longos continuam legiveis
- acoes importantes permanecem acessiveis

### 1.3 Criar utilitarios/padroes mobile-first

Objetivo:
parar de resolver responsividade isoladamente em cada template.

Acoes:

- definir padroes para container interno
- definir padrao para grids: `grid-cols-1`, `sm:*`, `md:*`
- criar padrao para barras de acao: busca, filtros e botao novo
- criar padrao para cards, tabelas, modais e blocos de resumo
- revisar classes repetidas de input, botao e card

Entregavel:

- partials ou convencoes reutilizaveis no Jinja/Tailwind

## Fase 2: Componentes criticos para mobile

### 2.1 Tabelas responsivas

Problema:
tabela com scroll horizontal resolve parcialmente, mas nao entrega boa leitura no celular.

Plano:

- manter tabela tradicional no desktop
- no mobile, avaliar transformacao para cards por linha
- mostrar so informacoes essenciais por item
- mover acoes para botao de contexto, linha expandivel ou rodape do card
- usar badges compactas para status, setor e metadados

Prioridade alta:

- [core/templates/clients/index.html](/c:/prod/sgestor/core/templates/clients/index.html)
- listagens de produtos, servicos, financeiro, tarefas e orcamentos

Criterio de aceite:

- usuario consegue visualizar item, status e acao principal sem arrastar horizontalmente

### 2.2 Formularios e modais

Problema:
alguns formularios sao longos, densos e com muitas colunas.

Plano:

- quebrar formularios em blocos verticais no mobile
- reduzir colunas para `grid-cols-1` em larguras menores
- revisar inputs em linha com botao lateral
- melhorar espacamento entre campos
- transformar tabs estreitas em navegacao mais clara no celular
- limitar altura de modais e garantir `overflow-y-auto`
- quando necessario, trocar modal por painel full-screen no mobile

Prioridade alta:

- [core/templates/budgets/create.html](/c:/prod/sgestor/core/templates/budgets/create.html)
- modais de cliente
- modais de agendamento
- formularios de cadastro/edicao em geral

Criterio de aceite:

- formulario pode ser preenchido com uma mao sem zoom do navegador
- nenhum campo fica espremido ou cortado

### 2.3 Blocos de filtros e acoes

Problema:
busca, filtros, toggle de visualizacao e botao de adicionar as vezes ficam apertados.

Plano:

- empilhar controles no mobile
- deixar busca em largura total
- agrupar filtros em linha com scroll so quando realmente necessario
- usar botao principal em largura natural ou total, conforme contexto
- revisar icones sem texto quando o significado nao estiver claro

Criterio de aceite:

- barra de acoes cabe sem quebrar experiencia em `360px`

### 2.4 Cards, metricas e graficos

Plano:

- revisar grids de dashboard para leitura vertical
- reduzir alturas fixas quando prejudicarem telas pequenas
- garantir que graficos tenham `maintainAspectRatio: false` quando necessario
- simplificar legendas e labels no mobile
- priorizar informacao principal antes de detalhes

Criterio de aceite:

- dashboard continua legivel e util no celular sem sensacao de miniatura

### 2.5 Calendario mobile

Problema:
`FullCalendar` costuma ficar apertado no modo mes em telas pequenas.

Plano:

- trocar visualizacao padrao no mobile para `listWeek` ou `timeGridDay`
- adaptar `headerToolbar` para menos controles por linha
- revisar altura e toque dos eventos
- manter acesso rapido para criar agendamento em um dia especifico
- usar modal/lista do dia como experiencia principal em mobile

Prioridade alta:

- [core/templates/schedule/index.html](/c:/prod/sgestor/core/templates/schedule/index.html)

Criterio de aceite:

- agendamentos podem ser consultados e criados sem apertar alvos minusculos

## Fase 3: Refatoracao por ordem de impacto

### Sprint 1

- refatorar `base.html`
- extrair partial do menu
- estabilizar `menu-drawer`
- padronizar header mobile
- criar convencoes de container, spacing e action bars

### Sprint 2

- adaptar dashboard
- adaptar clientes
- adaptar agenda

### Sprint 3

- adaptar orcamento
- adaptar produtos
- adaptar servicos
- adaptar financeiro

### Sprint 4

- revisar admin
- revisar mecanicos
- revisar tarefas
- fechar inconsistencias visuais

## Checklist tecnico

- validar `320px`, `360px`, `390px`, `430px`, `768px`
- revisar `overflow-x` desnecessario
- revisar `min-width` que forca quebra ruim
- revisar modais com altura maior que viewport
- revisar botoes com area de toque minima
- revisar textos truncados e icones sem contexto
- revisar contraste e legibilidade
- revisar uso de `sticky` no topo mobile
- revisar comportamento ao rotacionar tela

## Padronizacao sugerida

### Navegacao

- desktop: sidebar fixa
- mobile: drawer com overlay
- acoes secundarias: menu contextual ou bloco abaixo do titulo

### Listagens

- desktop: tabela
- mobile: card list ou tabela simplificada com detalhes expansiveis

### Formularios

- desktop: 2 a 4 colunas quando fizer sentido
- mobile: 1 coluna por padrao

### Modais

- desktop: centralizados
- mobile: quase full-screen com rolagem interna

## Riscos e cuidados

- duplicacao atual do menu pode gerar regressao se mexermos sem extrair partial antes
- algumas paginas misturam logica JS e markup no mesmo template, entao a responsividade pode exigir refino visual e funcional ao mesmo tempo
- calendario e tabelas sao os pontos com maior chance de retrabalho
- mudancas visuais no mobile podem afetar desktop se a refatoracao nao seguir abordagem mobile-first com breakpoints claros

## Ordem recomendada de execucao

1. `base.html` e navegacao compartilhada
2. padroes de action bar, cards e modais
3. clientes
4. agenda
5. orcamento
6. demais modulos
7. rodada final de QA mobile

## Resultado esperado

Ao final, o sistema deve:

- abrir e navegar bem no celular
- permitir cadastro e edicao sem friccao
- exibir listas sem depender de arraste horizontal o tempo todo
- manter consistencia visual entre modulos
- ter uma base tecnica mais limpa para evolucoes futuras

## Proximo passo

Comecar pela refatoracao de [core/templates/base.html](/c:/prod/sgestor/core/templates/base.html), extraindo o menu compartilhado e fechando a infraestrutura do `menu-drawer`.
