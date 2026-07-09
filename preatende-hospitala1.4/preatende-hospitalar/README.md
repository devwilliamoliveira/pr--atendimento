#  PreAtende — Sistema de Pré-atendimento Hospitalar

Sistema web de **pré-atendimento e triagem hospitalar**, feito em **Python (Flask)**,
acessível tanto pelo **navegador (HTML responsivo, instalável como app/PWA)** quanto
por uma **API REST em JSON** pronta para ser consumida por um aplicativo móvel
(Flutter, React Native, Ionic, etc.) ou qualquer outro cliente HTTP.

>  **Aviso importante:** este software é uma ferramenta de apoio à priorização de
> atendimento. Ele **não substitui** avaliação médica presencial. Em emergências reais,
> procure imediatamente o pronto-socorro ou o serviço de emergência local (192/193 no Brasil).

---

##  Funcionalidades

- **Cadastro e login de pacientes** (senha com hash seguro, sessão protegida).
- **Formulário de pré-atendimento**: queixa principal, sintomas, escala de dor,
  sinais vitais (pressão, frequência cardíaca/respiratória, temperatura, saturação de O2)
  e sinais de alerta (ex.: dor no peito, falta de ar, sangramento intenso).
- **Classificação automática de risco**, inspirada no Protocolo de Manchester,
  em 5 níveis: 🔴 Emergência · 🟠 Muito urgente · 🟡 Urgente · 🟢 Pouco urgente · 🔵 Não urgente.
- **Fila de atendimento** para a equipe de saúde (perfil `profissional`/`admin`),
  ordenada automaticamente por prioridade clínica.
- **API REST em JSON com autenticação JWT**, com os mesmos recursos do site,
  pronta para alimentar um aplicativo mobile.
- **PWA**: o site pode ser "instalado" na tela inicial do celular como um app.
- Testes automatizados (17 testes cobrindo motor de triagem, rotas web e API).

---

##  Segurança implementada

- Senhas com hash (`werkzeug.security`), nunca armazenadas em texto puro.
- Sessões web via `Flask-Login` com cookies `HttpOnly` e `SameSite=Lax`.
- Autenticação de API via **JWT** (`Flask-JWT-Extended`), sem uso de cookies.
- Proteção **CSRF** em todos os formulários HTML (`Flask-WTF`).
- **Rate limiting** em rotas sensíveis (login e criação de conta) via `Flask-Limiter`.
- Controle de acesso por perfil (`paciente`, `profissional`, `admin`), com bloqueio 403.
- Cabeçalhos de segurança HTTP (`X-Frame-Options`, `X-Content-Type-Options`,
  `Content-Security-Policy`, `Permissions-Policy`, `Referrer-Policy`).
- Validação de entrada em todos os formulários e na API (whitelist de campos e faixas de valores).
- Segredos (chaves, banco de dados) sempre via variáveis de ambiente — nunca hardcoded.
- **A aplicação se recusa a iniciar em modo produção (`FLASK_ENV=production`)** se `SECRET_KEY`
  ou `JWT_SECRET_KEY` não estiverem definidas com valores fortes (mínimo 32 caracteres, diferentes
  dos valores padrão de desenvolvimento). Isso evita o erro comum de subir para produção esquecendo
  de trocar as chaves.
- Redirecionamento pós-login (`?next=`) validado contra *open redirect*: só aceita caminhos internos.
- Cabeçalho `Strict-Transport-Security` (HSTS) ativado automaticamente quando os cookies estão
  configurados como `Secure` (produção via HTTPS).
- ORM (`SQLAlchemy`) previne injeção de SQL.

---

##  Estrutura do projeto

```
preatende-hospitalar/
├── app/
│   ├── __init__.py          # application factory, segurança, CLI
│   ├── config.py            # configurações (dev/prod/test)
│   ├── extensions.py        # db, login, jwt, csrf, limiter
│   ├── models.py            # User e Triagem
│   ├── forms.py             # formulários com validação
│   ├── triage_engine.py     # motor de classificação de risco
│   ├── utils.py             # decorators de autorização
│   ├── auth/                # rotas de login/registro/logout
│   ├── web/                 # páginas HTML (site)
│   ├── api/                 # API JSON (para apps/integrações)
│   ├── templates/           # HTML (Jinja2)
│   └── static/               # CSS, JS, ícones, manifest PWA
├── tests/                   # testes automatizados (pytest)
├── requirements.txt
├── run.py                   # ponto de entrada
├── .env.example
└── README.md
```

---

##  Como rodar localmente

### 1. Pré-requisitos
- Python 3.10+

### 2. Instalação

```bash
git clone https://github.com/SEU_USUARIO/preatende-hospitalar.git
cd preatende-hospitalar

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # edite as chaves secretas do .env
```

### 3. Rodar o servidor

```bash
export $(cat .env | xargs)      # Windows: configure as variáveis manualmente
python run.py
```

Acesse **http://localhost:5000**

### 4. Criar uma conta de profissional/admin

Contas de paciente se cadastram sozinhas pelo site. Contas da equipe de saúde são
criadas via linha de comando (para não permitir que qualquer pessoa vire "profissional"):

```bash
export FLASK_APP=run.py
flask criar-profissional "Dra. Ana Souza" ana@hospital.com SenhaForte123
flask criar-profissional "Admin Geral" admin@hospital.com SenhaForte123 --admin
```

### 5. Rodar os testes

```bash
pip install pytest
python -m pytest -v
```

---

##  Acesso via aplicativo (mobile)

O sistema expõe uma **API REST em `/api/v1`** que pode ser usada por um app mobile
nativo ou híbrido (Flutter, React Native, Ionic, Kotlin, Swift, etc.). Principais endpoints:

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/registrar` | Cria conta de paciente, retorna token JWT |
| POST | `/api/v1/auth/login` | Login, retorna token JWT |
| GET | `/api/v1/auth/me` | Dados do usuário logado |
| POST | `/api/v1/triagens` | Cria um novo pré-atendimento |
| GET | `/api/v1/triagens` | Lista pré-atendimentos (próprios ou todos, se profissional) |
| GET | `/api/v1/triagens/<id>` | Detalhe de um pré-atendimento |
| GET | `/api/v1/fila` | Fila priorizada (somente profissional/admin) |
| PATCH | `/api/v1/triagens/<id>/status` | Atualiza status (somente profissional/admin) |

Autenticação: envie o token no cabeçalho `Authorization: Bearer <token>`.

Além disso, como o site é um **PWA**, o usuário pode abri-lo no celular e escolher
"Adicionar à tela inicial" para usá-lo como um aplicativo instalado, sem precisar
de loja de aplicativos.


---

##  Próximos passos

- [ ] Enviar notificações (e-mail/SMS/push) quando o status do pré-atendimento mudar.
- [ ] Painel de métricas para gestores (tempo médio de espera por cor de risco).
- [ ] Multi-idioma (i18n).
- [ ] Deploy com PostgreSQL + Redis (rate limiting distribuído) em produção.
- [ ] App mobile nativo consumindo a API `/api/v1`.

---

## Licença

Distribuído sob a licença MIT — veja [LICENSE](LICENSE).
