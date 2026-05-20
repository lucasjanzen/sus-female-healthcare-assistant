# Deploy com Docker Compose na Google Cloud (Free Tier)

Guia baseado no deploy real do projeto **sus-female-healthcare-assistant (sfha)**.

---

## Pré-requisitos

- Conta no [Google Cloud](https://cloud.google.com) com Free Tier ativado
- Imagens Docker publicadas no GitHub Container Registry (GHCR)
- Arquivos `docker-compose.prod.yml`, `.env` (raiz) e `api/.env` prontos

---

## 1. Criar a VM no Google Cloud Console

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Menu lateral → **Compute Engine → VM instances**
3. Clique em **"Create Instance"** e configure:

| Campo | Valor |
|---|---|
| Name | `sfha-vm` |
| Region | `us-central1` |
| Zone | `us-central1-a` |
| Machine type | `e2-micro` (Free Tier — grátis permanente) |
| Boot disk | Ubuntu 24.04 LTS, 30GB Standard persistent disk |
| Firewall | Marcar **Allow HTTP** e **Allow HTTPS** |

4. Clique em **Create**

---

## 2. Fixar IP estático

Por padrão o IP muda ao reiniciar a VM. Para fixar:

```bash
# No Cloud Shell do Google Cloud (ícone >_ no portal)

# Remover IP dinâmico atual
gcloud compute instances delete-access-config sfha-vm \
  --access-config-name="External NAT" \
  --zone=us-central1-a

# Criar IP estático
gcloud compute addresses create sfha-static-ip \
  --region=us-central1

# Associar à VM
gcloud compute instances add-access-config sfha-vm \
  --access-config-name="External NAT" \
  --address=$(gcloud compute addresses describe sfha-static-ip --region=us-central1 --format="get(address)") \
  --zone=us-central1-a

# Verificar o IP fixado
gcloud compute addresses describe sfha-static-ip \
  --region=us-central1 \
  --format="get(address)"
```

Anote o IP — ele será usado no `CORS_ORIGIN` do `.env`.

---

## 3. Verificar regras de firewall

As regras `default-allow-http` (porta 80) e `default-allow-https` (porta 443) devem existir e estar associadas à VM via tags.

```bash
# Verificar regras
gcloud compute firewall-rules list

# Verificar tags da VM
gcloud compute instances describe sfha-vm \
  --zone=us-central1-a \
  --format="get(tags.items)"

# Se as tags não existirem, adicionar
gcloud compute instances add-tags sfha-vm \
  --tags http-server,https-server \
  --zone us-central1-a
```

---

## 4. Conectar na VM

No Console, em **Compute Engine → VM instances**, clique em **SSH** na linha da VM — abre terminal no navegador.

---

## 5. Instalar Docker na VM

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verificar instalação
docker --version
docker compose version
```

---

## 6. Configurar os arquivos na VM

```bash
# Criar estrutura de pastas
mkdir -p ~/sfha/api
cd ~/sfha
```

### docker-compose.prod.yml

Crie ou transfira o arquivo. O compose deve usar imagens do GHCR (sem `build`):

```yaml
services:
  db:
    image: postgres:16
    container_name: sfha_db
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    expose:
      - "5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: sfha_redis
    expose:
      - "6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  api:
    image: ghcr.io/SEU_USUARIO/sfha-api:latest
    container_name: sfha_api
    expose:
      - "8000"
    env_file:
      - .env
      - api/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  worker:
    image: ghcr.io/SEU_USUARIO/sfha-api:latest
    container_name: sfha_worker
    command: celery -A celery_app worker --loglevel=info --concurrency=2
    env_file:
      - .env
      - api/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    image: ghcr.io/SEU_USUARIO/sfha-frontend:latest
    container_name: sfha_frontend
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
```

### .env (raiz)

```dotenv
POSTGRES_DB=sfha_db
POSTGRES_USER=sfha
POSTGRES_PASSWORD=SUA_SENHA

DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
CELERY_BROKER_URL=redis://redis:6379/0
```

> **Atenção:** evite `@`, `#`, `"`, `'` na senha — são caracteres reservados em URLs ou no parser do `.env`.

### api/.env

```dotenv
DATABASE_URL=postgresql://sfha:SUA_SENHA@db:5432/sfha_db
CELERY_BROKER_URL=redis://redis:6379/0

SECRET_KEY=gere_com_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=8

CORS_ORIGIN=http://SEU_IP_ESTATICO

SECRET_SALT=gere_com_openssl_rand_hex_32

# outras variáveis específicas da aplicação...
```

Para gerar `SECRET_KEY` e `SECRET_SALT`:

```bash
openssl rand -hex 32
```

---

## 7. Autenticar no GHCR e subir os containers

O build das imagens deve ser feito **localmente** — a VM tem recursos limitados e o build do frontend pode levar mais de 50 minutos. Fazendo o build local e publicando no GHCR, o deploy na VM se resume a um `pull` de poucos minutos.

### 7.1 Localmente — build e push das imagens

Gere o token em: **github.com → Settings → Developer settings → Personal access tokens → Classic**
com permissões: `write:packages` e `read:packages`.

```bash
# Autenticar no GHCR
echo "SEU_TOKEN_GITHUB" | docker login ghcr.io -u SEU_USUARIO_GITHUB --password-stdin

# Build das imagens
docker build -t ghcr.io/SEU_USUARIO/sfha-api:latest ./api
docker build -t ghcr.io/SEU_USUARIO/sfha-frontend:latest ./frontend

# Push para o GHCR
docker push ghcr.io/SEU_USUARIO/sfha-api:latest
docker push ghcr.io/SEU_USUARIO/sfha-frontend:latest
```

> **Atenção:** antes do build, garanta que `api/.dockerignore` e `frontend/.dockerignore` contenham `.env` para não vazar credenciais nas imagens.

### 7.2 Na VM — pull e subir os containers

```bash
# Autenticar no GHCR (só na primeira vez)
echo "SEU_TOKEN_GITHUB" | docker login ghcr.io -u SEU_USUARIO_GITHUB --password-stdin

# Baixar as imagens prontas do GHCR
docker compose -f docker-compose.prod.yml pull

# Subir os containers
docker compose -f docker-compose.prod.yml up -d

# Verificar status
docker compose -f docker-compose.prod.yml ps
```

---

## 8. Rodar migrações e seeds

```bash
# Migrações do banco
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Dados base (obrigatório)
docker compose -f docker-compose.prod.yml exec api python seed.py

# Histórico (opcional)
docker compose -f docker-compose.prod.yml exec api python seed-history.py
```

---

## 9. Verificar acesso

```bash
# Testar localmente na VM
curl -I http://localhost

# Testar externamente
curl -I http://SEU_IP_ESTATICO
```

Acesse no navegador:

- **Frontend:** `http://SEU_IP_ESTATICO`
- **API (Swagger):** `http://SEU_IP_ESTATICO:8000/docs`

---

## Comandos úteis do dia a dia

```bash
# Ver status dos containers
docker compose -f docker-compose.prod.yml ps

# Ver logs em tempo real
docker compose -f docker-compose.prod.yml logs -f

# Reiniciar um serviço específico
docker compose -f docker-compose.prod.yml restart api

# Atualizar imagens e recriar containers
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# Parar tudo
docker compose -f docker-compose.prod.yml down
```

---

## Observações importantes

- **Portas 5432 (Postgres) e 6379 (Redis) não devem ser expostas publicamente** — use `expose` no compose, não `ports`
- **Nunca commitar `.env` no repositório** — adicione ao `.gitignore`
- **Adicionar `.dockerignore`** em `api/` e `frontend/` com `.env` listado para não vazar credenciais nas imagens
- **O IP pode mudar** se a VM for reiniciada sem IP estático — sempre fixe o IP conforme o passo 2
- **Worker e API usam a mesma imagem** — qualquer alteração no código rebuilda os dois
