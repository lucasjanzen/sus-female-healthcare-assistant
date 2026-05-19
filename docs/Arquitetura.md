# CASF — Arquitetura do Sistema

**Centro de Assistência à Saúde Feminina**  
Sistema SUS para detecção precoce de depressão pós-parto, ansiedade gestacional e violência doméstica durante consultas médicas.

---

## 1. Visão Geral

```
Profissional de Saúde (Browser)
          │ HTTPS
          ▼
  ┌──────────────────┐
  │  Frontend Nginx   │  Angular 21 SPA
  │  :4200 → :80     │
  └────────┬─────────┘
           │ /api/* (proxy reverso)
           ▼
  ┌──────────────────┐       ┌─────────────────────┐
  │  Backend FastAPI  │──────▶│  PostgreSQL 16       │
  │  :8000            │       │  (sfha_db)           │
  └────────┬─────────┘       └─────────────────────┘
           │ .delay()
           ▼
  ┌──────────────────┐       ┌─────────────────────┐
  │  Redis           │──────▶│  Celery Worker       │
  │  (fila de tasks) │       │  (processar_analise) │
  └──────────────────┘       └────────┬────────────┘
                                      │
                    ┌─────────────────┼──────────────┐
                    ▼                 ▼              ▼
              Azure Blob         Azure  Azure      Azure
              Storage            Speech Language   OpenAI
              (áudio temp)       (STT)  (Sentim.)  (GPT-4o)
```

### Papéis de Usuário

| Papel | Acesso |
|---|---|
| `MEDICO` | Consultas, pacientes, análises, fila |
| `ENFERMEIRO` | Consultas, pacientes, análises, fila |
| `ADMIN` | Gestão de pacientes e usuários |

---

## 2. Frontend

**Stack:** Angular 21 · Angular Material · RxJS 7 · TypeScript 5.9 · SCSS

### Arquitetura Angular

```
frontend/src/app/
├── core/
│   ├── auth/               # AuthService, JWT signal, authGuard, roleGuard
│   ├── services/           # ApiService (wrapper HttpClient), ConsultaService, etc.
│   ├── models/             # Interfaces TypeScript
│   └── date/               # PtBrNativeDateAdapter (datepickers pt-BR)
├── features/
│   ├── auth/               # Tela de login
│   ├── home/               # Dashboard
│   ├── consulta/           # Fluxo de nova consulta (MatStepper)
│   │   ├── nova-consulta/  # Container com stepper
│   │   ├── step-identificacao/  # Busca paciente, tipo, DUM, TCLE
│   │   ├── step-triagem/        # Peso, pressão arterial
│   │   ├── step-atendimento/    # Relato, speech-to-text, notas clínicas
│   │   └── step-encerramento/   # Encerramento + PDF
│   ├── fila/               # Fila de atendimento
│   ├── analises/           # Resultados de análise IA
│   └── admin/              # Gestão de pacientes/usuários
└── shared/
    └── layout/             # Shell autenticado (sidebar, header)
```

### Autenticação no Frontend

- JWT armazenado em `localStorage` (chave `sfha_token`)
- `isAuthenticated` e `currentUser` são `computed()` signals derivados do token
- Interceptor HTTP (`auth.interceptor.ts`) anexa `Authorization: Bearer <token>` e redireciona para `/login` em 401
- Guards: `authGuard` (qualquer usuário autenticado) e `roleGuard(['ROLE'])` (papel específico)

### Build e Container

```dockerfile
# Stage 1 — Build
FROM node:22-alpine
RUN npm ci && npm run build --configuration=production

# Stage 2 — Runtime
FROM nginx:alpine
COPY dist/... /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**nginx.conf** — SPA routing + proxy reverso:

```nginx
location /         { try_files $uri $uri/ /index.html; }
location /api/     { proxy_pass http://api:8000/; }
```

### Configuração de Ambiente

| Arquivo | `apiUrl` |
|---|---|
| `environment.ts` (dev) | `http://localhost:8000` |
| `environment.prod.ts` (prod) | `/api` (proxy nginx) |

---

## 3. Backend

**Stack:** Python 3.12 · FastAPI 0.115 · SQLAlchemy 2 · Uvicorn · Alembic · pydantic-settings

### Estrutura de Pastas

```
api/
├── celery_app.py              # Instância Celery (broker Redis, inclui tasks)
└── app/
    ├── main.py                # App FastAPI, registro de routers, CORS
    ├── core/
    │   ├── config.py          # Settings (pydantic-settings, lê api/.env)
    │   ├── security.py        # JWT HS256, bcrypt
    │   ├── dependencies.py    # get_current_user, require_role()
    │   └── exception_handlers.py
    ├── db/
    │   └── session.py         # Engine + SessionLocal SQLAlchemy
    ├── models/                # ORM: user, paciente, consulta, audit_acessos
    ├── schemas/               # Pydantic request/response: auth, paciente, consulta, fila, analise
    ├── routers/
    │   ├── auth.py            # POST /auth/login, GET /auth/me
    │   ├── paciente.py        # GET/POST /pacientes
    │   ├── admin_paciente.py  # GET /admin/pacientes/*
    │   ├── fila.py            # GET/POST /fila/*
    │   ├── analise.py         # GET /analises/*
    │   ├── speech.py          # GET /speech/token
    │   └── consulta/
    │       ├── triagem.py     # GET/PATCH /consulta/{id}/triagem
    │       ├── atendimento.py # GET/PATCH /consulta/{id}/atendimento
    │       └── encerramento.py # POST /consulta/{id}/encerrar
    ├── services/
    │   ├── analise_llm_service.py # Integração Azure OpenAI (GPT-4o)
    │   ├── azure_service.py       # Azure Speech (transcrição) + Azure Language (sentimento)
    │   ├── blob_service.py        # Upload/download/delete no Azure Blob Storage
    │   └── encerramento_service.py # Geração de PDF (reportlab)
    └── tasks/
        ├── analise_task.py    # @shared_task Celery: transcr. + LLM + salva resultado
        └── consulta_timeout.py # Fecha consultas abertas > 4h
```

### Fluxo de Autenticação

```
POST /auth/login
  → valida email/senha (bcrypt)
  → gera JWT HS256 (payload: sub, nome, role)
  → TTL: 8 horas
```

### Endpoints Principais

| Método | Rota | Papel | Descrição |
|---|---|---|---|
| POST | `/auth/login` | — | Login e geração de token |
| GET | `/auth/me` | Qualquer | Dados do usuário atual |
| GET | `/pacientes` | MEDICO, ENFERMEIRO | Lista pacientes |
| POST | `/pacientes` | ADMIN | Cria paciente |
| GET | `/consulta/pacientes/buscar` | MEDICO, ENFERMEIRO | Busca por nome/CPF/CNS |
| POST | `/consulta/iniciar` | MEDICO, ENFERMEIRO | Inicia nova consulta |
| GET/PATCH | `/consulta/{id}/triagem` | MEDICO, ENFERMEIRO | Triagem |
| GET/PATCH | `/consulta/{id}/atendimento` | MEDICO, ENFERMEIRO | Atendimento |
| POST | `/consulta/{id}/encerrar` | MEDICO, ENFERMEIRO | Encerramento + análise |
| POST | `/speech/transcribe` | MEDICO, ENFERMEIRO | Transcrição de áudio |
| GET | `/analises/*` | MEDICO, ENFERMEIRO | Resultados de análise |
| GET | `/fila/*` | MEDICO, ENFERMEIRO | Fila de atendimento |
| GET | `/health` | — | Health check |

### Compliance LGPD

- CPF **nunca** armazenado em texto plano
- Armazenado apenas como `cpf_hash` = SHA-256 HMAC com `SECRET_SALT`
- Tabela `audit_acessos` tem trigger PostgreSQL que bloqueia UPDATE/DELETE (imutável)

### Container

```dockerfile
FROM python:3.12-slim
# Instala: libssl, libasound2, gstreamer, ffmpeg (requisitos Azure Speech)
RUN pip install -r requirements.txt
USER appuser  # executa como não-root
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 600
```

### Variáveis de Ambiente (api/.env)

| Variável | Obrigatório | Descrição |
|---|---|---|
| `DATABASE_URL` | Sim | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Sim | Chave para assinar JWT |
| `SECRET_SALT` | Sim | Salt para HMAC do CPF |
| `ALGORITHM` | Não (padrão `HS256`) | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_HOURS` | Não (padrão `8`) | TTL do token |
| `CORS_ORIGIN` | Não (padrão `http://localhost:4200`) | Origem permitida |
| `AZURE_SPEECH_KEY` | Sim | Chave do Azure Speech |
| `AZURE_SPEECH_REGION` | Sim | Região (ex: `brazilsouth`) |
| `AZURE_LANGUAGE_ENDPOINT` | Sim | Endpoint Azure Language |
| `AZURE_LANGUAGE_KEY` | Sim | Chave Azure Language |
| `AZURE_OPENAI_ENDPOINT` | Sim | Endpoint Azure OpenAI |
| `AZURE_OPENAI_API_KEY` | Sim | Chave Azure OpenAI |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Sim | Nome do deployment (ex: `gpt-4o`) |
| `AZURE_OPENAI_API_VERSION` | Não (padrão `2024-02-01`) | Versão da API |
| `AZURE_STORAGE_CONNECTION_STRING` | Sim | Connection string da Storage Account (Azure Blob) |
| `CELERY_BROKER_URL` | Não (padrão `redis://localhost:6379/0`) | URL do Redis para Celery |

---

## 4. Banco de Dados

**SGBD:** PostgreSQL 16  
**ORM:** SQLAlchemy 2  
**Migrações:** Alembic

### Schema de Tabelas

| Tabela | Propósito |
|---|---|
| `usuarios` | Profissionais com papel MEDICO / ENFERMEIRO / ADMIN |
| `pacientes` | Pacientes; CPF apenas como `cpf_hash` (SHA-256 HMAC) |
| `pacientes_log` | Log de auditoria de alterações em pacientes |
| `consultas_identidade` | Cabeçalho da consulta (status, tipo, DUM, IG, encaminhamento) |
| `consulta_triagem` | Peso e pressão arterial por consulta |
| `consulta_relato` | Relato da paciente e anotações clínicas |
| `consulta_resultado` | Resultado da análise IA (scores, indicadores, saída do LLM) |
| `historico_peso` | Histórico de peso por paciente entre consultas |
| `audit_acessos` | Log de acessos imutável (trigger bloqueia UPDATE/DELETE) |

### Status do Ciclo de Vida da Consulta

```
AGUARDANDO → ABERTA → EM_ATENDIMENTO → ENCERRADA
                                    ↘ TIMEOUT (após 4h via task)
```

### Migrações Alembic

```bash
alembic upgrade head                          # aplica todas as migrações
alembic revision --autogenerate -m "descricao"  # gera nova migração
```

Arquivos em `api/alembic/versions/`:
- `69c4df361ee9` — Schema inicial completo
- `a2b3c4d5e6f7` — Correções e histórico

---

## 5. Integrações Azure AI

| Serviço | SDK | Uso |
|---|---|---|
| **Azure Speech** | `azure-cognitiveservices-speech >= 1.36` | Transcrição de áudio do relato da paciente (speech-to-text) |
| **Azure Language** | `azure-ai-textanalytics 5.3` | Análise de sentimento do texto do relato |
| **Azure OpenAI** | `openai >= 1.30` (endpoint Azure) | Análise clínica com GPT-4o: scores de risco, indicadores, encaminhamento |

### Fluxo de Análise IA

```
Consulta encerrada
        │
        ├──▶ [se áudio] upload → Azure Blob Storage (casf-audio-temp)
        │
        └──▶ processar_analise.delay() → Redis
                                            │
                                            ▼
                                     Celery Worker
                                            │
                              ┌─────────────┴────────────┐
                              ▼                          ▼
                     [se áudio]                    sempre
                     download blob                 analise_llm_service.py
                     azure_service.py              └──▶ Azure OpenAI (GPT-4o)
                     ├──▶ Azure Speech                    → análise clínica estruturada
                     │    (transcrição + diarização)              │
                     └──▶ Azure Language                          ▼
                          (sentimento Paciente)       consulta_resultado (salvo no banco)
                                            │
                                            ▼
                                     delete blob (finally)
```

---

## 6. Infraestrutura Docker (Desenvolvimento/Local)

### docker-compose.yml

| Serviço | Imagem | Porta | Depende de |
|---|---|---|---|
| `db` | `postgres:16` | `5432:5432` | — |
| `redis` | `redis:7-alpine` | `6379:6379` | — |
| `api` | `./api` (Dockerfile) | `8000:8000` | `db` (healthy), `redis` (healthy) |
| `worker` | `./api` (mesmo Dockerfile) | — | `db` (healthy), `redis` (healthy) |
| `frontend` | `./frontend` (Dockerfile) | `4200:80` | `api` |

```yaml
volumes:
  postgres_data:    # persiste dados entre reinicializações
```

O `worker` usa a mesma imagem da `api`, mas executa `celery -A celery_app worker` em vez de `uvicorn`.

### Healthcheck do Banco

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U sfha"]
  interval: 5s
  timeout: 5s
  retries: 5
```

### Comandos Essenciais

```bash
docker-compose up --build                        # inicia tudo
docker-compose exec api alembic upgrade head     # aplica migrações
docker-compose exec api python seed.py           # popula dados de teste
```

---

## 7. Segurança

| Camada | Mecanismo |
|---|---|
| Autenticação | JWT HS256, 8h TTL |
| Senhas | bcrypt (passlib) |
| CPF | SHA-256 HMAC com SECRET_SALT (LGPD) |
| Auditoria | Tabela `audit_acessos` com trigger imutável |
| Autorização | `require_role()` dependency por endpoint |
| Transporte | HTTPS (nginx ou load balancer) |
| Container | Executa como usuário não-root (`appuser`) |
