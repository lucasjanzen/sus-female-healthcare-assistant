from typing import Optional
from uuid import UUID

from app.models.consulta_banco_b import ConsultaAudio
from app.models.consulta_clinica import (
    ConsultaExameFisico,
    ConsultaRastreioPsicossocial,
)
from app.models.consulta import ConsultaTriagem
from app.schemas.consulta_clinica import AlertaResultado


def _faixa(score: int) -> str:
    if score <= 30:
        return "VERDE"
    if score <= 50:
        return "AMARELO"
    if score <= 75:
        return "LARANJA"
    return "VERMELHO"


def _sugestao_conduta(faixa: str) -> str:
    mapa = {
        "VERDE": "Manter acompanhamento pré-natal de rotina conforme calendário SUS.",
        "AMARELO": "Intensificar vigilância. Agendar retorno em até 15 dias.",
        "LARANJA": "Acionar equipe multiprofissional. Considerar encaminhamento especializado.",
        "VERMELHO": "Encaminhamento imediato. Acionar protocolo de acolhimento em saúde mental e/ou violência.",
    }
    return mapa.get(faixa, "")


def _resumo_encaminhamento(
    faixa: str,
    score_geral: int,
    alertas: list[AlertaResultado],
) -> Optional[str]:
    if faixa not in ("LARANJA", "VERMELHO"):
        return None
    criticos = [a.descricao for a in alertas if a.nivel == "CRITICO"]
    linhas = [
        f"Score de risco: {score_geral}/100 — Faixa {faixa}.",
    ]
    if criticos:
        linhas.append("Alertas críticos: " + "; ".join(criticos) + ".")
    linhas.append("Recomenda-se encaminhamento para avaliação especializada.")
    return " ".join(linhas)


def calcular_score(
    id_consulta: UUID,
    triagem: Optional[ConsultaTriagem],
    exame: Optional[ConsultaExameFisico],
    rastreio: Optional[ConsultaRastreioPsicossocial],
    audio: Optional[ConsultaAudio],
) -> dict:
    alertas: list[AlertaResultado] = []

    # ── Bloco 1: Score estruturado ────────────────────────────────────────────
    score_estruturado = 0

    if triagem:
        if triagem.pa_sistolica >= 140 or triagem.pa_diastolica >= 90:
            score_estruturado += 20
            alertas.append(AlertaResultado(
                tipo="PA_ELEVADA",
                descricao="Pressão arterial elevada — risco de pré-eclâmpsia.",
                nivel="CRITICO",
                origem="ESTRUTURADO",
            ))
        if triagem.temperatura_c and float(triagem.temperatura_c) >= 37.8:
            score_estruturado += 10
            alertas.append(AlertaResultado(
                tipo="FEBRE",
                descricao="Temperatura acima do normal.",
                nivel="ATENCAO",
                origem="ESTRUTURADO",
            ))
        tags = triagem.queixas_tags or []
        if "SANGRAMENTO" in tags:
            score_estruturado += 10
            alertas.append(AlertaResultado(
                tipo="QUEIXA_SANGRAMENTO",
                descricao="Paciente relata sangramento.",
                nivel="CRITICO",
                origem="ESTRUTURADO",
            ))

    if exame:
        if exame.bcf_bpm is not None and (exame.bcf_bpm < 110 or exame.bcf_bpm > 160):
            score_estruturado += 15
            alertas.append(AlertaResultado(
                tipo="BCF_ALTERADO",
                descricao=f"BCF {exame.bcf_bpm} bpm — fora da faixa normal (110–160).",
                nivel="CRITICO",
                origem="ESTRUTURADO",
            ))
        if exame.edema_grau is not None and exame.edema_grau >= 3:
            score_estruturado += 15
            alertas.append(AlertaResultado(
                tipo="EDEMA_GRAVE",
                descricao="Edema grau 3+ — avaliar pré-eclâmpsia.",
                nivel="CRITICO",
                origem="ESTRUTURADO",
            ))
        if exame.movimentacao_fetal in ("REDUZIDA", "AUSENTE"):
            score_estruturado += 10
            alertas.append(AlertaResultado(
                tipo="MF_REDUZIDA",
                descricao="Movimentação fetal reduzida ou ausente.",
                nivel="CRITICO",
                origem="ESTRUTURADO",
            ))

    if rastreio and rastreio.hits_flag:
        score_estruturado += 20
        alertas.append(AlertaResultado(
            tipo="HITS_POSITIVO",
            descricao="Rastreio HITS positivo — indicativo de violência doméstica.",
            nivel="CRITICO",
            origem="ESTRUTURADO",
        ))

    score_estruturado = min(score_estruturado, 100)

    # ── Bloco 2: Score psicossocial ───────────────────────────────────────────
    score_psicossocial = 0

    if rastreio:
        if rastreio.epds_score >= 12:
            score_psicossocial += 40
            alertas.append(AlertaResultado(
                tipo="EPDS_FLAG",
                descricao=f"EPDS score {rastreio.epds_score} — acima do ponto de corte (≥12).",
                nivel="CRITICO",
                origem="PSICOSSOCIAL",
            ))
        elif rastreio.epds_score >= 8:
            score_psicossocial += 20
            alertas.append(AlertaResultado(
                tipo="EPDS_ATENCAO",
                descricao=f"EPDS score {rastreio.epds_score} — atenção aumentada.",
                nivel="ATENCAO",
                origem="PSICOSSOCIAL",
            ))

        if rastreio.gad7_score >= 10:
            score_psicossocial += 25
            alertas.append(AlertaResultado(
                tipo="GAD7_FLAG",
                descricao=f"GAD-7 score {rastreio.gad7_score} — acima do ponto de corte (≥10).",
                nivel="CRITICO",
                origem="PSICOSSOCIAL",
            ))
        elif rastreio.gad7_score >= 5:
            score_psicossocial += 10
            alertas.append(AlertaResultado(
                tipo="GAD7_ATENCAO",
                descricao=f"GAD-7 score {rastreio.gad7_score} — ansiedade leve.",
                nivel="ATENCAO",
                origem="PSICOSSOCIAL",
            ))

        if rastreio.hits_score >= 11:
            score_psicossocial += 35

        situacao = rastreio.situacao_social or {}
        itens_negativos = sum(1 for v in situacao.values() if not v)
        score_psicossocial += itens_negativos * 5
        if itens_negativos > 0:
            alertas.append(AlertaResultado(
                tipo="SITUACAO_SOCIAL",
                descricao=f"{itens_negativos} fator(es) de vulnerabilidade social identificado(s).",
                nivel="ATENCAO" if itens_negativos < 3 else "CRITICO",
                origem="PSICOSSOCIAL",
            ))

    score_psicossocial = min(score_psicossocial, 100)

    # ── Bloco 3: Score de áudio ───────────────────────────────────────────────
    audio_disponivel = audio is not None and audio.status_processamento == "CONCLUIDO"
    score_audio: Optional[int] = 0 if not audio_disponivel else 0
    status_audio = audio.status_processamento if audio else "INDISPONIVEL"

    if audio_disponivel and audio.transcricao:
        alertas.append(AlertaResultado(
            tipo="AUDIO_CONCLUIDO",
            descricao="Transcrição de áudio disponível para revisão.",
            nivel="INFO",
            origem="AUDIO",
        ))

    # ── Score final ───────────────────────────────────────────────────────────
    if audio_disponivel:
        score_final = (score_estruturado * 0.35) + (score_psicossocial * 0.35) + (score_audio * 0.30)
    else:
        score_final = (score_estruturado * 0.50) + (score_psicossocial * 0.50)

    score_geral = min(int(round(score_final)), 100)
    faixa = _faixa(score_geral)

    alertas.sort(key=lambda a: {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}.get(a.nivel, 3))

    transcricao = audio.transcricao if audio else None

    return {
        "id_consulta": id_consulta,
        "score_geral": score_geral,
        "faixa_risco": faixa,
        "score_psicossocial": score_psicossocial,
        "score_audio": score_audio,
        "score_estruturado": score_estruturado,
        "alertas": [a.model_dump() for a in alertas],
        "resumo_encaminhamento": _resumo_encaminhamento(faixa, score_geral, alertas),
        "sugestao_conduta": _sugestao_conduta(faixa),
        "transcricao": transcricao,
        "status_audio": status_audio,
    }
