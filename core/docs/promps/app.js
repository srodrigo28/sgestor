const modules = [
  {
    id: "intro",
    title: "1) Por que Docker é tão hypado?",
    subtitle: "O problema real que ele resolve e por que virou padrão no dia a dia.",
    blocks: [
      p(`
Docker virou “hype” porque ele resolve um problema que todo time sente:
o clássico “funciona na minha máquina”. Ele cria um ambiente isolado e reprodutível,
onde seu app roda do mesmo jeito para qualquer pessoa e em qualquer máquina.
      `),
      ul([
        "Padroniza versões (Node/Python/PHP) sem instalar tudo no PC",
        "Reduz onboarding (clone + 1 comando e pronto)",
        "Evita conflito de dependências entre projetos",
        "Ajuda no CI/CD: o mesmo container que você testa é o que vai para produção"
      ]),
      note(`
Docker não é só “rodar em container”: é criar uma unidade de execução (imagem)
que embala app + dependências + configuração mínima.
      `),
    ],
  },

  {
    id: "ports",
    title: "2) Portas: o que são e por que sempre dá ruim",
    subtitle: "Entenda host vs container e como mapear certo.",
    blocks: [
      p(`
Porta é o “endereço de entrada” para um serviço (HTTP, banco, etc.).
No Docker você tem dois mundos:
      `),
      ul([
        "Host: seu computador (onde você abre o navegador)",
        "Container: a aplicação isolada (onde o servidor realmente roda)"
      ]),
      p(`
O mapeamento de portas é: HOST:CONTAINER.
Exemplo: "3000:3000" significa:
- Seu PC recebe em 3000
- O container entrega para a app na porta 3000
      `),
      code("Exemplo no docker-compose.yml (porta 8080 no host -> 80 no container):", `ports:
  - "8080:80"`),
      warn(`
Se der erro “port is already allocated”, é porque alguma coisa já está usando a porta no HOST.
Troque a porta do lado esquerdo (HOST).
      `),
    ],
  },

  {
    id: "versions",
    title: "3) Versões: por que usar tag (e não latest)",
    subtitle: "Controle de versão nas imagens evita surpresas.",
    blocks: [
      p(`
Imagem Docker normalmente tem “tags” de versão.
Exemplos: node:20, python:3.12, php:8.2-apache
      `),
      ul([
        "Usar latest é arriscado: amanhã pode quebrar",
        "Tags fixas dão previsibilidade",
        "Times precisam da mesma versão para não dar diferença de comportamento"
      ]),
      code("Exemplo de base image com versão:", `FROM python:3.12-slim`),
      note(`
Boa prática: pinning de versão + atualizar de forma consciente (ex.: todo mês).
      `),
    ],
  },

  {
    id: "images",
    title: "4) Tipos de imagens e escolhas (slim, alpine, distroless)",
    subtitle: "Como escolher a base e por quê isso muda performance e segurança.",
    blocks: [
      p(`
Você vai ver variações como:
      `),
      ul([
        "Imagem “full”: maior, mais ferramentas, mais pesada",
        "slim: menor, suficiente para a maioria dos apps",
        "alpine: bem pequena, mas pode dar dor com bibliotecas nativas",
        "distroless: mínima (quase sem shell), mais segura, boa para produção"
      ]),
      p(`
Regra prática:
- Dev: pode ser slim (equilíbrio)
- Prod: multi-stage + base menor (slim/distroless)
      `),
      code("Exemplos:", `node:20
node:20-slim
python:3.12-slim
php:8.2-apache`),
      warn(`
Alpine é ótima para tamanho, mas algumas dependências nativas ficam mais chatas.
Se você quer menos dor, slim costuma ser a melhor.
      `),
    ],
  },

  {
    id: "howto",
    title: "5) Como rodar (comandos essenciais)",
    subtitle: "O mínimo que você precisa para trabalhar no dia a dia.",
    blocks: [
      ul([
        "docker build -t meu-app .  (constrói imagem a partir do Dockerfile)",
        "docker run -p 3000:3000 meu-app  (roda container e mapeia porta)",
        "docker compose up -d  (sobe serviços do compose)",
        "docker compose down  (derruba)",
        "docker compose logs -f  (ver logs)",
        "docker exec -it <container> sh  (entrar no container)"
      ]),
      note(`
Hoje o comando recomendado é "docker compose ..." (com espaço).
O antigo era "docker-compose" (com hífen) em muitas máquinas.
      `),
    ],
  },

  // PHP
  {
    id: "php",
    title: "6) Projeto PHP com Docker (simples e didático)",
    subtitle: "Exemplo com Apache: você entende portas, volumes e imagens.",
    blocks: [
      p(`Estrutura sugerida:`),
      code("", `php-app/
  Dockerfile
  docker-compose.yml
  src/
    index.php`),

      p(`src/index.php:`),
      code("", `<?php
echo "PHP rodando no Docker!\\n";
?>`),

      p(`Dockerfile (PHP + Apache):`),
      code("", `FROM php:8.2-apache

# Copia seus arquivos PHP para o diretório do Apache
COPY ./src/ /var/www/html/

# Apache já expõe 80 dentro do container (default)
EXPOSE 80`),

      p(`docker-compose.yml:`),
      code("", `services:
  web:
    build: .
    ports:
      - "8080:80"
    volumes:
      - ./src:/var/www/html`),

      p(`Como rodar:`),
      ul([
        "Na pasta php-app: docker compose up -d --build",
        "Abra: http://localhost:8080",
        "Para ver logs: docker compose logs -f web"
      ]),
      note(`
Aqui o volume faz o “hot reload”: você edita src/ e o Apache já serve a alteração.
      `),
    ],
  },

  // React
  {
    id: "react",
    title: "7) Projeto React com Docker (dev server)",
    subtitle: "Rodar React no container com porta 5173/3000 e volume para edição.",
    blocks: [
      p(`Estrutura sugerida (ex.: Vite):`),
      code("", `react-app/
  Dockerfile
  docker-compose.yml
  package.json
  ...`),

      p(`Dockerfile (modo DEV):`),
      code("", `FROM node:20-slim
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Ex.: Vite usa 5173
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]`),

      p(`docker-compose.yml:`),
      code("", `services:
  web:
    build: .
    ports:
      - "5173:5173"
    volumes:
      - ./:/app
    environment:
      - CHOKIDAR_USEPOLLING=true`),

      p(`Como rodar:`),
      ul([
        "docker compose up -d --build",
        "Abra: http://localhost:5173",
        "Se não atualizar, o polling ajuda (especialmente no Windows/macOS dependendo do FS)."
      ]),
      warn(`
Em dev, volumes são ótimos. Em prod, o ideal é buildar estático e servir com nginx (multi-stage).
      `),
    ],
  },

  // Python
  {
    id: "python",
    title: "8) Projeto Python com Docker (FastAPI ou Flask)",
    subtitle: "Exemplo com FastAPI + uvicorn e mapeamento de porta 8000.",
    blocks: [
      p(`Estrutura sugerida:`),
      code("", `py-app/
  Dockerfile
  docker-compose.yml
  requirements.txt
  main.py`),

      p(`main.py (FastAPI):`),
      code("", `from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"ok": True, "message": "Python rodando no Docker!"}`),

      p(`requirements.txt:`),
      code("", `fastapi
uvicorn[standard]`),

      p(`Dockerfile:`),
      code("", `FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`),

      p(`docker-compose.yml:`),
      code("", `services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./:/app`),

      p(`Como rodar:`),
      ul([
        "docker compose up -d --build",
        "Abra: http://localhost:8000",
        "Docs: http://localhost:8000/docs"
      ]),
    ],
  },

  {
    id: "compose-vs-dockerfile",
    title: "9) Dockerfile vs docker-compose.yml (na prática)",
    subtitle: "Quem faz o quê e por que quase sempre você usa os dois.",
    blocks: [
      p(`
Dockerfile: como construir a imagem (receita).
Compose: como rodar (e conectar) serviços (app, banco, cache…).
      `),
      ul([
        "Dockerfile = empacotar (build)",
        "Compose = orquestrar (run de múltiplos serviços, portas, volumes, envs)",
        "Compose pode usar image pronta OU buildar via Dockerfile"
      ]),
      code("Compose chamando build:", `services:
  web:
    build: .
    ports:
      - "8080:80"`),
    ],
  },

  {
    id: "monitoring",
    title: "10) Monitorar uso e ser transparente no dia a dia",
    subtitle: "O que monitorar e como criar disciplina para não estourar limite/custo.",
    blocks: [
      p(`
No mundo Docker: monitore “o que está rodando” e “quanto está consumindo”.
No mundo IA/agents: monitore “quanto você gastou hoje” e “por que gastou”.
      `),
      ul([
        "docker ps / docker stats (CPU/RAM por container)",
        "docker compose logs (entender erro rápido)",
        "Padronizar comandos e portas no README",
        "Quebrar tarefas: planejar → aplicar → testar (reduz retrabalho e custo)"
      ]),
      note(`
Se você usa agentes (Codex/Cursor/Windsurf), seja explícito:
“não varrer repo inteiro”, “trabalhar só em X pastas”, “responder em passos curtos”.
Isso economiza MUITO limite/tokens.
      `),
    ],
  },
];

function $(id) { return document.getElementById(id); }

function p(text) {
  return { type: "p", text: text.trim() };
}
function ul(items) {
  return { type: "ul", items };
}
function code(label, codeText) {
  return { type: "code", label, codeText };
}
function note(text) {
  return { type: "note", text: text.trim() };
}
function warn(text) {
  return { type: "warn", text: text.trim() };
}

function render(module) {
  $("title").textContent = module.title;
  $("subtitle").textContent = module.subtitle;

  const root = $("content");
  root.innerHTML = "";

  module.blocks.forEach(block => {
    if (block.type === "p") {
      const el = document.createElement("p");
      el.className = "leading-relaxed text-slate-200";
      el.textContent = block.text;
      root.appendChild(el);
    }

    if (block.type === "ul") {
      const el = document.createElement("ul");
      el.className = "list-disc pl-6 space-y-2 text-slate-200";
      block.items.forEach(i => {
        const li = document.createElement("li");
        li.textContent = i;
        el.appendChild(li);
      });
      root.appendChild(el);
    }

    if (block.type === "code") {
      const wrap = document.createElement("div");
      wrap.className = "rounded-2xl border border-slate-800 bg-slate-950/50 overflow-hidden";

      const top = document.createElement("div");
      top.className = "flex items-center justify-between border-b border-slate-800 px-4 py-2";
      const lbl = document.createElement("div");
      lbl.className = "text-sm font-semibold text-slate-200";
      lbl.textContent = block.label || "Código";
      const btn = document.createElement("button");
      btn.className = "text-xs rounded-lg border border-slate-700 px-3 py-1 hover:bg-slate-900";
      btn.textContent = "Copiar";
      btn.onclick = async () => {
        await navigator.clipboard.writeText(block.codeText);
        btn.textContent = "Copiado!";
        setTimeout(() => (btn.textContent = "Copiar"), 900);
      };

      top.appendChild(lbl);
      top.appendChild(btn);

      const pre = document.createElement("pre");
      pre.className = "p-4 text-sm overflow-auto text-slate-100";
      pre.textContent = block.codeText;

      wrap.appendChild(top);
      wrap.appendChild(pre);
      root.appendChild(wrap);
    }

    if (block.type === "note" || block.type === "warn") {
      const el = document.createElement("div");
      el.className =
        "rounded-2xl border p-4 " +
        (block.type === "note"
          ? "border-emerald-900/60 bg-emerald-950/20 text-emerald-100"
          : "border-amber-900/60 bg-amber-950/20 text-amber-100");
      el.textContent = block.text;
      root.appendChild(el);
    }
  });
}

function mountNav() {
  const nav = $("nav");
  nav.innerHTML = "";

  modules.forEach(m => {
    const btn = document.createElement("button");
    btn.className =
      "text-left rounded-xl border border-slate-800 bg-slate-950/30 px-3 py-2 hover:bg-slate-900/40";
    btn.innerHTML = `<div class="text-sm font-semibold">${m.title}</div>
                     <div class="text-xs text-slate-400 mt-1">${m.subtitle}</div>`;
    btn.onclick = () => {
      location.hash = m.id;
    };
    nav.appendChild(btn);
  });
}

function getModuleById(id) {
  return modules.find(m => m.id === id) || modules[0];
}

function syncFromHash() {
  const id = (location.hash || "#intro").replace("#", "");
  render(getModuleById(id));
}

mountNav();
window.addEventListener("hashchange", syncFromHash);
syncFromHash();