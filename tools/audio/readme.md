# CASF — Gerador de Áudios de Teste

Ferramenta para gerar áudios de conversas simuladas entre médico e paciente,
usados para testar o pipeline de análise de voz e LLM do sistema CASF.

---

## Estrutura

```
tools/audio/
├── gerar_audios.py        # script principal
├── requirements.txt       # dependências Python
├── roteiros/              # textos dos diálogos
│   ├── ana_silva.txt
│   ├── maria_oliveira.txt
│   └── julia_santos.txt
└── output/                # áudios gerados (criada automaticamente)
    ├── audio_ana_silva.wav
    ├── audio_maria_oliveira.wav
    └── audio_julia_santos.wav
```

---

## Pré-requisitos

### 1. Python 3.10+

### 2. Dependências Python

```bash
pip install -r requirements.txt
```

Não é necessário instalar nenhuma dependência de sistema.
Os arquivos são gerados em `.wav`, processado nativamente pelo Python
e aceito diretamente pelo Azure Speech.

---

## Como usar

```bash
cd tools/audio
python gerar_audios.py
```

Os arquivos `.wav` são gerados automaticamente em `output/`.

---

## Roteiros disponíveis

| Arquivo | Paciente | Tipo | Indicadores esperados | Faixa |
|---|---|---|---|---|
| ana_silva.txt | Ana Silva | Pré-natal | Depressão (ALTO) + Ideação | VERMELHO |
| maria_oliveira.txt | Maria Oliveira | Ginecológica | Ansiedade (ALTO) + Isolamento | LARANJA |
| julia_santos.txt | Julia Santos | Pré-natal | Violência Doméstica (ALTO) | VERMELHO |

---

## Como adicionar um novo roteiro

1. Criar um novo arquivo `.txt` em `roteiros/`
2. Usar o formato abaixo — o parser identifica os falantes pelo prefixo:

```
# Comentários começam com #

MÉDICO:
Texto da fala do médico aqui.

PACIENTE:
Texto da fala da paciente aqui.
(pausa)

MÉDICO:
Próxima fala.

PACIENTE:
(pausa longa)
Resposta após pausa longa.
```

Marcações de pausa disponíveis:
- `(pausa)` — pausa de ~750ms
- `(pausa longa)` — pausa de ~1500ms, usada em momentos de hesitação

3. Registrar o novo roteiro em `gerar_audios.py` na lista `ROTEIROS_CONFIG`:

```python
ROTEIROS_CONFIG = [
    ...
    {"arquivo": "novo_roteiro.txt", "saida": "audio_novo.wav"},
]
```

---

## Vozes

O script usa duas vozes do Google TTS com entonações levemente distintas:

| Falante | Configuração |
|---|---|
| Médico | `lang=pt`, `tld=com.br` |
| Paciente | `lang=pt`, `tld=pt` |

A diferença é sutil mas suficiente para a diarização do Azure Speech
identificar dois falantes distintos na transcrição.

---

## Observações

- Os áudios são gerados com conexão com a internet (API do Google TTS)
- Cada roteiro leva entre 30 e 60 segundos para ser gerado
- O script é idempotente — rodar novamente sobrescreve os arquivos em `output/`
- Os arquivos temporários em `_temp/` são deletados automaticamente ao final