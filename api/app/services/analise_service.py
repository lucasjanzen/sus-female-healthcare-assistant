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


def _detectar(texto: str, origem: str) -> list[IndicadorIA]:
    indicadores: list[IndicadorIA] = []
    negativo_forte = _sentimento_negativo_forte(texto)
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


def _resumo(indicadores: list[IndicadorIA], faixa: str, mensagem_faixa: str) -> str:
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

    return f"{mensagem_faixa}.\n\n{achados}\n\n{encaminhamento}\n\n{AVISO_CLINICO}"


def analisar(
    relato_texto: str,
    transcricao: Optional[str] = None,
    id_consulta: Optional[UUID] = None,
) -> ResultadoIAOut:
    logger.info(
        "Azure Text Analytics indisponivel nesta configuracao; usando fallback local."
    )
    texto_completo = relato_texto
    origem = "TEXTO_LOCAL"
    if transcricao:
        texto_completo = f"{relato_texto}\n{transcricao}"
        origem = "AMBOS"

    indicadores = _detectar(_normalizar(texto_completo), origem)
    score = min(sum(PESOS[i.tipo][i.nivel] for i in indicadores), 100)
    faixa, mensagem = _faixa(score)

    return ResultadoIAOut(
        id_consulta=id_consulta or UUID(int=0),
        score_geral=score,
        faixa_risco=faixa,
        indicadores=indicadores,
        resumo_ia=_resumo(indicadores, faixa, mensagem),
        status_audio="CONCLUIDO" if transcricao else "AGUARDANDO",
        confirmado=False,
        calculado_em=datetime.now(timezone.utc),
    )
