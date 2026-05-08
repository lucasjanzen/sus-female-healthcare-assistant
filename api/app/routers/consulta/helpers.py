import hashlib
from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.consulta import (
    ConsultaIdentidade,
    ConsultaRelato,
    ConsultaResultado,
    ConsultaTriagem,
)
from app.schemas.consulta import Etapa1Out, RelatoOut, ResultadoIAOut, SentimentoVozOut, TriagemResumo


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


def _calcular_ig(dum: date | None) -> tuple[int | None, int | None]:
    if not dum:
        return None, None
    dias = max((date.today() - dum).days, 0)
    return dias // 7, dias % 7


def _consulta_ou_404(id_consulta: UUID, db: Session) -> ConsultaIdentidade:
    consulta = (
        db.query(ConsultaIdentidade)
        .filter(ConsultaIdentidade.id_consulta == id_consulta)
        .first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta nao encontrada")
    return consulta


def _triagem_resumo(triagem: ConsultaTriagem | None) -> TriagemResumo | None:
    if not triagem:
        return None
    return TriagemResumo(
        peso_kg=float(triagem.peso_kg),
        pa_sistolica=triagem.pa_sistolica,
        pa_diastolica=triagem.pa_diastolica,
    )


def _build_etapa1_out(consulta: ConsultaIdentidade, db: Session) -> Etapa1Out:
    triagem = (
        db.query(ConsultaTriagem)
        .filter(ConsultaTriagem.id_consulta == consulta.id_consulta)
        .first()
    )
    return Etapa1Out(
        id_consulta=consulta.id_consulta,
        paciente_id=consulta.paciente_id,
        tipo_consulta=consulta.tipo_consulta,
        status=consulta.status,
        dum=consulta.dum,
        ig_semanas=consulta.ig_semanas,
        ig_dias=consulta.ig_dias,
        triagem_concluida=consulta.triagem_concluida,
        triagem=_triagem_resumo(triagem),
        aberta_em=consulta.aberta_em,
        triagem_concluida_em=consulta.triagem_concluida_em,
    )


def _build_relato_out(relato: ConsultaRelato) -> RelatoOut:
    return RelatoOut(
        id_consulta=relato.id_consulta,
        relato_texto=relato.relato_texto,
        parecer_medico=relato.parecer_medico,
        registrado_em=relato.registrado_em,
        atualizado_em=relato.atualizado_em,
    )


def _build_resultado_out(resultado: ConsultaResultado) -> ResultadoIAOut:
    sentimento_voz_out: SentimentoVozOut | None = None
    if resultado.sentimento_voz:
        sv = resultado.sentimento_voz
        sentimento_voz_out = SentimentoVozOut(
            dominante=sv["dominante"],
            scores=sv["scores"],
        )
    return ResultadoIAOut(
        id_consulta=resultado.id_consulta,
        score_geral=resultado.score_geral,
        faixa_risco=resultado.faixa_risco,
        indicadores=resultado.indicadores,
        resumo_ia=resultado.resumo_ia or "",
        status_audio="CONCLUIDO" if resultado.sentimento_voz is not None else "NAO_PROCESSADO",
        confirmado=resultado.confirmado,
        calculado_em=resultado.calculado_em,
        sentimento_voz=sentimento_voz_out,
    )
