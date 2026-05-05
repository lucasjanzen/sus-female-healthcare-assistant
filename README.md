# CASF - Centro de Assistência à Saúde Feminina

Assistente para auxiliar nas consultas médicas realizadas pelo SUS em mulheres, buscando detectar sinais precoces de depressão pós-parto, ansiedade gestacional e violência doméstica.

---

## Requisitos

- Docker e Docker Compose
- Node.js 22+ (desenvolvimento local do frontend)
- Python 3.12+ (desenvolvimento local do backend)

---

## Inteligência Artificial (Azure AI)

A análise psicossocial e a transcrição de áudio das consultas utilizam dois serviços do Azure AI. Ambos são **opcionais**: quando não configurados, o sistema usa detecção local por palavras-chave (fallback automático).

| Serviço | Finalidade |
|---------|-----------|
| **Azure AI Speech** | Transcreve o áudio da consulta em texto (pt-BR) |
| **Azure AI Language** | Analisa sentimento do relato para calibrar o nível de risco |

### Como obter as credenciais

**Azure AI Speech**
1. Acesse [portal.azure.com](https://portal.azure.com) → **Criar recurso** → **Azure AI services** → **Speech service**
2. Após criar, vá em **Keys and Endpoint**
3. Copie a **Key 1** e a **Region** (ex: `brazilsouth`)

**Azure AI Language**
1. Acesse [portal.azure.com](https://portal.azure.com) → **Criar recurso** → **Azure AI services** → **Language service**
2. Após criar, vá em **Keys and Endpoint**
3. Copie a **Key 1** e o **Endpoint** (ex: `https://<nome>.cognitiveservices.azure.com/`)

### Configuração

Adicione as variáveis abaixo no arquivo `api/.env`:

```env
AZURE_SPEECH_KEY=<sua chave>
AZURE_SPEECH_REGION=brazilsouth

AZURE_LANGUAGE_ENDPOINT=https://<nome-do-recurso>.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=<sua chave>
```

> Deixe as variáveis em branco para usar o fallback local. Os logs da API indicam qual modo está ativo (`"Azure Speech nao configurado"` ou `"Sentimento Azure obtido"`).

---

## Início Rápido com Docker

### 1. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

> **Importante:** Altere `SECRET_KEY` para uma string aleatória segura antes de usar em produção.

### 2. Suba os serviços

```bash
docker-compose up --build
```

### 3. Popule o banco com dados de teste

Em outro terminal, após os serviços subirem:

```bash
docker-compose exec api python seed.py
```

> **Desenvolvimento local (sem o container `api`):** execute direto com o Python do venv:
> ```bash
> cd api
> .venv\Scripts\python.exe seed.py   # Windows
> # .venv/bin/python seed.py         # Linux/macOS
> ```

### 4. Acesse a aplicação

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:4200 |
| API (Swagger) | http://localhost:8000/docs |

---

## Usuários de Teste

| E-mail | Senha | Perfil |
|--------|-------|--------|
| medico@sfha.dev | senha123 | MEDICO |
| enfermeiro@sfha.dev | senha123 | ENFERMEIRO |
| admin@sfha.dev | senha123 | ADMIN |

---

## Permissões por Perfil

| Perfil | Acessa /home | Botão Nova Consulta |
|--------|:---:|:---:|
| MEDICO | ✓ | ✓ |
| ENFERMEIRO | ✓ | ✓ |
| ADMIN | ✓ | — |

---

## Desenvolvimento Local

### Backend (FastAPI)

**1. Suba apenas o banco de dados via Docker:**

```bash
docker-compose up -d db
```

O PostgreSQL ficará disponível em `localhost:5432` com usuário `sfha`, senha `sfha` e banco `sfha_db`.

**2. Instale as dependências Python:**

```bash
cd api
python -m venv .venv
# source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate             # Windows
pip install -r requirements.txt
```

**3. Crie o arquivo `api/.env`** com a URL apontando para `localhost` (diferente do Docker, que usa o hostname `db`):

```env
DATABASE_URL=postgresql://sfha:sfha@localhost:5432/sfha_db
SECRET_KEY=troque-por-uma-string-aleatoria-longa-e-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=8
CORS_ORIGIN=http://localhost:4200

# Azure AI (opcional — deixe em branco para usar fallback local)
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
AZURE_LANGUAGE_ENDPOINT=
AZURE_LANGUAGE_KEY=
```

> **Por que `api/.env` e não o `.env` raiz?**
> O `.env` raiz usa `db:5432` (hostname do serviço Docker Compose). Quando o backend roda fora do Docker, o hostname `db` não existe — use `localhost:5432`, que é a porta exposta pelo container.

**4. Inicie o servidor** (com venv ativado):

```bash
task dev
```

#### Scripts disponíveis (`api/`)

| Comando | Descrição |
|---------|-----------|
| `task dev` | Sobe o servidor com hot-reload |
| `task format` | Formata todos os arquivos Python com ruff |
| `task lint` | Lint + auto-fix com ruff |
| `task check` | Verifica formatação e lint sem alterar arquivos (CI) |

> Requer `taskipy` e `ruff` instalados: `pip install -r requirements.txt`

### Frontend (Angular 21)

```bash
cd frontend
npm install
ng serve
```

Acesse em http://localhost:4200.

#### Scripts disponíveis (`frontend/`)

| Comando | Descrição |
|---------|-----------|
| `npm start` | Sobe o servidor de desenvolvimento |
| `npm run build` | Build de produção |
| `npm test` | Executa os testes unitários |
| `npm run format` | Formata todos os arquivos TS, HTML e SCSS com Prettier |

---

## Estrutura do Projeto

```
sus-female-healthcare-assistant/
├── api/                        # Backend FastAPI
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py       # Settings (pydantic-settings)
│   │   │   ├── security.py     # bcrypt + JWT
│   │   │   └── dependencies.py # get_current_user, require_role
│   │   ├── db/
│   │   │   └── session.py      # Engine e SessionLocal
│   │   ├── models/
│   │   │   └── user.py         # SQLAlchemy model (tabela: usuarios)
│   │   ├── routers/
│   │   │   └── auth.py         # POST /auth/login, GET /auth/me
│   │   ├── schemas/
│   │   │   └── auth.py         # Pydantic schemas
│   │   └── main.py
│   ├── seed.py                 # Dados de teste
│   └── requirements.txt
│
├── frontend/                   # Frontend Angular 21
│   └── src/
│       └── app/
│           ├── core/
│           │   ├── auth/       # AuthService, AuthGuard, RoleGuard, Interceptor
│           │   ├── models/     # Interfaces TypeScript
│           │   └── services/   # ApiService base
│           └── features/
│               ├── auth/login/ # Tela de login
│               └── home/       # Tela home
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Endpoints da API

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | `/auth/login` | Autenticação | — |
| GET | `/auth/me` | Dados do usuário logado | Bearer |
| GET | `/health` | Status da API | — |

### Exemplo de login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "medico@sfha.dev", "password": "senha123"}'
```

Resposta:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```
