# Plano Funcionario

## Objetivo

Adicionar uma nova guia opcional no cadastro de funcionarios para dados trabalhistas basicos, deixando a estrutura pronta para admissao/fichamento sem travar o cadastro operacional.

A ideia e manter o cadastro rapido funcionando com os dados atuais e, quando necessario, preencher a guia de dados trabalhistas para carteira/CLT.

## Escopo Inicial

Criar uma terceira guia no formulario de funcionario:

- Principal
- Endereco e Contato
- Dados Trabalhistas

A guia `Dados Trabalhistas` nao deve ter campos obrigatorios nesta primeira etapa. O usuario pode salvar o funcionario mesmo sem preencher nenhum dado trabalhista.

## Campos Da Nova Guia

### Documentos

- CPF
- RG
- Orgao emissor do RG
- UF do RG
- Data de emissao do RG
- PIS/PASEP
- Numero da CTPS
- Serie da CTPS
- UF da CTPS

Observacao: com CTPS Digital, CPF costuma ser a principal referencia pratica, mas vamos manter campos de CTPS fisica para historico e compatibilidade.

### Dados Pessoais Complementares

- Nome da mae
- Nome do pai
- Estado civil
- Escolaridade
- Numero de dependentes

### Dados De Admissao

- Data de contratacao
- Cargo/Função
- Salario
- Tipo de contrato
- Jornada de trabalho
- Observacoes trabalhistas

## Regras Da Tela

- Todos os campos da guia trabalhista serao opcionais.
- CPF deve ter mascara visual.
- RG, PIS/PASEP e CTPS devem aceitar texto/numeros sem bloquear formatos antigos.
- Salario deve usar formato monetario.
- Numero de dependentes deve aceitar apenas inteiro maior ou igual a zero.
- A guia deve aparecer tanto em `Novo Funcionario` quanto em `Editar Funcionario`.
- O botao `Salvar Funcionario` deve continuar unico para todas as guias.

## Banco De Dados

Hoje existe a migration `22_add_clt_fields.sql`, mas ela ainda aponta para a tabela antiga `mechanics`. Como a refatoracao atual moveu o dominio para `employees`, precisamos criar uma migration nova ou ajustar o reconciliador para garantir esses campos em `employees`.

Campos sugeridos na tabela `employees`:

```sql
cpf VARCHAR(14)
rg VARCHAR(20)
rg_issuer VARCHAR(20)
rg_state VARCHAR(2)
rg_issue_date DATE
pis_pasep VARCHAR(20)
ctps_number VARCHAR(20)
ctps_series VARCHAR(10)
ctps_state VARCHAR(2)
mother_name VARCHAR(100)
father_name VARCHAR(100)
education_level VARCHAR(50)
marital_status VARCHAR(50)
salary DECIMAL(10, 2)
num_dependents INT DEFAULT 0
job_title VARCHAR(100)
contract_type VARCHAR(50)
work_schedule VARCHAR(100)
labor_notes TEXT
```

## Back-End

Atualizar `core/apps/employees/views.py` para:

- ler os novos campos do `request.form`;
- normalizar CPF, RG, PIS/PASEP e CTPS;
- gravar os dados no `INSERT INTO employees`;
- atualizar os dados no `UPDATE employees`;
- manter tudo opcional;
- evitar erro se as colunas ainda nao existirem, usando o helper de schema.

## Front-End

Atualizar:

- `core/templates/employees/create.html`
- `core/templates/employees/edit.html`

Adicionar a aba `Dados Trabalhistas` depois de `Endereco e Contato`, com layout em blocos:

- Documentos
- Dados Pessoais Complementares
- Admissao

## Prioridade De Implementacao

1. Criar/regularizar colunas em `employees`.
2. Adicionar campos no cadastro e edicao.
3. Atualizar `INSERT` e `UPDATE` do modulo de funcionarios.
4. Adicionar mascaras simples para CPF, PIS/PASEP e salario.
5. Validar salvamento com guia vazia e com guia preenchida.

## Fora Do Escopo Agora

- Geracao de contrato.
- Upload de documentos.
- Assinatura digital.
- Integracao eSocial.
- Validacao legal completa de admissao.
- Obrigatoriedade dos campos.

Esses pontos podem entrar em uma fase posterior, quando o cadastro basico de funcionario estiver estabilizado.
