# Guia de Desenvolvimento da Aplicação

Este documento descreve o fluxo de trabalho para expandir a aplicação e o passo a passo para integrar autenticação com Google.

---

## 🚀 Fluxo de Desenvolvimento

Para adicionar novas funcionalidades (ex: Criar uma tabela de "Produtos"), siga este ciclo:

### 1. Criar a Migration (SQL)
Crie um novo arquivo na pasta `sql/` com um prefixo numérico para manter a ordem.
**Exemplo:** `sql/02_produtos.sql`

```sql
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Rodar a Migration
Execute o script de migração para atualizar o banco de dados.

```bash
python migration.py
```
*Selecione o arquivo novo ou "Rodar Todos".*

### 3. Atualizar o Backend (`main.py`)
Adicione as rotas para manipular os novos dados.

```python
@app.route('/produtos')
def listar_produtos():
    # Conexão com banco e select...
    return render_template('produtos.html', produtos=lista)
```

### 4. Criar o Frontend (`templates/`)
Crie o arquivo HTML correspondente (ex: `templates/produtos.html`) usando o padrão visual do projeto.

---

## 🔐 Guia de Autenticação com Google

Para permitir que usuários façam login com sua conta Google, precisamos configurar o OAuth 2.0.

### Passo 1: Configurar no Google Cloud Platform (GCP)

> [!WARNING]
> COMPLICAÇÃO: Este passo **NÃO PODE SER AUTOMATIZADO**.
> O Google exige configuração manual por motivos de segurança. Não há script que possa criar o "Client ID" e "Secret" para você. É chato, mas é necessário para produção.
>
> **Alternativa (Para Estudo):** Podemos criar um "Login Fake" no código que simula o Google, apenas para você testar o fluxo sem precisar configurar nada agora.

1.  Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2.  Crie um **Novo Projeto**.
3.  No menu lateral, vá em **APIs e Serviços** > **Tela de permissão OAuth**.
    *   Tipo de usuário: **Externo**.
    *   Preencha os dados obrigatórios (Nome do App, Email).
4.  Vá em **Credenciais** > **Criar Credenciais** > **ID do cliente OAuth**.
    *   Tipo de Aplicativo: **Aplicação Web**.
    *   **URIs de redirecionamento autorizados**: Adicione `http://127.0.0.1:5000/login/google/callback`.
5.  **Copie e Salve**:
    *   `Client ID`
    *   `Client Secret`

### Passo 2: Instalar Dependências

Precisaremos de bibliotecas extras para lidar com OAuth.

```bash
pip install authlib requests
```
*(Adicione isso ao `setup.py` na lista REQUIREMENTS para automatizar)*

### Passo 3: Atualizar `main.py`

Adicione a configuração do OAuth no seu app Flask.

```python
from authlib.integrations.flask_client import OAuth

# Configuração
app.config['GOOGLE_CLIENT_ID'] = 'SEU_CLIENT_ID'
app.config['GOOGLE_CLIENT_SECRET'] = 'SEU_CLIENT_SECRET'

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def authorize():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    
    # Lógica: Verificar se email existe no banco
    # Se sim -> Loga
    # Se não -> Registra automaticamente e Loga
    
    session['email'] = user_info['email']
    session['name'] = user_info['name']
    return redirect(url_for('dashboard'))
```

### Passo 4: Botão no Frontend

Adicione o botão de login no `templates/login.html`.

```html
<a href="/login/google" class="w-full flex items-center justify-center gap-2 bg-white text-gray-700 border border-gray-300 font-medium py-2 rounded-lg hover:bg-gray-50 transition">
    <img src="https://www.svgrepo.com/show/475656/google-color.svg" class="w-5 h-5" alt="Google">
    Entrar com Google
</a>
```

---

## 📝 Resumo

1.  **Migrations**: Sempre comece pelo banco (`sql/` -> `migration.py`).
2.  **Google Auth**: Exige configuração externa (GCP) antes de mexer no código.
