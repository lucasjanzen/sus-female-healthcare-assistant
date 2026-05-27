### Arquitetura
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
