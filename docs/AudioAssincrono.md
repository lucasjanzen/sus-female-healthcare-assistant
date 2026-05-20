# Processamento Assíncrono de Áudio
## Como funciona o Celery + Redis + Azure Blob Storage no sistema

---

## O problema que o Celery resolve

Sem processamento assíncrono, o fluxo seria bloqueante:

```
Médico clica "Encerrar"
       ↓
API recebe o áudio
       ↓
Azure Speech transcreve... (15–30s)
       ↓
GPT-4o analisa... (10–20s)
       ↓
Resultado salvo
       ↓
API retorna resposta ← médico esperou até 60 segundos
```

Com Celery + Redis, o médico não espera nada:

```
Médico clica "Encerrar"
       ↓
API salva encerramento + faz upload do áudio para Azure Blob
       ↓
API enfileira task no Redis (.delay) e retorna imediatamente ← médico liberado em < 1s
       ↓ (em background, processo separado)
Celery Worker baixa áudio do Blob → Azure Speech → GPT-4o → DB → deleta Blob
       ↓
Resultado aparece na Fila de Análises
```

A diferença crítica para `BackgroundTasks` do FastAPI: se a API reiniciar (deploy, crash), a task **permanece na fila Redis** e é processada quando o worker está disponível. Com `BackgroundTasks`, a task seria perdida.

---

## Por que Azure Blob Storage para o áudio

Celery serializa argumentos em JSON antes de enviar ao Redis. `bytes` não é serializável em JSON, então o áudio não pode ser passado diretamente na mensagem.

A solução: o endpoint salva o áudio no Azure Blob Storage e passa apenas o **nome do blob** (string) na mensagem Celery. O worker baixa o blob, processa e o deleta no bloco `finally`.

Vantagens sobre alternativas (arquivo em `/tmp`, pickle):
- API e worker podem rodar em containers/máquinas diferentes sem volume compartilhado
- Áudio sobrevive a falhas do worker — está no Blob enquanto não for processado
- Mensagens Redis pequenas (apenas o nome do blob, ~50 bytes)

---

## Os 3 componentes

### 1. Celery — a biblioteca Python

Define e executa as tasks. Configurado em `api/celery_app.py`:

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "casf",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
    include=["app.tasks.analise_task"],
)
```

A task em `api/app/tasks/analise_task.py` usa `@shared_task` com retry automático:

```python
@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def processar_analise(self, id_consulta_str, blob_name=None, content_type="audio/webm"):
    # 1. Baixa o áudio do Azure Blob (se presente)
    if blob_name:
        audio_bytes = download_audio(blob_name)
        resultado_voz = transcrever_e_analisar_voz(audio_bytes, content_type)
        transcricao = resultado_voz["transcricao"]
        sentimento_voz = resultado_voz["sentimento_voz"]

    # 2. GPT-4o analisa tudo e gera o resultado
    resultado_llm = analise_llm_service.analisar_com_llm(id_consulta, db, transcricao, sentimento_voz)

    # 3. Salva resultado no banco
    ...
    db.commit()
```

O bloco `finally` sempre deleta o blob, mesmo em caso de erro.

### 2. Redis — a fila intermediária

Banco de dados em memória que armazena as tasks pendentes.
Funciona como uma lista: a API empurra tasks (`.delay()`), o Worker as consome.

```
API → [ task1, task2, task3 ] → Worker
             REDIS
```

Configurado via variável de ambiente:
```
CELERY_BROKER_URL=redis://sfha_redis:6379/0
```

### 3. Worker — o processo executor

Processo separado que fica em loop consumindo tasks do Redis.

```bash
celery -A celery_app worker --loglevel=info --concurrency=2
```

---

## Fluxo completo no CASF

```
1. Médico encerra a consulta (com ou sem áudio gravado)
         ↓
2. POST /consulta/{id}/encerrar  (multipart/form-data)
         ↓
3. Backend:
   - Salva consulta como ENCERRADA no banco
   - Se áudio presente: upload para Azure Blob Storage (container: casf-audio-temp)
     blob_name = "{id_consulta}.webm"
   - Chama: processar_analise.delay(id, blob_name, content_type)
   - Retorna resposta imediatamente
         ↓
4. Redis recebe a task e aguarda
         ↓
5. Celery Worker pega a task
         ↓
6. Se blob_name presente:
   blob_service.download_audio(blob_name)
   azure_service.transcrever_e_analisar_voz()
   - Converte para WAV
   - Envia para Azure Speech SDK (ConversationTranscriber)
   - Recebe: transcrição com diarização Médico/Paciente
   - Recebe: sentimento_voz via Azure Language (sentimento da Paciente)
         ↓
7. analise_llm_service.analisar_com_llm()
   - Coleta: parecer médico (consulta_relato)
   - Coleta: transcrição + sentimento_voz
   - Coleta: dados da consulta (peso, PA, IG, tipo)
   - Coleta: histórico das últimas 5 consultas + peso
   - Monta prompt e envia para Azure OpenAI GPT-4o
   - Recebe: sumario_estruturado + texto_clinico + score
         ↓
8. Salva em consulta_resultado
9. Atualiza analise_concluida_em em consultas_identidade
10. Deleta o blob do Azure Blob Storage (bloco finally)
         ↓
11. Consulta aparece na Fila de Análises (/analises)
    ordenada por score decrescente
```

---

## Cenário sem áudio

Se o médico não gravou áudio, o fluxo é idêntico exceto que as etapas de Blob e Azure Speech são puladas:

```
POST /consulta/{id}/encerrar (sem campo audio)
         ↓
processar_analise.delay(id, blob_name=None)
         ↓
GPT-4o analisa apenas o parecer médico + histórico
         ↓
Resultado salvo e disponível na Fila de Análises
```

---

## Frontend

O `EncerramentoService` (`encerramento.service.ts`) envia o áudio via `FormData`:

```typescript
encerrar(idConsulta: string, audioBlob?: Blob | null): Observable<EncerramentoSimplesOut> {
  const formData = new FormData();
  if (audioBlob) {
    formData.append('audio', audioBlob, 'recording.webm');
  }
  return this.api.post<EncerramentoSimplesOut>(`/consulta/${idConsulta}/encerrar`, formData);
}
```

`HttpClient` detecta `FormData` automaticamente e define `Content-Type: multipart/form-data` com o boundary correto.

---

## Tratamento de falhas

O Celery tem retry automático configurado:

```python
@shared_task(bind=True, max_retries=2, default_retry_delay=60)
```

- Tenta até 2 vezes em caso de falha (Azure Speech indisponível, GPT-4o timeout, etc.)
- Aguarda 60s antes de tentar novamente
- Se todas as tentativas falharem: erro salvo em `consultas_identidade.analise_erro`
- A consulta aparece na Fila de Análises com chip vermelho "Erro"
- O profissional pode acionar o reprocessamento manualmente

O blob do áudio é deletado apenas no `finally` da última tentativa — se o worker crashar no meio, o blob permanece no Azure Blob Storage e a task será reprocessada pelo Redis.

---

## Como rodar localmente

Três processos precisam estar rodando simultaneamente:

```bash
# Terminal 1 — PostgreSQL + Redis
docker compose up -d db redis

# Terminal 2 — API FastAPI
cd api && task dev

# Terminal 3 — Celery Worker
cd api && task worker
```

> **Windows:** `task worker` já inclui `--pool=solo`, necessário para evitar erros de permissão do multiprocessing no Windows (`PermissionError WinError 5`). Em Linux/macOS o pool padrão (prefork) é usado automaticamente.

Via Docker Compose (recomendado para produção local):

```bash
docker compose up --build
# Sobe: db, redis, api, worker, frontend
```

Se o worker não estiver rodando, as tasks ficam acumuladas no Redis e as consultas nunca aparecem na Fila de Análises.

---

## Segurança do áudio

| Requisito | Implementação |
|---|---|
| Sem persistência em banco | Nunca armazenado em nenhuma tabela do banco |
| Retenção mínima | Deletado do Azure Blob imediatamente após processamento (bloco `finally`) |
| Acesso restrito ao upload | Apenas o endpoint com role `MEDICO` recebe o arquivo |
| Container isolado | `casf-audio-temp` — separado de outros dados do sistema |
| Transmissão segura | HTTPS em produção; Azure Blob usa HTTPS nativamente |
