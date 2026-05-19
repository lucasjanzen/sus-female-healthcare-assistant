# CASF — Guia de Deploy na Azure Cloud

**Centro de Assistência à Saúde Feminina**  
Recomendações e passo a passo para subir a aplicação na Microsoft Azure.

> **Pré-requisito:** leia o [ARQUITETURA.md](ARQUITETURA.md) para entender os componentes antes de prosseguir.

---

## 1. Mapeamento de Componentes → Serviços Azure

| Componente Atual | Serviço Azure | Motivo |
|---|---|---|
| PostgreSQL 16 (Docker volume) | **Azure Database for PostgreSQL Flexible Server** | Banco gerenciado, backups automáticos, compatível com Alembic |
| FastAPI container (`api`) | **Azure Container Apps** | Serverless containers, escalabilidade automática, sem gerenciar VMs |
| Celery Worker container (`worker`) | **Azure Container Apps** | Mesmo ambiente que a API, mesma imagem Docker |
| Redis container | **Azure Cache for Redis** | Gerenciado, persistência de tasks garantida, alta disponibilidade |
| Azure Blob Storage (`casf-audio-temp`) | **Azure Blob Storage** (Storage Account existente) | Container para áudio temporário durante análise — deletado após processamento |
| Angular + Nginx container (`frontend`) | **Azure Container Apps** | Mesmo ambiente que o backend, proxy interno simplificado |
| Imagens Docker | **Azure Container Registry (ACR)** | Registry privado integrado ao Container Apps |
| Variáveis de ambiente e secrets | **Azure Key Vault** | Rotação de secrets, integração nativa com Container Apps via Managed Identity |
| Logs e métricas | **Azure Monitor + Log Analytics Workspace** | Observabilidade centralizada |
| HTTPS / DNS | **Container Apps Ingress** | TLS automático, sem configurar certificates manualmente |
| Azure Speech (já provisionado) | Manter recurso existente | Apenas atualizar endpoint/chave nas variáveis |
| Azure Language (já provisionado) | Manter recurso existente | Apenas atualizar endpoint/chave nas variáveis |
| Azure OpenAI (já provisionado) | Manter recurso existente | Apenas atualizar endpoint/chave nas variáveis |

**Região recomendada para todos os recursos novos:** `brazilsouth`  
(dados de saúde sob LGPD devem permanecer no Brasil)

---

## 2. Diagrama de Arquitetura Azure

```
                         Internet
                             │ HTTPS
                             ▼
              ┌──────────────────────────────────────────┐
              │      Azure Container Apps Environment     │
              │                (brazilsouth)              │
              │                                          │
              │  ┌──────────────────────────────────┐   │
              │  │  Container App: casf-frontend     │   │
              │  │  Angular + Nginx                  │   │
              │  │  Ingress: externo (HTTPS público)  │   │
              │  └──────────────┬───────────────────┘   │
              │                 │ /api/* (HTTP interno)  │
              │  ┌──────────────▼───────────────────┐   │
              │  │  Container App: casf-api          │   │
              │  │  FastAPI + Uvicorn                │   │
              │  │  Ingress: interno apenas          │   │
              │  └──────────────┬───────────────────┘   │
              │                 │ .delay()              │
              │  ┌──────────────▼───────────────────┐   │
              │  │  Container App: casf-worker       │   │
              │  │  Celery Worker                    │   │
              │  │  Ingress: nenhum                  │   │
              │  └──────────────┬───────────────────┘   │
              └─────────────────┼────────────────────────┘
                                │
     ┌──────────────────────────┼───────────────────────────────┐
     │                          │                               │
     ▼                          ▼                               ▼
Azure Cache              Azure DB for               Azure Key Vault
for Redis                PostgreSQL                 (secrets, env vars)
(fila Celery)            Flexible Server
                         (brazilsouth)
     │                                              Azure Monitor
     │ (Managed Identity via Key Vault)             + Log Analytics
     ▼
Azure Blob Storage        Azure Speech        Azure Language    Azure OpenAI
(casf-audio-temp)         (já existente)      (já existente)    (já existente)
```

---

## 3. Variáveis de Ambiente → Azure Key Vault

Todos os secrets devem ser criados no Key Vault e referenciados no Container App via **Managed Identity** (sem hardcoded credentials).

### Secrets a criar no Key Vault

| Nome do Secret no Key Vault | Valor |
|---|---|
| `casf-database-url` | `postgresql://user:pass@<servidor>.postgres.database.azure.com:5432/sfha_db?sslmode=require` |
| `casf-secret-key` | String aleatória longa (≥ 32 chars) |
| `casf-secret-salt` | String aleatória longa (≥ 32 chars) |
| `casf-azure-speech-key` | Chave do Azure Speech existente |
| `casf-azure-speech-region` | `brazilsouth` (ou região do recurso) |
| `casf-azure-language-endpoint` | Endpoint do Azure Language existente |
| `casf-azure-language-key` | Chave do Azure Language existente |
| `casf-azure-openai-endpoint` | Endpoint do Azure OpenAI existente |
| `casf-azure-openai-api-key` | Chave do Azure OpenAI existente |
| `casf-azure-openai-deployment` | Nome do deployment (ex: `gpt-4o`) |
| `casf-storage-connection-string` | Connection string da Storage Account (portal.azure.com → Storage Account → Access keys) |
| `casf-celery-broker-url` | `redis://<host-redis>.redis.cache.windows.net:6380/0?ssl=True&password=<access-key>` |

### Variáveis de configuração (não-secret)

| Variável | Valor em produção |
|---|---|
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `8` |
| `CORS_ORIGIN` | URL pública do Container App frontend |
| `AZURE_OPENAI_API_VERSION` | `2024-02-01` |

---

## 4. Passo a Passo de Deploy

### Pré-requisitos

```bash
# Instalar Azure CLI
winget install Microsoft.AzureCLI

# Login
az login

# Definir variáveis de ambiente locais para o deploy
$RESOURCE_GROUP = "rg-casf-prod"
$LOCATION = "brazilsouth"
$ACR_NAME = "acrcasfprod"          # deve ser globalmente único
$KV_NAME = "kv-casf-prod"
$PG_SERVER = "pg-casf-prod"
$ENVIRONMENT = "cae-casf-prod"
```

---

### Etapa 1 — Criar Resource Group

```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

---

### Etapa 2 — Azure Container Registry (ACR)

```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Login no registry
az acr login --name $ACR_NAME
```

**Build e push das imagens:**

```bash
# Backend
docker build -t $ACR_NAME.azurecr.io/casf-api:latest ./api
docker push $ACR_NAME.azurecr.io/casf-api:latest

# Frontend
docker build -t $ACR_NAME.azurecr.io/casf-frontend:latest ./frontend
docker push $ACR_NAME.azurecr.io/casf-frontend:latest
```

---

### Etapa 3 — Azure Database for PostgreSQL Flexible Server

```bash
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $PG_SERVER \
  --location $LOCATION \
  --admin-user sfha \
  --admin-password "<senha-segura>" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 16 \
  --storage-size 32 \
  --database-name sfha_db \
  --public-access None    # sem acesso público, apenas via VNet ou Container Apps
```

> **Importante:** após criar, configure a regra de firewall ou integração com VNet para permitir acesso do Container Apps.

**Aplicar migrações Alembic contra o banco de produção:**

```bash
# Execute localmente apontando para o banco Azure (com tunnel ou IP temporário)
cd api
DATABASE_URL="postgresql://sfha:<senha>@<servidor>.postgres.database.azure.com:5432/sfha_db?sslmode=require" \
  alembic upgrade head
```

---

### Etapa 4 — Azure Key Vault

```bash
az keyvault create \
  --resource-group $RESOURCE_GROUP \
  --name $KV_NAME \
  --location $LOCATION \
  --enable-rbac-authorization true

# Criar secrets
az keyvault secret set --vault-name $KV_NAME --name "casf-database-url"    --value "postgresql://sfha:<senha>@<servidor>.postgres.database.azure.com:5432/sfha_db?sslmode=require"
az keyvault secret set --vault-name $KV_NAME --name "casf-secret-key"      --value "<string-aleatoria>"
az keyvault secret set --vault-name $KV_NAME --name "casf-secret-salt"     --value "<string-aleatoria>"
az keyvault secret set --vault-name $KV_NAME --name "casf-azure-speech-key"  --value "<sua-chave>"
# ... (repetir para todos os secrets da tabela na seção 3)
```

---

### Etapa 5 — Azure Cache for Redis

```bash
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name casf-redis \
  --location $LOCATION \
  --sku Basic \
  --vm-size C0

# Obter a connection string para usar no Key Vault
az redis list-keys --resource-group $RESOURCE_GROUP --name casf-redis
# Host: casf-redis.redis.cache.windows.net:6380
# CELERY_BROKER_URL: redis://casf-redis.redis.cache.windows.net:6380/0?ssl=True&password=<primary-key>
```

---

### Etapa 6 — Container Apps Environment

```bash
az containerapp env create \
  --name $ENVIRONMENT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

---

### Etapa 7 — Deploy do Backend (casf-api)

```bash
az containerapp create \
  --name casf-api \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image $ACR_NAME.azurecr.io/casf-api:latest \
  --registry-server $ACR_NAME.azurecr.io \
  --target-port 8000 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --secrets \
    database-url=keyvaultref:<URI-do-secret-casf-database-url>,identityref:<managed-identity-id> \
    secret-key=keyvaultref:<URI-casf-secret-key>,identityref:<managed-identity-id> \
    secret-salt=keyvaultref:<URI-casf-secret-salt>,identityref:<managed-identity-id> \
    azure-speech-key=keyvaultref:<URI-casf-azure-speech-key>,identityref:<managed-identity-id> \
  --env-vars \
    "DATABASE_URL=secretref:database-url" \
    "SECRET_KEY=secretref:secret-key" \
    "SECRET_SALT=secretref:secret-salt" \
    "AZURE_SPEECH_KEY=secretref:azure-speech-key" \
    "AZURE_SPEECH_REGION=brazilsouth" \
    "CORS_ORIGIN=https://casf-frontend.<hash>.brazilsouth.azurecontainerapps.io"
```

> O ingress `internal` garante que o backend não seja exposto diretamente à internet — apenas o frontend acessa via rede interna do Container Apps Environment.

---

### Etapa 8 — Deploy do Celery Worker (casf-worker)

O worker usa a **mesma imagem** da API (`casf-api`), mas com comando diferente e sem ingress:

```bash
az containerapp create \
  --name casf-worker \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image $ACR_NAME.azurecr.io/casf-api:latest \
  --registry-server $ACR_NAME.azurecr.io \
  --ingress disabled \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --command "celery" "-A" "celery_app" "worker" "--loglevel=info" "--concurrency=2" \
  --secrets \
    database-url=keyvaultref:<URI-casf-database-url>,identityref:<managed-identity-id> \
    celery-broker-url=keyvaultref:<URI-casf-celery-broker-url>,identityref:<managed-identity-id> \
    storage-connection-string=keyvaultref:<URI-casf-storage-connection-string>,identityref:<managed-identity-id> \
    azure-speech-key=keyvaultref:<URI-casf-azure-speech-key>,identityref:<managed-identity-id> \
  --env-vars \
    "DATABASE_URL=secretref:database-url" \
    "CELERY_BROKER_URL=secretref:celery-broker-url" \
    "AZURE_STORAGE_CONNECTION_STRING=secretref:storage-connection-string" \
    "AZURE_SPEECH_KEY=secretref:azure-speech-key" \
    "AZURE_SPEECH_REGION=brazilsouth"
```

> O worker não expõe porta alguma (`--ingress disabled`). Ele só consome tasks do Redis.

---

### Etapa 9 — Deploy do Frontend (casf-frontend)

```bash
az containerapp create \
  --name casf-frontend \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image $ACR_NAME.azurecr.io/casf-frontend:latest \
  --registry-server $ACR_NAME.azurecr.io \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.25 \
  --memory 0.5Gi
```

O ingress `external` gera automaticamente um endpoint HTTPS público (TLS gerenciado pela Azure).

**Após o deploy, atualizar `CORS_ORIGIN` na API com a URL real do frontend:**

```bash
az containerapp update \
  --name casf-api \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars "CORS_ORIGIN=https://<url-real-do-frontend>"
```

---

### Etapa 10 — Configurar nginx.conf para o ambiente Azure

O `nginx.conf` atual usa `proxy_pass http://api:8000/` (hostname Docker). Na Azure, o hostname interno do Container App é diferente. Atualize antes do build da imagem de produção:

```nginx
# frontend/nginx.conf — produção Azure
location /api/ {
    proxy_pass http://casf-api/;  # nome do Container App interno
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

> O Container Apps resolve automaticamente `casf-api` para o IP interno quando ambos estão no mesmo Environment.

---

## 5. Considerações LGPD na Azure

| Requisito LGPD | Implementação |
|---|---|
| Dados no Brasil | Todos os recursos em `brazilsouth` |
| CPF pseudonimizado | SHA-256 HMAC já implementado — `SECRET_SALT` no Key Vault |
| Auditoria imutável | Trigger PostgreSQL na tabela `audit_acessos` — compatível com Azure DB for PostgreSQL |
| Acesso restrito | Backend com ingress interno; frontend com HTTPS obrigatório |
| Rotação de secrets | Azure Key Vault com versioning automático |
| Logs de acesso | Azure Monitor captura todos os logs do Container Apps |

---

## 6. Monitoramento

```bash
# Habilitar Log Analytics no Container Apps Environment
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name law-casf-prod \
  --location $LOCATION

# Consultar logs da API em tempo real
az containerapp logs show \
  --name casf-api \
  --resource-group $RESOURCE_GROUP \
  --follow
```

**Health check:** o endpoint `GET /health` da API retorna `{"status": "ok"}` — configure como probe no Container App para restart automático em falha.

---

## 7. Checklist de Deploy

### Infraestrutura
- [ ] Resource Group criado em `brazilsouth`
- [ ] Azure Container Registry criado e imagens publicadas
- [ ] Azure DB for PostgreSQL Flexible Server criado
- [ ] Migrações Alembic aplicadas (`alembic upgrade head`)
- [ ] Azure Cache for Redis criado (Basic C0)
- [ ] Azure Blob Storage: container `casf-audio-temp` criado na Storage Account existente
- [ ] Azure Key Vault criado com todos os secrets (incluindo `casf-storage-connection-string` e `casf-celery-broker-url`)

### Aplicação
- [ ] `nginx.conf` atualizado com hostname interno do Container App (para produção)
- [ ] Container App Environment criado
- [ ] Container App `casf-api` com ingress **interno** deployado
- [ ] Container App `casf-worker` com ingress **desabilitado** deployado
- [ ] Container App `casf-frontend` com ingress **externo** deployado
- [ ] `CORS_ORIGIN` atualizado na API com a URL pública do frontend
- [ ] Verificar `GET /health` retornando `{"status": "ok"}`
- [ ] Testar login com credencial de teste (`medico@sfha.dev` / `senha123`)
- [ ] Encerrar uma consulta com áudio e verificar que o worker processa (logs do casf-worker)

### Segurança
- [ ] Managed Identity habilitado nos Container Apps `casf-api` e `casf-worker`
- [ ] Managed Identity com permissão `Key Vault Secrets User` no Key Vault
- [ ] Backend não acessível externamente (ingress interno confirmado)
- [ ] Worker sem ingress (ingress disabled confirmado)
- [ ] HTTPS funcionando no frontend (TLS automático do Container Apps)

### Pós-deploy
- [ ] `seed.py` executado se necessário para dados iniciais
- [ ] Azure Monitor configurado com alertas de erro
- [ ] Backups automáticos habilitados no Azure DB for PostgreSQL
- [ ] Verificar container `casf-audio-temp` fica vazio após análises (blobs sendo deletados)

---

## 8. Estimativa de Custo (brazilsouth)

> Estimativas aproximadas — consulte a [Azure Pricing Calculator](https://azure.microsoft.com/pt-br/pricing/calculator/) para valores exatos.

| Serviço | Configuração | Custo/mês estimado |
|---|---|---|
| Azure DB for PostgreSQL Flexible | Standard_B1ms, 32 GB | ~USD 25–40 |
| Container Apps (api) | 0.5 vCPU, 1 GB, 1–3 réplicas | ~USD 10–30 |
| Container Apps (worker) | 0.5 vCPU, 1 GB, 1–2 réplicas | ~USD 5–15 |
| Container Apps (frontend) | 0.25 vCPU, 0.5 GB, 1–2 réplicas | ~USD 5–15 |
| Azure Cache for Redis | Basic C0, 250 MB | ~USD 16 |
| Azure Blob Storage | Centavos (blobs deletados após uso) | < USD 1 |
| Azure Container Registry | Basic | ~USD 5 |
| Azure Key Vault | Standard | ~USD 1–5 |
| Azure Monitor | Log Analytics básico | ~USD 5–15 |
| **Total estimado** | | **~USD 72–142/mês** |

> Os serviços Azure Speech, Language e OpenAI são cobrados por uso — verifique as cotas dos recursos existentes.
