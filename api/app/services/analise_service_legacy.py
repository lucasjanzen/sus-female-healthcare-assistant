"""
Análise de risco por palavras-chave — fallback local quando o LLM está indisponível.
"""
import re
from typing import Optional

from app.schemas.consulta import IndicadorIA

PADROES = {
    "DEPRESSAO": [
        "tristeza", "choro", "sem esperanca", "nao quero mais", "cansada",
        "nao consigo", "solidao", "vazio", "sem vontade",
    ],
    "ANSIEDADE": [
        "medo", "preocupada", "nervosa", "nao consigo dormir", "tensao",
        "agitada", "coracao acelerado", "sufocando",
    ],
    "VIOLENCIA_DOMESTICA": [
        "briga", "machucou", "bateu", "ameaca", "com medo dele",
        "nao posso sair", "ele nao deixa", "ciume excessivo",
    ],
    "ISOLAMENTO_SOCIAL": [
        "sozinha", "ninguem me ajuda", "sem apoio", "familia distante",
        "marido nao ajuda", "sem amigos",
    ],
}

PESOS = {
    "DEPRESSAO": {"ALTO": 40, "MODERADO": 20, "BAIXO": 10},
    "ANSIEDADE": {"ALTO": 30, "MODERADO": 15, "BAIXO": 5},
    "VIOLENCIA_DOMESTICA": {"ALTO": 40, "MODERADO": 20, "BAIXO": 10},
    "ISOLAMENTO_SOCIAL": {"ALTO": 20, "MODERADO": 10, "BAIXO": 5},
}

_AVISO = (
    "Este resultado e um apoio a decisao clinica. "
    "A conduta final e responsabilidade do profissional de saude."
)


def _normalizar(texto: str) -> str:
    mapa = str.maketrans("áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ", "aaaaeeiooouucAAAAEEIOOOUUC")
    return texto.translate(mapa).lower()


def _negativo_forte(texto: str) -> bool:
    return sum(
        1 for p in ["nao", "medo", "triste", "choro", "ameaca", "vazio"] if p in texto
    ) >= 2


def analisar_texto(texto: str) -> tuple[int, list[IndicadorIA], str]:
    """
    Analisa o texto por palavras-chave e retorna (score, indicadores, resumo).
    """
    texto_norm = _normalizar(texto)
    forte = _negativo_forte(texto_norm)
    negativo = forte or any(
        p in texto_norm for p in ["triste", "medo", "preocupada", "nervosa"]
    )

    indicadores: list[IndicadorIA] = []
    for tipo, padroes in PADROES.items():
        encontrados = [p for p in padroes if re.search(rf"\b{re.escape(p)}\b", texto_norm)]
        if not encontrados:
            continue
        if tipo == "VIOLENCIA_DOMESTICA":
            nivel = "ALTO"
        elif forte and len(encontrados) >= 2:
            nivel = "ALTO"
        elif negativo and len(encontrados) >= 1:
            nivel = "MODERADO"
        else:
            nivel = "BAIXO"
        indicadores.append(IndicadorIA(
            tipo=tipo,
            nivel=nivel,
            descricao=(
                f"Sinais relacionados a {tipo.replace('_', ' ').lower()}: "
                f"{', '.join(encontrados)}."
            ),
            origem="TEXTO_LOCAL",
        ))

    score = min(sum(PESOS[i.tipo][i.nivel] for i in indicadores), 100)

    if not indicadores:
        achados = "Nenhum indicador psicossocial significativo identificado."
    else:
        linhas = [
            f"- {i.tipo.replace('_', ' ').title()}: nivel {i.nivel}. {i.descricao}"
            for i in indicadores
        ]
        achados = "Indicadores encontrados:\n" + "\n".join(linhas)

    faixa_map = {
        (0, 25): "Nenhum indicador significativo.",
        (26, 50): "Indicadores leves — atenção recomendada.",
        (51, 75): "Indicadores moderados — intervenção recomendada.",
        (76, 100): "Indicadores críticos — encaminhamento imediato.",
    }
    mensagem = next(v for (lo, hi), v in faixa_map.items() if lo <= score <= hi)
    resumo = f"{mensagem}\n\n{achados}\n\n{_AVISO}"
    return score, indicadores, resumo
