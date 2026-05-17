from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade, ConsultaResultado, ConsultaTriagem
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.fila import ConsultaAssumidaOut, ConsultaEmProcessamentoItem, ConsultaFilaItem, ConsultaParaFinalizarItem
from app.schemas.consulta import TriagemResumo

router = APIRouter()


def _triagem_resumo(triagem: ConsultaTriagem) -> TriagemResumo:
    return TriagemResumo(
        peso_kg=float(triagem.peso_kg),
        pa_sistolica=triagem.pa_sistolica,
        pa_diastolica=triagem.pa_diastolica,
    )


def _assumida_out(
    consulta: ConsultaIdentidade, paciente: Paciente, triagem: ConsultaTriagem
) -> ConsultaAssumidaOut:
    return ConsultaAssumidaOut(
        id_consulta=consulta.id_consulta,
        paciente_id=paciente.id,
        paciente_nome=paciente.nome,
        paciente_data_nascimento=paciente.data_nascimento,
        tipo_consulta=consulta.tipo_consulta,
        ig_semanas=consulta.ig_semanas,
        ig_dias=consulta.ig_dias,
        triagem_resumo=_triagem_resumo(triagem),
        assumida_em=consulta.assumida_em,
    )


@router.get(
    "/consultas", response_model=list[ConsultaFilaItem], response_model_by_alias=True
)
def listar_fila(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    linhas = (
        db.query(ConsultaIdentidade, Paciente)
        .join(Paciente, Paciente.id == ConsultaIdentidade.paciente_id)
        .filter(
            ConsultaIdentidade.triagem_concluida.is_(True),
            ConsultaIdentidade.status == "ABERTA",
            ConsultaIdentidade.medico_id.is_(None),
        )
        .order_by(ConsultaIdentidade.triagem_concluida_em.asc())
        .all()
    )
    return [
        ConsultaFilaItem(
            id_consulta=consulta.id_consulta,
            paciente_nome=paciente.nome,
            paciente_data_nascimento=paciente.data_nascimento,
            tipo_consulta=consulta.tipo_consulta,
            ig_semanas=consulta.ig_semanas,
            ig_dias=consulta.ig_dias,
            triagem_concluida_em=consulta.triagem_concluida_em,
        )
        for consulta, paciente in linhas
    ]


@router.get(
    "/consultas/em-andamento",
    response_model=ConsultaAssumidaOut | None,
    response_model_by_alias=True,
)
def consulta_em_andamento(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    linha = (
        db.query(ConsultaIdentidade, Paciente, ConsultaTriagem)
        .join(Paciente, Paciente.id == ConsultaIdentidade.paciente_id)
        .join(
            ConsultaTriagem,
            ConsultaTriagem.id_consulta == ConsultaIdentidade.id_consulta,
        )
        .filter(
            ConsultaIdentidade.medico_id == current_user.id,
            ConsultaIdentidade.status == "EM_ATENDIMENTO",
        )
        .order_by(ConsultaIdentidade.assumida_em.desc())
        .first()
    )
    if not linha:
        return None
    consulta, paciente, triagem = linha
    return _assumida_out(consulta, paciente, triagem)


@router.get(
    "/consultas/para-finalizar",
    response_model=list[ConsultaParaFinalizarItem],
    response_model_by_alias=True,
)
def listar_para_finalizar(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    """Consultas do médico com análise concluída (EM_ATENDIMENTO + resultado não confirmado)."""
    linhas = (
        db.query(ConsultaIdentidade, Paciente, ConsultaResultado)
        .join(Paciente, Paciente.id == ConsultaIdentidade.paciente_id)
        .join(
            ConsultaResultado,
            ConsultaResultado.id_consulta == ConsultaIdentidade.id_consulta,
        )
        .filter(
            ConsultaIdentidade.medico_id == current_user.id,
            ConsultaIdentidade.status == "EM_ATENDIMENTO",
            ConsultaResultado.confirmado.is_(False),
        )
        .order_by(ConsultaResultado.calculado_em.desc())
        .all()
    )
    return [
        ConsultaParaFinalizarItem(
            id_consulta=consulta.id_consulta,
            paciente_nome=paciente.nome,
            paciente_data_nascimento=paciente.data_nascimento,
            tipo_consulta=consulta.tipo_consulta,
            ig_semanas=consulta.ig_semanas,
            ig_dias=consulta.ig_dias,
            score_risco=resultado.score_geral,
            faixa_risco=resultado.faixa_risco,
            concluida_em=resultado.calculado_em,
        )
        for consulta, paciente, resultado in linhas
    ]


@router.get(
    "/consultas/em-processamento",
    response_model=list[ConsultaEmProcessamentoItem],
    response_model_by_alias=True,
)
def listar_em_processamento(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    """Consultas do médico com áudio enviado e análise em andamento (AGUARDANDO_ANALISE)."""
    linhas = (
        db.query(ConsultaIdentidade, Paciente)
        .join(Paciente, Paciente.id == ConsultaIdentidade.paciente_id)
        .filter(
            ConsultaIdentidade.medico_id == current_user.id,
            ConsultaIdentidade.status == "AGUARDANDO_ANALISE",
        )
        .order_by(ConsultaIdentidade.assumida_em.desc())
        .all()
    )
    return [
        ConsultaEmProcessamentoItem(
            id_consulta=consulta.id_consulta,
            paciente_nome=paciente.nome,
            paciente_data_nascimento=paciente.data_nascimento,
            tipo_consulta=consulta.tipo_consulta,
            ig_semanas=consulta.ig_semanas,
            ig_dias=consulta.ig_dias,
            enviada_em=consulta.assumida_em,
        )
        for consulta, paciente in linhas
    ]


@router.post(
    "/consultas/{id_consulta}/assumir",
    response_model=ConsultaAssumidaOut,
    response_model_by_alias=True,
)
def assumir_consulta(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    linha = (
        db.query(ConsultaIdentidade, Paciente, ConsultaTriagem)
        .join(Paciente, Paciente.id == ConsultaIdentidade.paciente_id)
        .join(
            ConsultaTriagem,
            ConsultaTriagem.id_consulta == ConsultaIdentidade.id_consulta,
        )
        .filter(ConsultaIdentidade.id_consulta == id_consulta)
        .first()
    )
    if not linha:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    consulta, paciente, triagem = linha
    if consulta.medico_id and consulta.medico_id != current_user.id:
        raise HTTPException(
            status_code=409, detail="Consulta assumida por outro médico"
        )

    consulta.medico_id = current_user.id
    consulta.assumida_em = consulta.assumida_em or datetime.now(timezone.utc)
    consulta.status = "EM_ATENDIMENTO"
    db.commit()
    db.refresh(consulta)
    return _assumida_out(consulta, paciente, triagem)
