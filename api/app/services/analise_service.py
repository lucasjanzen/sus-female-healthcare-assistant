import logging
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.schemas.consulta import IndicadorIA, ResultadoIAOut

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
    """Detecta indicadores psicossociais por padrões de palavras-chave.

    negativo_forte e negativo podem ser fornecidos pela análise Azure para maior precisão;
    se None, calculados localmente por contagem de palavras negativas.
    """
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


def _faixa(score: int) -> tuple[str, str]:
    if score <= 25:
        return "VERDE", "Nenhum indicador significativo identificado"
    if score <= 50:
        return "AMARELO", "Indicadores leves - atencao recomendada"
    if score <= 75:
        return "LARANJA", "Indicadores moderados - intervencao recomendada"
    return "VERMELHO", "Indicadores criticos - encaminhamento imediato"


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


def analisar(
    relato_texto: str,
    transcricao: Optional[str] = None,
    id_consulta: Optional[UUID] = None,
) -> ResultadoIAOut:
    from app.services.azure_service import analisar_sentimento_azure

    texto_completo = relato_texto
    origem = "TEXTO_LOCAL"
    if transcricao:
        texto_completo = f"{relato_texto}\n{transcricao}"
        origem = "AMBOS"

    sentimento_azure = analisar_sentimento_azure(texto_completo)

    negativo_forte: Optional[bool] = None
    negativo: Optional[bool] = None
    if sentimento_azure:
        logger.info("Sentimento Azure obtido: %s", sentimento_azure["sentimento"])
        neg_score = sentimento_azure["scores"]["negativo"]
        negativo_forte = neg_score >= 0.7
        negativo = neg_score >= 0.4 or sentimento_azure["sentimento"] in ("negative", "mixed")
    else:
        logger.info("Azure Language indisponivel; usando deteccao local de sentimento.")

    indicadores = _detectar(_normalizar(texto_completo), origem, negativo_forte, negativo)
    score = min(sum(PESOS[i.tipo][i.nivel] for i in indicadores), 100)
    faixa, mensagem = _faixa(score)

    return ResultadoIAOut(
        id_consulta=id_consulta or UUID(int=0),
        score_geral=score,
        faixa_risco=faixa,
        indicadores=indicadores,
        resumo_ia=_resumo(indicadores, faixa, mensagem, sentimento_azure),
        status_audio="CONCLUIDO" if transcricao else "AGUARDANDO",
        confirmado=False,
        calculado_em=datetime.now(timezone.utc),
    )
