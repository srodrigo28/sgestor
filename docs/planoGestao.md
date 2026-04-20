# Plano de Gestão e Evolução Multi-Segmento ...

Este documento detalha o plano técnico para transformar o sistema atual em uma **Plataforma Multi-Segmento** (SaaS), capaz de atender nichos distintos (Oficina, Loja, Uso Pessoal) com experiências personalizadas.

## 1. Visão Geral do Problema
Atualmente, o sistema possui um controle de permissões básico via tabela `role_menu_permissions`. No entanto, os módulos (Orçamentos, Produtos, Clientes) são genéricos.
*   **Problema:** Uma Loja vê campos de Oficina (ex: Placa, Modelo do Carro) ou vice-versa, causando poluição visual e complexidade desnecessária.
*   **Objetivo:** O sistema deve se comportar como um software nativo de Oficina para oficinas, e de Vendas para lojas.

## 2. Estratégia de Segmentação

### A. Definição dos Segmentos (Roles)
Vamos formalizar os "Seguimentos" como a entidade principal de configuração do usuário.

1.  **Pessoal (pessoal):** Foco em Tarefas e Finanças simples.
2.  **Loja (loja):** Foco em Produtos, Vendas, Estoque e Clientes.
3.  **Oficina (oficina):** Foco em Ordem de Serviço, Veículos/Equipamentos, Placas, Serviços e Mão de obra.
4.  **Admin (admin):** Superusuário com acesso irrestrito e configurações globais.

### B. Fluxo de Cadastro (Onboarding)
O campo "Seguimento" deve ser obrigatório no registro (`/register`).
*   **Tela de Registro:** Adicionar um `select` (dropdown) para escolher o tipo de conta: "Para mim (Pessoal)", "Para minha Loja", "Para minha Oficina".
*   **Inicialização:** Ao criar a conta, o sistema automaticamente aplica o "Template de Permissões" daquele segmento.

## 3. Arquitetura de Módulos Dinâmicos

Para evitar criar tabelas gigantes com colunas nulas, usaremos estratégias de **Extensão de Dados**.

### Mudanças no Banco de Dados
1.  **Tabela `users`:** Confirmar o uso da coluna `role` como o definidor do segmento.
2.  **Tabela `clients`:** Adicionar suporte a campos flexíveis (JSON) ou tabelas auxiliares.
    *   *Sugestão:* Criar `client_vehicles` (id_client, placa, modelo) vinculado apenas se o usuário for Oficina.
3.  **Tabela `budgets` (Orçamentos):**
    *   **Loja:** Vê "Venda", lista de "Produtos".
    *   **Oficina:** Vê "Ordem de Serviço", lista de "Peças" + "Mão de Obra" + "Dados do Veículo".

## 4. Controle de Visibilidade (Filtros)

O filtro deve ocorrer em duas camadas:

### Camada 1: Menu (Navegação)
O menu lateral (`sidebar`) só deve renderizar o que o segmento permite.
*   **Oficina:** Dashboard, Agenda, Orçamentos (OS), Clientes, Estoque (Peças), Financeiro.
*   **Loja:** Dashboard, Vendas (PDV), Produtos, Clientes, Financeiro.
*   **Pessoal:** Dashboard, Tarefas, Financeiro.

*Ação Técnica:* Melhorar a query em `main.py` (`inject_menu_permissions`) para ler configurações padrão baseadas no `role` se não houver personalização específica no banco.

### Camada 2: Campos de Formulários (Views)
Dentro dos templates Jinja2 (HTML), usaremos condicionais baseadas no `session['role']`.

**Exemplo Prático (Cadastro de Orçamento):**
```html
<!-- Campo visível apenas para Oficina -->
{% if session['role'] == 'oficina' %}
    <div class="form-group">
        <label>Placa do Veículo / Equipamento</label>
        <input type="text" name="vehicle_plate">
    </div>
{% endif %}

<!-- Campo visível apenas para Loja -->
{% if session['role'] == 'loja' %}
    <div class="form-group">
        <label>Canal de Venda (Instagram, WhatsApp, Site)</label>
        <input type="text" name="sales_channel">
    </div>
{% endif %}
```

## 5. Roteiro de Implementação (Passo a Passo)

### Fase 1: Correção do Fluxo de Entrada
1.  [ ] Alterar `login.html` e `register` em `auth.py` para salvar o `role` correto na criação.
2.  [ ] Garantir que `main.py` carregue as permissões corretas logo após o login.

### Fase 2: Refatoração dos Produtos/Serviços
1.  [ ] Renomear visualmente "Produtos" para "Estoque/Peças" quando for Oficina no menu.
2.  [ ] Criar distinção entre "Produtos" (físico) e "Serviços" (mão de obra).
    *   *Oficinas* usam muito a combinação dos dois em um único orçamento.
    *   *Lojas* usam majoritariamente Produtos.

### Fase 3: Orçamentos Inteligentes
1.  [ ] Criar uma tabela auxiliar `budget_details` ou adicionar colunas específicas na tabela `budgets` (`vehicle_info`, `delivery_status`).
2.  [ ] Adaptar a tela de "Novo Orçamento" para esconder/mostrar campos via JavaScript baseado no perfil logado.

## 6. Próximos Passos Imediatos
Sugerir ao desenvolvedor começar pela **Fase 1**, ajustando o formulário de cadastro para que novos usuários já entrem com o perfil de menu correto.
