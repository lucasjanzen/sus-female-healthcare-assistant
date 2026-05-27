# Roteiro de Apresentação — CASF

## Context
O usuário precisa de um roteiro de apresentação do sistema CASF para demonstrar
processamento multimodal (áudio + texto), integração Azure, detecção de anomalias
e fluxo de alerta à equipe médica. Serão usados 2 casos: Caso 2 (Maria Oliveira —
violência doméstica, VERMELHO) e Caso 3 (Ana Silva — rotina, VERDE).

---

## Casos Escolhidos

| # | Paciente | CPF | Tipo | Resultado |
|---|----------|-----|------|-----------|
| A | Maria Oliveira | 555.666.777-88 | GINECOLOGICA | VERMELHO — Violência Doméstica (ALTO) |
| B | Ana Silva | 111.222.333-44 | GINECOLOGICA | VERDE — sem indicadores |

> Motivo: Maria é mais impactante que Julia para o público (violência doméstica é
> visualmente clara nos dados — equimoses, isolamento imposto, pausa ao ser questionada).
> Ana serve como controle perfeito, mostrando que o sistema não gera falsos positivos.

---

## Roteiro Completo

### [0:00 – 1:00] ABERTURA — O Problema

**Fala sugerida:**
> "O SUS atende milhões de mulheres por ano. Sinais de depressão perinatal, ansiedade e
> violência doméstica aparecem nessas consultas — mas são frequentemente perdidos porque
> o médico tem menos de 15 minutos por paciente. O CASF é um assistente clínico que
> observa a consulta em segundo plano e alerta a equipe quando detecta risco."

**Pontos a enfatizar:**
- O sistema não interrompe o atendimento
- Tudo roda de forma assíncrona — o médico nunca espera pela IA
- Dados permanecem no Brasil (região `brazilsouth` da Azure)

### IMPORTANTE: Mostrar Arquitetura

---

### [1:00 – 3:00] ETAPA 1 — TRIAGEM (login como Enfermeiro)

**Ação na tela:**
1. Login: `enfermeiro@sfha.dev` / `senha123`
2. Buscar paciente: **Maria Oliveira** (CPF `555.666.777-88`)
3. Tipo de consulta: **GINECOLOGICA** (sem DUM)
4. Preencher triagem:
   - Peso: `63.0 kg`
   - PA Sistólica: `132 mmHg`
   - PA Diastólica: `86 mmHg`
5. Confirmar TCLE e avançar

**Fala:**
> "O enfermeiro inicia a consulta. CPF nunca é armazenado em texto claro — o sistema
> guarda apenas um hash criptográfico, por conformidade com a LGPD."

---

### [3:00 – 5:30] ETAPA 2 — CONSULTA CLÍNICA (trocar para Médico)

**Ação na tela:**
1. Login: `medico@sfha.dev` / `senha123`
2. Assumir a consulta de Maria na fila
3. Mostrar o histórico de peso (gráfico de tendência) e histórico de consultas:
   - 210 dias atrás: AMARELO — evasiva sobre vida doméstica
   - 120 dias atrás: LARANJA — hematoma, referência ao companheiro
   - 45 dias atrás: VERMELHO — equimose periorbital, comportamento de fuga

**Fala:**
> "Antes mesmo de o médico digitar qualquer coisa, o sistema já exibe o histórico completo.
> Três consultas anteriores mostram uma escalada clara de violência doméstica."

4. Iniciar gravação de áudio (botão de microfone)
5. Digitar o parecer médico:

```
Paciente chegou com manga longa em dia de calor. Ao examinar o braço 
para aferir a pressão, foram visíveis múltiplas equimoses em diferentes 
estágios de cicatrização — algumas recentes, outras mais antigas. 
Atribuiu ao "bater nos móveis com frequência". Durante toda a consulta 
manteve postura fechada, braços cruzados, respostas monossilábicas. 
Quando questionada sobre como estava em casa, disse "normal" e mudou 
de assunto. Ao ser perguntada diretamente se alguém a machucava, fez 
uma pausa longa, olhou para a porta e disse que não. Mencionou que 
o marido "tem cuidado" dela. Relatou não dormir bem há semanas, 
sem apetite, sem vontade de sair de casa. Disse que parou de ver 
as amigas porque o marido prefere que fique em casa.
```

**Fala enquanto digita:**
> "O médico registra o parecer clínico. O sistema aceita texto livre — sem formulários
> rígidos que quebram o fluxo da consulta."

---

### [5:30 – 6:30] ETAPA 3 — ENCERRAMENTO E ENVIO PARA A IA

**Ação na tela:**
1. Parar gravação de áudio
2. Clicar em "Encerrar Consulta"
3. Mostrar que a resposta da API é imediata (< 1 segundo)

**Fala:**
> "Ao encerrar, o sistema faz duas coisas em paralelo: libera o médico para o próximo
> paciente imediatamente, e enfileira a análise no Celery — um worker em background que
> vai processar o áudio e o texto usando os serviços Azure."

**Mostrar diagrama (opcional — quadro ou slide):**
```
Encerrar → API responde em <1s → Redis enfileira → Celery Worker processa
                                                        ├── Azure Blob (áudio)
                                                        ├── Azure Speech (transcrição)
                                                        ├── Azure Language (sentimento)
                                                        └── Azure OpenAI GPT-4o (análise)
```

---

### [6:30 – 9:00] ETAPA 4 — PROCESSAMENTO MULTIMODAL (explicar enquanto processa)

**Fala enquanto aguarda o resultado:**
> "Três serviços Azure trabalham em sequência:"

**Azure AI Speech:**
> "Primeiro, o Speech converte o áudio WebM para WAV e transcreve a conversa com
> diarização — separa automaticamente a fala do médico da fala da paciente.
> Isso é fundamental: o sistema analisa principalmente o que a *paciente* diz,
> não o que o médico pergunta."

**Azure AI Language:**
> "Em seguida, o Language analisa o sentimento da fala da paciente — tom emocional,
> confiança nas respostas, pausas. Neste caso, respostas monossilábicas com sentimento
> negativo são um sinal claro."

**Azure OpenAI GPT-4o:**
> "Por fim, o GPT-4o recebe tudo: transcrição, sentimento, notas clínicas, sinais
> vitais e os últimos 5 atendimentos. Ele gera um score de 0 a 100, classifica os
> indicadores e escreve um texto clínico estruturado."

> "O áudio nunca é salvo no banco — é deletado do Azure Blob logo após o processamento,
> por exigência da LGPD."

---

### [9:00 – 11:00] ETAPA 5 — FILA DE ANÁLISES (resultado de Maria)

**Ação na tela:**
1. Abrir a Fila de Análises
2. Mostrar Maria no topo (VERMELHO, score ~88/100)

**Fala:**
> "A fila é ordenada por score — os casos mais críticos sempre aparecem primeiro.
> Uma enfermeira ou médico em qualquer turno consegue ver, de relance, quem precisa
> de atenção urgente."

3. Clicar em Maria para abrir o painel de resultado

**Mostrar e comentar:**
- Score: `85–95 / 100` → faixa VERMELHO
- Indicador **Violência Doméstica — ALTO**:
  > "Equimoses múltiplas em diferentes estágios, isolamento social imposto pelo
  > companheiro, pausa longa ao ser questionada diretamente."
- Indicador **Depressão — MODERADO**: insônia, sem apetite
- Indicador **Isolamento Social — ALTO**: impedida de ver amigas

**Fala:**
> "O sistema não apenas detecta — ele cita as evidências específicas do texto.
> O médico consegue revisar e, se necessário, ajustar antes de encaminhar."

4. Mostrar o contexto histórico na análise:
> "Padrão progressivo de 3 consultas anteriores — o modelo considera isso.
> Não é um episódio isolado: é uma escalada documentada."

5. Clicar **"Paciente Encaminhada"** → CVR, DELEGACIA_MULHER, CAPS
6. Item some da fila

---

### [11:00 – 13:00] CASO CONTROLE — Ana Silva (VERDE)

**Ação na tela:**
1. Como Enfermeiro: buscar Ana Silva (CPF `111.222.333-44`)
2. Triagem: Peso `63.5`, PA `112/72`
3. Como Médico: assumir, digitar o parecer positivo:

```
Paciente veio para consulta ginecológica de rotina anual. Chegou 
sorridente, comunicativa. Refere estar bem no trabalho — foi 
promovida recentemente. Relacionamento estável há 3 anos, companheiro 
presente e apoiador. Dorme bem, 7 a 8 horas por noite. Alimentação 
equilibrada, pratica caminhada três vezes por semana. Sem queixas 
ginecológicas. Sem sintomas de ansiedade ou alteração de humor. 
Rede de apoio sólida com família e amigas próximas.
```

4. Gravar áudio com o roteiro do `CasosDeTeste.txt` (diálogo Médico/Paciente)
5. Encerrar consulta

**Aguardar processamento e mostrar na Fila:**
- Ana aparece no final da lista (VERDE, score ~10/100)
- Clicar para abrir: **nenhum indicador relevante**
- Texto clínico: recomenda retorno de rotina apenas
- Clicar **"Revisar sem encaminhar"**

**Fala:**
> "Esse caso é tão importante quanto o anterior. Ele demonstra que o sistema não gera
> falsos positivos. Uma paciente saudável recebe score baixo, não consome atenção clínica
> desnecessária, e a equipe pode focar nos casos que realmente precisam."

---

### [13:00 – 14:00] FECHAMENTO — Fila vazia

**Ação na tela:**
- Mostrar a Fila de Análises vazia após revisar os dois casos

**Fala:**
> "Dois casos processados. Um encaminhado para rede de proteção. Um confirmado como
> saudável. A equipe pode continuar o trabalho com mais segurança — sabendo que têm
> um segundo par de olhos treinado em cada atendimento."

**Encerramento:**
> "CASF não substitui o médico. Ele amplifica a capacidade humana de detectar o
> que, em 15 minutos de consulta, às vezes passa despercebido."

---

## Requisitos Mapeados → Partes do Roteiro

| Requisito | Onde aparece no roteiro |
|-----------|------------------------|
| Análise de áudio | Etapas 2–4: gravação + Azure Speech + diarização |
| Análise de vídeo* | Não implementado — **não mencionar** ou explicar que o MVP foca em áudio + texto |
| Detecção de anomalias | Etapa 5: indicadores ALTO detectados no caso Maria |
| Integração Azure | Etapa 4: Speech, Language, OpenAI, Blob Storage |
| Fluxo de alerta | Etapa 5: fila ordenada por risco → encaminhamento CVR/DELEGACIA |

> *Se a banca questionar "vídeo": o sistema captura áudio da consulta (não vídeo) por
> privacidade. O processamento multimodal combina áudio + texto clínico + dados vitais.

---

## Perguntas Prováveis da Banca

**"E se os serviços Azure estiverem fora?"**
> O sistema tem fallback para análise por palavras-chave localmente. A consulta nunca
> é bloqueada — o resultado chega com uma indicação de "modo fallback".

**"Como vocês protegem os dados da paciente?"**
> CPF: hash SHA-256 com HMAC (nunca texto claro). Áudio: deletado do Blob após
> processamento. Todos os dados em `brazilsouth` (Brasil). JWT com 8h de expiração.

**"O médico pode editar o resultado da IA?"**
> Sim. O texto clínico gerado pelo GPT-4o é editável antes do encaminhamento.
> O sistema sugere — a decisão é sempre do profissional de saúde.

**"Como o sistema aprende com o tempo?"**
> Atualmente não há fine-tuning — usa GPT-4o com prompt engineering. Os logs de tokens
> e respostas estão armazenados para eventual retreinamento futuro.
