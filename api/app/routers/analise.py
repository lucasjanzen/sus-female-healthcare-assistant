from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade, ConsultaRelato, ConsultaResultado
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.analise import (
    AnaliseFilaItem,
    AnaliseFilaTotais,
    AnaliseResultadoOut,
    EncaminharRequest,
)
from app.routers.consulta.helpers import _build_resultado_out

logger = logging.getLogger(__name__)
router = APIRouter()

_FAIXAS_CRITICAS = {"LARANJA", "VERMELHO"}


def _get_indicadores_criticos(resultado: Optional[ConsultaResultado]) -> list[str]:
    if not resultado or not resultado.indicadores:
        return []
    return [
        ind["tipo"]
        for ind in resultado.indicadores
        if ind.get("nivel") == "ALTO"
    ]


@router.get(
    "/fila",
    response_model=list[AnaliseFilaItem],
    response_model_by_alias=True,
)
def listar_fila(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consultas = (
        db.query(ConsultaIdentidade)
        .filter(
            ConsultaIdentidade.status == "ENCERRADA",
            ConsultaIdentidade.analise_concluida_em.isnot(None),
            ConsultaIdentidade.analise_revisada.is_(False),
        )
        .all()
    )

    items: list[AnaliseFilaItem] = []
    for consulta in consultas:
        paciente = db.get(Paciente, consulta.paciente_id)
        resultado = (
            db.query(ConsultaResultado)
            .filter(ConsultaResultado.id_consulta == consulta.id_consulta)
            .first()
        )
        if not resultado:
            continue

        items.append(
            AnaliseFilaItem(
                id_consulta=consulta.id_consulta,
                paciente_nome=paciente.nome if paciente else "—",
                tipo_consulta=consulta.tipo_consulta,
                ig_semanas=consulta.ig_semanas,
                data_consulta=consulta.aberta_em.date(),
                score_geral=resultado.score_geral,
                faixa_risco=resultado.faixa_risco,
                indicadores_criticos=_get_indicadores_criticos(resultado),
                analise_concluida_em=consulta.analise_concluida_em,
                tem_erro=False,
            )
        )

    # Consultas com erro (analise_concluida_em=NULL mas tem analise_erro)
    consultas_erro = (
        db.query(ConsultaIdentidade)
        .filter(
            ConsultaIdentidade.status == "ENCERRADA",
            ConsultaIdentidade.analise_concluida_em.is_(None),
            ConsultaIdentidade.analise_erro.isnot(None),
            ConsultaIdentidade.analise_revisada.is_(False),
        )
        .all()
    )
    for consulta in consultas_erro:
        paciente = db.get(Paciente, consulta.paciente_id)
        items.append(
            AnaliseFilaItem(
                id_consulta=consulta.id_consulta,
                paciente_nome=paciente.nome if paciente else "—",
                tipo_consulta=consulta.tipo_consulta,
                ig_semanas=consulta.ig_semanas,
                data_consulta=consulta.aberta_em.date(),
                score_geral=0,
                faixa_risco="VERDE",
                indicadores_criticos=[],
                analise_concluida_em=consulta.encerrada_em or datetime.now(timezone.utc),
                tem_erro=True,
            )
        )

    # Consultas em processamento (ENCERRADA, sem analise_concluida_em e sem erro)
    consultas_processando = (
        db.query(ConsultaIdentidade)
        .filter(
            ConsultaIdentidade.status == "ENCERRADA",
            ConsultaIdentidade.analise_concluida_em.is_(None),
            ConsultaIdentidade.analise_erro.is_(None),
            ConsultaIdentidade.analise_revisada.is_(False),
        )
        .all()
    )
    for consulta in consultas_processando:
        paciente = db.get(Paciente, consulta.paciente_id)
        items.append(
            AnaliseFilaItem(
                id_consulta=consulta.id_consulta,
                paciente_nome=paciente.nome if paciente else "—",
                tipo_consulta=consulta.tipo_consulta,
                ig_semanas=consulta.ig_semanas,
                data_consulta=consulta.aberta_em.date(),
                score_geral=0,
                faixa_risco="VERDE",
                indicadores_criticos=[],
                analise_concluida_em=None,
                tem_erro=False,
                em_processamento=True,
            )
        )

    faixa_ordem = {"VERMELHO": 0, "LARANJA": 1, "AMARELO": 2, "VERDE": 3}
    items.sort(
        key=lambda x: (
            1 if x.em_processamento else 0,
            faixa_ordem.get(x.faixa_risco, 4),
            x.analise_concluida_em or datetime.now(timezone.utc),
        )
    )
    return items


@router.get(
    "/fila/total",
    response_model=AnaliseFilaTotais,
    response_model_by_alias=True,
)
def totais_fila(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    pendentes = (
        db.query(ConsultaIdentidade)
        .filter(
            ConsultaIdentidade.status == "ENCERRADA",
            ConsultaIdentidade.analise_revisada.is_(False),
            (ConsultaIdentidade.analise_concluida_em.isnot(None))
            | (ConsultaIdentidade.analise_erro.isnot(None)),
        )
        .all()
    )

    total = len(pendentes)
    criticos = 0
    for consulta in pendentes:
        resultado = (
            db.query(ConsultaResultado)
            .filter(ConsultaResultado.id_consulta == consulta.id_consulta)
            .first()
        )
        if resultado and resultado.faixa_risco in _FAIXAS_CRITICAS:
            criticos += 1

    return AnaliseFilaTotais(total=total, criticos=criticos)


@router.get(
    "/historico",
    response_model=list[AnaliseFilaItem],
    response_model_by_alias=True,
)
def listar_historico(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    offset = (page - 1) * page_size
    consultas = (
        db.query(ConsultaIdentidade)
        .filter(
            ConsultaIdentidade.status == "ENCERRADA",
            ConsultaIdentidade.analise_revisada.is_(True),
        )
        .order_by(ConsultaIdentidade.analise_revisada_em.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items: list[AnaliseFilaItem] = []
    for consulta in consultas:
        paciente = db.get(Paciente, consulta.paciente_id)
        resultado = (
            db.query(ConsultaResultado)
            .filter(ConsultaResultado.id_consulta == consulta.id_consulta)
            .first()
        )
        items.append(
            AnaliseFilaItem(
                id_consulta=consulta.id_consulta,
                paciente_nome=paciente.nome if paciente else "—",
                tipo_consulta=consulta.tipo_consulta,
                ig_semanas=consulta.ig_semanas,
                data_consulta=consulta.aberta_em.date(),
                score_geral=resultado.score_geral if resultado else 0,
                faixa_risco=resultado.faixa_risco if resultado else "VERDE",
                indicadores_criticos=_get_indicadores_criticos(resultado),
                analise_concluida_em=consulta.analise_concluida_em or consulta.encerrada_em or datetime.now(timezone.utc),
                tem_erro=bool(consulta.analise_erro and not consulta.analise_concluida_em),
            )
        )
    return items


@router.get(
    "/{id_consulta}/resultado",
    response_model=AnaliseResultadoOut,
    response_model_by_alias=True,
)
def obter_resultado_analise(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = db.get(ConsultaIdentidade, id_consulta)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado de análise não encontrado")

    base = _build_resultado_out(resultado)
    return AnaliseResultadoOut(
        **base.model_dump(),
        analise_revisada=consulta.analise_revisada,
        analise_revisada_em=consulta.analise_revisada_em,
        encaminhado=consulta.encaminhado,
        encaminhado_em=consulta.encaminhado_em,
    )


@router.post("/{id_consulta}/reprocessar", status_code=200)
def reprocessar_analise(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = db.get(ConsultaIdentidade, id_consulta)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    if consulta.status != "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta não está encerrada")
    if consulta.analise_concluida_em is not None:
        raise HTTPException(status_code=409, detail="Análise já concluída")

    consulta.analise_erro = None
    db.commit()

    from app.tasks.analise_task import processar_analise
    processar_analise.delay(str(id_consulta), None, "audio/webm")
    return {"mensagem": "Reprocessamento enfileirado."}


@router.post("/{id_consulta}/revisar", status_code=200)
def revisar_analise(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = db.get(ConsultaIdentidade, id_consulta)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    consulta.analise_revisada = True
    consulta.analise_revisada_em = datetime.now(timezone.utc)
    consulta.analise_revisada_por = current_user.id
    db.commit()
    return {"mensagem": "Análise marcada como revisada."}


@router.post("/{id_consulta}/encaminhar", status_code=200)
def encaminhar_paciente(
    id_consulta: UUID,
    payload: EncaminharRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = db.get(ConsultaIdentidade, id_consulta)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    agora = datetime.now(timezone.utc)
    consulta.encaminhado = True
    consulta.encaminhado_em = agora
    consulta.encaminhado_por = current_user.id
    if payload.observacao is not None:
        consulta.observacao_encaminhamento = payload.observacao

    if not consulta.analise_revisada:
        consulta.analise_revisada = True
        consulta.analise_revisada_em = agora
        consulta.analise_revisada_por = current_user.id

    db.commit()
    return {"mensagem": "Encaminhamento registrado com sucesso."}
