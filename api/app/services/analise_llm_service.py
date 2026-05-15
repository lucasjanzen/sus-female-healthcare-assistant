"""
Pipeline de análise clínica com Azure OpenAI GPT-4o.
Chamado pelo atendimento.py após o processamento de áudio pelo azure_service.
"""
import json
import logging
from uuid import UUID

import openai
from openai import AzureOpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import analise_service_legacy as legacy

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# COLETA DE CONTEXTO
# -------------------------------------------------------

def coletar_contexto(
    id_consulta: UUID,
    db: Session,
    transcricao: str = "",
    sentimento_voz: dict = None,
) -> dict:
    """Coleta todas as fontes de dados clínicos para enviar ao GPT-4o."""
    fontes = {
        "relato": False,
        "transcricao": False,
        "sentimento_voz": False,
        "dados_consulta": False,
        "historico": False,
    }

    # Relato digitado pelo médico
    relato = db.execute(
        text("SELECT relato_texto FROM consulta_relato WHERE id_consulta = :id"),
        {"id": id_consulta},
    ).fetchone()
    relato_texto = relato.relato_texto if relato and relato.relato_texto else ""
    if relato_texto:
        fontes["relato"] = True

    if transcricao:
        fontes["transcricao"] = True
    if sentimento_voz:
        fontes["sentimento_voz"] = True

    # Dados da consulta atual
    consulta = db.execute(
        text(
            """SELECT ci.tipo_consulta, ci.ig_semanas, ci.ig_dias, ci.aberta_em,
                      ci.paciente_id,
                      ct.peso_kg, ct.pa_sistolica, ct.pa_diastolica
               FROM consultas_identidade ci
               LEFT JOIN consulta_triagem ct ON ct.id_consulta = ci.id_consulta
               WHERE ci.id_consulta = :id"""
        ),
        {"id": id_consulta},
    ).fetchone()

    dados_consulta: dict = {}
    paciente_id = None
    if consulta:
        dados_consulta = {
            "tipo_consulta": consulta.tipo_consulta,
            "ig_semanas": consulta.ig_semanas,
            "ig_dias": consulta.ig_dias,
            "data_consulta": str(consulta.aberta_em.date()) if consulta.aberta_em else "",
            "peso_kg": float(consulta.peso_kg) if consulta.peso_kg else None,
            "pa_sistolica": consulta.pa_sistolica,
            "pa_diastolica": consulta.pa_diastolica,
        }
        fontes["dados_consulta"] = True
        paciente_id = consulta.paciente_id

    # Histórico da paciente (últimas 5 consultas encerradas)
    historico_consultas: list = []
    historico_peso: list = []

    if paciente_id:
        consultas_anteriores = db.execute(
            text(
                """SELECT ci.aberta_em, cr.faixa_risco, cr.resumo_ia
                   FROM consultas_identidade ci
                   JOIN consulta_resultado cr ON cr.id_consulta = ci.id_consulta
                   WHERE ci.paciente_id = :pid
                     AND ci.status = 'ENCERRADA'
                     AND ci.id_consulta != :id_atual
                   ORDER BY ci.aberta_em DESC
                   LIMIT 5"""
            ),
            {"pid": paciente_id, "id_atual": id_consulta},
        ).fetchall()

        historico_consultas = [
            {
                "data": str(r.aberta_em.date()),
                "faixa_risco": r.faixa_risco,
                "resumo": (r.resumo_ia or "")[:200],
            }
            for r in consultas_anteriores
        ]

        pesos = db.execute(
            text(
                """SELECT peso_kg, registrado_em
                   FROM historico_peso
                   WHERE paciente_id = :pid
                   ORDER BY registrado_em DESC
                   LIMIT 10"""
            ),
            {"pid": paciente_id},
        ).fetchall()

        historico_peso = [
            {"data": str(p.registrado_em.date()), "peso_kg": float(p.peso_kg)}
            for p in pesos
        ]

        if historico_consultas or historico_peso:
            fontes["historico"] = True

    return {
        "relato_texto": relato_texto,
        "transcricao": transcricao,
        "sentimento_voz": sentimento_voz,
        "dados_consulta": dados_consulta,
        "historico_consultas": historico_consultas,
        "historico_peso": historico_peso,
        "fontes_utilizadas": fontes,
    }


# -------------------------------------------------------
# MONTAGEM DO PROMPT
# -------------------------------------------------------

SYSTEM_PROMPT = """Você é um assistente clínico especializado em saúde mental da mulher,
com foco em depressão perinatal, ansiedade gestacional e violência doméstica.
Sua função é analisar os dados de uma consulta de saúde feminina e gerar
um relatório de apoio à decisão clínica para o médico responsável.

Você NÃO faz diagnósticos. Você identifica indicadores de risco com base
nas evidências fornecidas e sugere condutas para avaliação do profissional.

Responda EXCLUSIVAMENTE em JSON válido, sem texto fora do JSON,
sem blocos de código markdown, seguindo exatamente o schema fornecido."""

SCHEMA_RESPOSTA = {
    "indicadores": [
        {
            "tipo": "DEPRESSAO | ANSIEDADE | VIOLENCIA_DOMESTICA | ISOLAMENTO_SOCIAL | OUTRO",
            "nivel": "BAIXO | MODERADO | ALTO",
            "evidencias": ["trecho ou observação que sustenta o indicador"],
            "recomendacao": "sugestão de conduta para este indicador",
        }
    ],
    "score_geral": "inteiro de 0 a 100",
    "faixa_risco": "VERDE | AMARELO | LARANJA | VERMELHO",
    "pontos_atencao": ["observações que merecem atenção mas não se encaixam nos indicadores"],
    "encaminhamentos_sugeridos": [
        "CAPS | CVR | ASSISTENCIA_SOCIAL | PSICOLOGIA | SERVICO_SOCIAL | DELEGACIA_MULHER | PRE_NATAL_ALTO_RISCO"
    ],
    "contexto_historico": "resumo do histórico relevante considerado na análise",
    "texto_clinico": (
        "parágrafo em linguagem clínica, terceira pessoa, máximo 300 palavras, "
        "para o médico usar como base no encaminhamento"
    ),
}


def montar_prompt(ctx: dict) -> str:
    partes: list[str] = []

    d = ctx["dados_consulta"]
    partes.append("## DADOS DA CONSULTA ATUAL")
    partes.append(f"Tipo: {d.get('tipo_consulta', 'não informado')}")
    if d.get("ig_semanas") is not None:
        partes.append(
            f"Idade gestacional: {d['ig_semanas']} semanas e {d.get('ig_dias', 0)} dias"
        )
    if d.get("peso_kg"):
        partes.append(f"Peso: {d['peso_kg']} kg")
    if d.get("pa_sistolica"):
        partes.append(f"Pressão arterial: {d['pa_sistolica']}/{d['pa_diastolica']} mmHg")
    partes.append(f"Data: {d.get('data_consulta', 'não informada')}")

    if ctx["relato_texto"]:
        partes.append("\n## OBSERVAÇÕES DO PROFISSIONAL")
        partes.append(ctx["relato_texto"])

    if ctx["transcricao"]:
        partes.append("\n## TRANSCRIÇÃO DO ÁUDIO DA CONSULTA")
        partes.append(ctx["transcricao"])

    sv = ctx.get("sentimento_voz")
    if sv:
        partes.append("\n## ANÁLISE VOCAL DA PACIENTE (diarização por falante)")
        partes.append(f"Tom predominante detectado: {sv.get('dominante', 'não disponível')}")
        scores = sv.get("scores", {})
        if scores:
            partes.append(
                f"Scores: positivo={scores.get('positivo', 0):.0%}, "
                f"negativo={scores.get('negativo', 0):.0%}, "
                f"neutro={scores.get('neutro', 0):.0%}"
            )
        partes.append(
            "Nota: análise baseada exclusivamente nos trechos da paciente (diarização ativa)."
        )

    if ctx["historico_consultas"]:
        n = len(ctx["historico_consultas"])
        partes.append(f"\n## HISTÓRICO DE CONSULTAS ANTERIORES ({n} registros)")
        for h in ctx["historico_consultas"]:
            partes.append(f"- {h['data']} | Risco: {h['faixa_risco']} | {h['resumo']}")

    if ctx["historico_peso"]:
        partes.append("\n## EVOLUÇÃO DE PESO (mais recentes primeiro)")
        for p in ctx["historico_peso"]:
            partes.append(f"- {p['data']}: {p['peso_kg']} kg")

    partes.append("\n## SCHEMA DE RESPOSTA ESPERADO")
    partes.append(json.dumps(SCHEMA_RESPOSTA, ensure_ascii=False, indent=2))

    return "\n".join(partes)


# -------------------------------------------------------
# CHAMADA AO GPT-4o
# -------------------------------------------------------

def chamar_gpt4o(prompt_usuario: str) -> tuple[dict, int]:
    """Chama o Azure OpenAI GPT-4o e retorna (resposta_json, tokens_utilizados)."""
    endpoint = settings.azure_openai_endpoint
    if "/v1" in endpoint:
        # Endpoint OpenAI-compatível: não aceita ?api-version
        client = openai.OpenAI(
            base_url=endpoint,
            api_key=settings.azure_openai_api_key,
        )
    else:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_usuario},
        ],
        temperature=0.3,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    tokens = response.usage.total_tokens if response.usage else 0
    conteudo = response.choices[0].message.content
    try:
        return json.loads(conteudo), tokens
    except json.JSONDecodeError as exc:
        raise ValueError(f"GPT-4o retornou JSON inválido: {exc}. Conteúdo: {conteudo[:200]!r}") from exc


# -------------------------------------------------------
# FUNÇÃO PRINCIPAL
# -------------------------------------------------------

def analisar_com_llm(
    id_consulta: UUID,
    db: Session,
    transcricao: str = "",
    sentimento_voz: dict = None,
) -> dict:
    """
    Executa o pipeline completo de análise com LLM.

    Retorna dict com:
        sumario_estruturado, texto_clinico, fontes_utilizadas,
        tokens_utilizados, score_geral, faixa_risco, indicadores, resumo_ia
    """
    ctx = coletar_contexto(id_consulta, db, transcricao, sentimento_voz)
    prompt = montar_prompt(ctx)

    try:
        resposta, tokens = chamar_gpt4o(prompt)

        sumario = {
            "indicadores": resposta.get("indicadores", []),
            "score_geral": int(resposta.get("score_geral", 0)),
            "faixa_risco": resposta.get("faixa_risco", "VERDE"),
            "pontos_atencao": resposta.get("pontos_atencao", []),
            "encaminhamentos_sugeridos": resposta.get("encaminhamentos_sugeridos", []),
            "contexto_historico": resposta.get("contexto_historico", ""),
            "modo_fallback": False,
        }

        return {
            "sumario_estruturado": sumario,
            "texto_clinico": resposta.get("texto_clinico", ""),
            "fontes_utilizadas": ctx["fontes_utilizadas"],
            "tokens_utilizados": tokens,
            "score_geral": sumario["score_geral"],
            "faixa_risco": sumario["faixa_risco"],
            "indicadores": sumario["indicadores"],
            "resumo_ia": resposta.get("texto_clinico", ""),
        }

    except (openai.OpenAIError, ValueError, json.JSONDecodeError) as e:
        logger.error("Azure OpenAI indisponível — usando fallback local. Erro: %s", e)
        return _fallback_local(ctx)


def _fallback_local(ctx: dict) -> dict:
    """Fallback baseado em palavras-chave quando o GPT-4o está indisponível."""
    texto = f"{ctx['relato_texto']} {ctx['transcricao']}".strip()
    from app.services.analise_service import calcular_faixa

    score, indicadores, resumo = legacy.analisar_texto(texto)
    faixa = calcular_faixa(score)

    sumario = {
        "indicadores": [i.model_dump() for i in indicadores],
        "score_geral": score,
        "faixa_risco": faixa,
        "pontos_atencao": [],
        "encaminhamentos_sugeridos": [],
        "contexto_historico": "",
        "modo_fallback": True,
    }

    return {
        "sumario_estruturado": sumario,
        "texto_clinico": resumo,
        "fontes_utilizadas": ctx["fontes_utilizadas"],
        "tokens_utilizados": 0,
        "score_geral": score,
        "faixa_risco": faixa,
        "indicadores": sumario["indicadores"],
        "resumo_ia": resumo,
    }


