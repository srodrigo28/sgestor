# Pasta `agente/` (memoria do projeto)

Esta pasta guarda notas persistentes do que foi feito e do que falta fazer.

Fluxo combinado:
- No inicio de cada nova sessao (ex: depois de reabrir o VSCode), o Codex le `agente/` para retomar o contexto.
- Ao final de cada etapa relevante, o Codex atualiza `agente/memoria.md` com:
  - estado atual
  - decisoes tomadas
  - proximos passos

Regra importante:
- Nao colocar segredos aqui (tokens/senhas). Se precisar, registrar apenas o nome da variavel (ex: `DATABASE_URL`), nao o valor.

