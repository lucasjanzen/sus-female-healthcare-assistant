# PrenaIA — Sistema de Assistência à Saúde Feminina

Assistente para auxiliar nas consultas médicas realizadas pelo SUS em mulheres, buscando detectar sinais precoces de depressão pós-parto, ansiedade gestacional e violência doméstica.

---

## Requisitos

- Docker e Docker Compose
- Node.js 22+ (desenvolvimento local do frontend)
- Python 3.12+ (desenvolvimento local do backend)

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

```bash
cd api
python -m venv .venv
# source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate             # Windows
pip install -r requirements.txt
```

Configure o `.env` com `DATABASE_URL` apontando para seu PostgreSQL local:

```
DATABASE_URL=postgresql://sfha:sfha@localhost:5432/sfha_db
CORS_ORIGIN=http://localhost:4200
```

Inicie o servidor:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend (Angular 21)

```bash
cd frontend
npm install
ng serve
```

Acesse em http://localhost:4200.

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
