# CASF — Centro de Assistência à Saúde Feminina

Assistente para auxiliar nas consultas médicas realizadas pelo SUS em mulheres, buscando detectar sinais precoces de depressão pós-parto, ansiedade gestacional e violência doméstica.

---

## Requisitos

- Docker e Docker Compose
- Node.js 22+ (desenvolvimento local do frontend)
- Python 3.12+ (desenvolvimento local do backend)

---

## Serviços Azure necessários

| Serviço | Finalidade |
|---------|-----------|
| **Azure AI Speech** | Transcreve o áudio da consulta em texto com diarização (pt-BR) |
| **Azure AI Language** | Analisa sentimento do relato da paciente |
| **Azure OpenAI (GPT-4o)** | Análise clínica: scores de risco, indicadores e encaminhamento |
| **Azure Blob Storage** | Armazena o áudio temporariamente durante o processamento assíncrono |

### Como obter as credenciais

**Azure AI Speech**
1. Portal Azure → **Criar recurso** → **Azure AI services** → **Speech service**
2. Após criar, vá em **Keys and Endpoint**
3. Copie a **Key 1** e a **Region** (ex: `brazilsouth`)

**Azure AI Language**
1. Portal Azure → **Criar recurso** → **Azure AI services** → **Language service**
2. Após criar, vá em **Keys and Endpoint**
3. Copie a **Key 1** e o **Endpoint**

**Azure OpenAI**
1. Portal Azure → **Azure OpenAI** → seu recurso → **Keys and Endpoint**
2. Copie a **Key 1**, o **Endpoint** e o nome do **Deployment** (ex: `gpt-4o`)

**Azure Blob Storage**
1. Portal Azure → **Storage Account** → seu recurso → **Access keys**
2. Copie a **Connection string** da Key 1
3. O container `casf-audio-temp` é criado automaticamente pelo sistema

### Configuração no `api/.env`

```env
AZURE_SPEECH_KEY=<sua chave>
AZURE_SPEECH_REGION=brazilsouth

AZURE_LANGUAGE_ENDPOINT=https://<nome>.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=<sua chave>

AZURE_OPENAI_ENDPOINT=https://<nome>.openai.azure.com/
AZURE_OPENAI_API_KEY=<sua chave>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01

AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
```

---

## Início Rápido com Docker

### 1. Configure as variáveis de ambiente

```bash
cp api/.env.example api/.env
# Edite api/.env com suas credenciais Azure e chaves secretas
```

> **Importante:** Altere `SECRET_KEY` e `SECRET_SALT` para strings aleatórias seguras antes de usar em produção.

### 2. Suba os serviços

```bash
docker-compose up --build
```

Serviços iniciados: `db` (PostgreSQL), `redis`, `api` (FastAPI), `worker` (Celery), `frontend` (Angular/Nginx).

### 3. Aplique as migrações e popule o banco

Em outro terminal, após os serviços subirem:

```bash
# Aplica as migrações do banco de dados
docker-compose exec api alembic upgrade head

# Usuários e pacientes base (obrigatório)
docker-compose exec api python seed.py

# Histórico de consultas encerradas (opcional — habilita análise LLM com contexto histórico)
docker-compose exec api python seed-history.py
```

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

| Perfil | Consultas | Pacientes | Análises | Admin |
|--------|:---------:|:---------:|:--------:|:-----:|
| MEDICO | ✓ | leitura | ✓ | — |
| ENFERMEIRO | ✓ | leitura | ✓ | — |
| ADMIN | — | ✓ | — | ✓ |

---

## Desenvolvimento Local

### Backend (FastAPI)

**1. Suba o banco de dados e o Redis via Docker:**

```bash
docker-compose up -d db redis
```

**2. Instale as dependências Python:**

```bash
cd api
python -m venv .venv
.venv\Scripts\activate             # Windows
# source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
```

**3. Crie o arquivo `api/.env`** apontando para `localhost` seguindo `api/.env.example`:

> **Por que `api/.env` e não o `.env` raiz?**
> O `.env` raiz usa `db:5432` e `sfha_redis:6379` (hostnames do Docker Compose). Fora do Docker, use `localhost`.

**4. Inicie a API** (com venv ativado):

```bash
task dev
```

**5. Inicie o worker Celery** (em outro terminal, com venv ativado):

```bash
cd api
task worker
```

> O worker é necessário para processar as análises IA após o encerramento das consultas. Sem ele, as consultas ficam aguardando na fila.

#### Scripts disponíveis (`api/`)

| Comando | Descrição |
|---------|-----------|
| `task dev` | Sobe o servidor com hot-reload |
| `task worker` | Sobe o Celery worker (análises IA) |
| `task migrate` | Aplica migrações do banco (`alembic upgrade head`) |
| `task seed` | Insere usuários e pacientes de teste |
| `task seed-history` | Insere histórico de consultas encerradas (requer `task seed`) |
| `task format` | Formata todos os arquivos Python com ruff |
| `task lint` | Lint + auto-fix com ruff |
| `task check` | Verifica formatação e lint sem alterar arquivos (CI) |

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
| `npm run format` | Formata arquivos TS, HTML e SCSS com Prettier |

---

## Estrutura do Projeto

```
sus-female-healthcare-assistant/
├── api/                              # Backend FastAPI + Celery
│   ├── celery_app.py                 # Instância Celery (broker Redis)
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py             # Settings (pydantic-settings)
│   │   │   ├── security.py           # bcrypt + JWT HS256
│   │   │   └── dependencies.py       # get_current_user, require_role
│   │   ├── db/
│   │   │   └── session.py            # Engine e SessionLocal
│   │   ├── models/                   # ORM: usuarios, pacientes, consultas, audit
│   │   ├── schemas/                  # Pydantic: auth, paciente, consulta, analise
│   │   ├── routers/
│   │   │   ├── auth.py               # POST /auth/login, GET /auth/me
│   │   │   ├── paciente.py           # GET /pacientes
│   │   │   ├── admin_paciente.py     # GET/POST /admin/pacientes
│   │   │   ├── fila.py               # GET /fila
│   │   │   ├── analise.py            # GET /analises
│   │   │   ├── speech.py             # GET /speech/token
│   │   │   └── consulta/
│   │   │       ├── triagem.py        # GET/PATCH /consulta/{id}/triagem
│   │   │       ├── atendimento.py    # GET/PATCH /consulta/{id}/atendimento
│   │   │       └── encerramento.py   # POST /consulta/{id}/encerrar
│   │   ├── services/
│   │   │   ├── analise_llm_service.py  # Azure OpenAI (GPT-4o)
│   │   │   ├── azure_service.py        # Azure Speech + Azure Language
│   │   │   ├── blob_service.py         # Azure Blob Storage (áudio temp)
│   │   │   └── encerramento_service.py # Geração de PDF
│   │   └── tasks/
│   │       ├── analise_task.py         # @shared_task Celery: transcrição + LLM
│   │       └── consulta_timeout.py     # Fecha consultas abertas > 4h
│   ├── alembic/                      # Migrações do banco
│   ├── seed.py                       # Usuários e pacientes de teste
│   ├── seed-history.py               # Histórico de consultas
│   └── requirements.txt
│
├── frontend/                         # Frontend Angular 21
│   └── src/app/
│       ├── core/
│       │   ├── auth/                 # AuthService, authGuard, roleGuard, interceptor
│       │   ├── models/               # Interfaces TypeScript
│       │   └── services/             # ApiService e serviços de feature
│       ├── features/
│       │   ├── auth/                 # Tela de login
│       │   ├── home/                 # Dashboard
│       │   ├── consulta/             # Fluxo nova consulta (MatStepper 4 etapas)
│       │   ├── fila/                 # Fila de atendimento
│       │   ├── analises/             # Resultados de análise IA
│       │   └── admin/                # Gestão de pacientes e usuários
│       └── shared/layout/            # Shell autenticado (sidebar, header)
│
├── docs/                             # Documentação técnica
│   ├── Arquitetura.md
│   ├── AudioAssincrono.md
│   ├── AzureDeploy.md
│   └── FluxoAtendimento.md
│
├── docker-compose.yml                # db, redis, api, worker, frontend
├── api/.env.example
└── README.md
```

---

## Endpoints da API

| Método | Rota | Perfil | Descrição |
|--------|------|--------|-----------|
| POST | `/auth/login` | — | Autenticação |
| GET | `/auth/me` | Qualquer | Dados do usuário logado |
| GET | `/health` | — | Status da API |
| GET | `/pacientes` | MEDICO, ENFERMEIRO | Lista pacientes |
| POST | `/pacientes` | ADMIN | Cria paciente |
| GET | `/admin/pacientes` | ADMIN | Lista pacientes (admin) |
| GET | `/consulta/pacientes/buscar` | MEDICO, ENFERMEIRO | Busca por nome/CPF/CNS |
| POST | `/consulta/iniciar` | MEDICO, ENFERMEIRO | Inicia nova consulta |
| GET/PATCH | `/consulta/{id}/triagem` | MEDICO, ENFERMEIRO | Triagem (peso, PA) |
| GET/PATCH | `/consulta/{id}/atendimento` | MEDICO, ENFERMEIRO | Relato e notas clínicas |
| POST | `/consulta/{id}/encerrar` | MEDICO, ENFERMEIRO | Encerra consulta e inicia análise IA |
| GET | `/fila` | MEDICO, ENFERMEIRO | Fila de atendimento |
| GET | `/analises` | MEDICO, ENFERMEIRO | Resultados de análise IA |
| GET | `/speech/token` | MEDICO, ENFERMEIRO | Token Azure Speech (STT no browser) |

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

---

## Fluxo de Análise IA

Ao encerrar uma consulta, a análise ocorre de forma assíncrona — o médico não precisa aguardar:

```
Encerrar consulta
      ↓
Se áudio gravado → upload para Azure Blob Storage
      ↓
processar_analise.delay() → enfileira no Redis (< 1s)
      ↓ (em background)
Celery Worker:
  ├── Se áudio: Azure Speech (transcrição) → Azure Language (sentimento)
  └── Azure OpenAI GPT-4o (análise clínica)
      ↓
Resultado salvo no banco → aparece na Fila de Análises
```

A análise usa o relato textual do médico + transcrição do áudio (se presente) + histórico das últimas 5 consultas da paciente.

---

## Segurança e LGPD

| Requisito | Implementação |
|-----------|---------------|
| Autenticação | JWT HS256, TTL 8h |
| Senhas | bcrypt (passlib) |
| CPF | Nunca armazenado — apenas SHA-256 HMAC com `SECRET_SALT` |
| Áudio | Nunca persiste no banco — deletado do Blob após análise |
| Auditoria | Tabela `audit_acessos` com trigger imutável (sem UPDATE/DELETE) |
| Autorização | `require_role()` por endpoint |
| Container | Executa como usuário não-root (`appuser`) |
