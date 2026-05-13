import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.schemas.consulta import IndicadorIA, ResultadoIAOut, SentimentoVozOut

logger = logging.getLogger(__name__)

AVISO_CLINICO = (
    "Este resultado e um apoio a decisao clinica. "
    "A conduta final e responsabilidade do profissional de saude."
)

PADROES = {
    "DEPRESSAO": [
        "tristeza",
        "choro",
        "sem esperanca",
        "nao quero mais",
        "cansada",
        "nao consigo",
        "solidao",
        "vazio",
        "sem vontade",
    ],
    "ANSIEDADE": [
        "medo",
        "preocupada",
        "nervosa",
        "nao consigo dormir",
        "tensao",
        "agitada",
        "coracao acelerado",
        "sufocando",
    ],
    "VIOLENCIA_DOMESTICA": [
        "briga",
        "machucou",
        "bateu",
        "ameaca",
        "com medo dele",
        "nao posso sair",
        "ele nao deixa",
        "ciume excessivo",
    ],
    "ISOLAMENTO_SOCIAL": [
        "sozinha",
        "ninguem me ajuda",
        "sem apoio",
        "familia distante",
        "marido nao ajuda",
        "sem amigos",
    ],
}

PESOS = {
    "DEPRESSAO": {"ALTO": 40, "MODERADO": 20, "BAIXO": 10},
    "ANSIEDADE": {"ALTO": 30, "MODERADO": 15, "BAIXO": 5},
    "VIOLENCIA_DOMESTICA": {"ALTO": 40, "MODERADO": 20, "BAIXO": 10},
    "ISOLAMENTO_SOCIAL": {"ALTO": 20, "MODERADO": 10, "BAIXO": 5},
}


def _normalizar(texto: str) -> str:
    mapa = str.maketrans("áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ", "aaaaeeiooouucAAAAEEIOOOUUC")
    return texto.translate(mapa).lower()


def _sentimento_negativo_forte(texto: str) -> bool:
    negativos = sum(
        1
        for palavra in ["nao", "medo", "triste", "choro", "ameaca", "vazio"]
        if palavra in texto
    )
    return negativos >= 2


def _detectar(
    texto: str,
    origem: str,
    negativo_forte: Optional[bool] = None,
    negativo: Optional[bool] = None,
) -> list[IndicadorIA]:
    indicadores: list[IndicadorIA] = []

    if negativo_forte is None:
        negativo_forte = _sentimento_negativo_forte(texto)
    if negativo is None:
        negativo = negativo_forte or any(
            p in texto for p in ["triste", "medo", "preocupada", "nervosa"]
        )

    for tipo, padroes in PADROES.items():
        encontrados = [p for p in padroes if re.search(rf"\b{re.escape(p)}\b", texto)]
        if not encontrados:
            continue

        if tipo == "VIOLENCIA_DOMESTICA":
            nivel = "ALTO"
        elif negativo_forte and len(encontrados) >= 2:
            nivel = "ALTO"
        elif negativo and len(encontrados) >= 1:
            nivel = "MODERADO"
        else:
            nivel = "BAIXO"

        descricao = f"Foram identificados sinais relacionados a {tipo.replace('_', ' ').lower()}: {', '.join(encontrados)}."
        indicadores.append(
            IndicadorIA(tipo=tipo, nivel=nivel, descricao=descricao, origem=origem)
        )

    return indicadores


def calcular_faixa(score: int) -> str:
    if score <= 25:
        return "VERDE"
    if score <= 50:
        return "AMARELO"
    if score <= 75:
        return "LARANJA"
    return "VERMELHO"


def _faixa(score: int) -> tuple[str, str]:
    mensagens = {
        "VERDE": "Nenhum indicador significativo identificado",
        "AMARELO": "Indicadores leves - atencao recomendada",
        "LARANJA": "Indicadores moderados - intervencao recomendada",
        "VERMELHO": "Indicadores criticos - encaminhamento imediato",
    }
    faixa = calcular_faixa(score)
    return faixa, mensagens[faixa]


def _resumo(
    indicadores: list[IndicadorIA],
    faixa: str,
    mensagem_faixa: str,
    sentimento_azure: Optional[dict] = None,
) -> str:
    if not indicadores:
        achados = "Nenhum indicador psicossocial significativo foi identificado no relato informado."
    else:
        linhas = [
            f"- {i.tipo.replace('_', ' ').title()}: nivel {i.nivel}. {i.descricao}"
            for i in indicadores
        ]
        achados = "Indicadores encontrados:\n" + "\n".join(linhas)

    encaminhamento = {
        "VERDE": "Manter acompanhamento clinico habitual e reavaliar se surgirem novos sinais.",
        "AMARELO": "Recomenda-se atencao ampliada, acolhimento e reavaliacao em consulta subsequente.",
        "LARANJA": "Recomenda-se intervencao, escuta qualificada e avaliacao de encaminhamento multiprofissional.",
        "VERMELHO": "Recomenda-se encaminhamento imediato conforme protocolo local e avaliacao de seguranca.",
    }[faixa]

    texto = f"{mensagem_faixa}.\n\n{achados}\n\n{encaminhamento}\n\n{AVISO_CLINICO}"

    if sentimento_azure:
        sent = sentimento_azure["sentimento"]
        neg_pct = sentimento_azure["scores"]["negativo"]
        texto += f"\n\nAnalise de sentimento (Azure AI Language): {sent} — negativo: {neg_pct:.0%}."

    return texto


def _calcular_voice_modifier(sentimento_voz: Optional[dict]) -> int:
    """Modificador de score ponderado por número de trechos do paciente."""
    if not sentimento_voz:
        return 0
    trechos = sentimento_voz.get("_por_trecho_interno", [])
    n = len(trechos)
    if n == 0:
        return 0
    confianca = min(n / 5.0, 1.0)
    negativo = sentimento_voz["scores"]["negativo"]
    if negativo > 0.8:
        modificador_bruto = 15
    elif negativo > 0.6:
        modificador_bruto = 10
    else:
        modificador_bruto = 0
    return round(modificador_bruto * confianca)


async def analisar(
    relato_texto: str = "",
    id_consulta: Optional[UUID] = None,
    audio_bytes: Optional[bytes] = None,
    audio_content_type: str = "audio/webm",
) -> ResultadoIAOut:
    from app.services.azure_service import analisar_sentimento_azure, transcrever_e_analisar_voz

    sentimento_voz: Optional[dict] = None
    transcricao_audio: Optional[str] = None

    if audio_bytes:
        resultado_voz = await asyncio.to_thread(
            transcrever_e_analisar_voz, audio_bytes, audio_content_type
        )
        if resultado_voz["transcricao"]:
            transcricao_audio = resultado_voz["transcricao"]
        sentimento_voz = resultado_voz["sentimento_voz"]

    texto_para_analise = transcricao_audio or relato_texto
    sentimento_azure = analisar_sentimento_azure(texto_para_analise) if texto_para_analise else None

    negativo_forte: Optional[bool] = None
    negativo: Optional[bool] = None
    if sentimento_azure:
        logger.info("Sentimento Azure obtido: %s", sentimento_azure["sentimento"])
        neg_score = sentimento_azure["scores"]["negativo"]
        negativo_forte = neg_score >= 0.7
        negativo = neg_score >= 0.4 or sentimento_azure["sentimento"] in ("negative", "mixed")
    else:
        logger.warning("Azure Language indisponivel; usando deteccao local de sentimento.")

    indicadores = _detectar(_normalizar(texto_para_analise), "TEXTO_LOCAL", negativo_forte, negativo)

    if sentimento_voz and sentimento_voz["scores"]["negativo"] > 0.65:
        ja_tem_depressao = any(i.tipo == "DEPRESSAO" for i in indicadores)
        if not ja_tem_depressao:
            indicadores.append(IndicadorIA(
                tipo="DEPRESSAO",
                nivel="BAIXO",
                descricao="Tom de voz negativo detectado pelo sistema de analise vocal",
                origem="VOZ",
            ))

    score = min(sum(PESOS[i.tipo][i.nivel] for i in indicadores), 100)
    score = min(score + _calcular_voice_modifier(sentimento_voz), 100)
    faixa, mensagem = _faixa(score)

    resumo = _resumo(indicadores, faixa, mensagem, sentimento_azure)
    if sentimento_voz:
        resumo += (
            f"\n\nAnalise vocal: tom predominantemente {sentimento_voz['dominante'].lower()} "
            f"detectado nos trechos do paciente "
            f"(negativo: {sentimento_voz['scores']['negativo']:.0%})."
        )

    sentimento_voz_out: Optional[SentimentoVozOut] = None
    if sentimento_voz:
        sentimento_voz_out = SentimentoVozOut(
            dominante=sentimento_voz["dominante"],
            scores=sentimento_voz["scores"],
        )

    return ResultadoIAOut(
        id_consulta=id_consulta,
        score_geral=score,
        faixa_risco=faixa,
        indicadores=indicadores,
        resumo_ia=resumo,
        confirmado=False,
        calculado_em=datetime.now(timezone.utc),
        sentimento_voz=sentimento_voz_out,
        transcricao=transcricao_audio,
    )
