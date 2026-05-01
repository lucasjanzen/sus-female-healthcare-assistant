import io
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade, ConsultaTriagem
from app.models.consulta_banco_b import ConsultaResultado
from app.models.consulta_encerramento import ConsultaEncerramento
from app.models.user import User
from app.schemas.encerramento import EncerramentoCreate, EncerramentoOut, ResumoPecOut
from app.services.encerramento_service import calcular_data_sugerida

router = APIRouter()


_COR_FAIXA = {
    "VERDE": (0.18, 0.65, 0.33),
    "AMARELO": (0.85, 0.65, 0.0),
    "LARANJA": (0.9, 0.45, 0.0),
    "VERMELHO": (0.8, 0.15, 0.15),
}


def _get_consulta_or_404(id_consulta: UUID, db: Session) -> ConsultaIdentidade:
    c = db.query(ConsultaIdentidade).filter(ConsultaIdentidade.id_consulta == id_consulta).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return c


def _gerar_pdf(resumo: ResumoPecOut) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=14, spaceAfter=4)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#666666"), spaceAfter=12)
    section_style = ParagraphStyle("section", parent=styles["Heading2"], fontSize=11, spaceBefore=12, spaceAfter=4)
    body_style = styles["Normal"]
    body_style.fontSize = 10

    r, g, b = _COR_FAIXA.get(resumo.faixa_risco or "VERDE", (0.5, 0.5, 0.5))
    faixa_color = colors.Color(r, g, b)
    elements = []

    elements.append(Paragraph("CASF — Centro de Assistência à Saúde Feminina", title_style))
    elements.append(Paragraph(
        f"Resumo para e-SUS PEC · Consulta: {resumo.tipo_consulta} · "
        f"Data: {resumo.data_consulta.strftime('%d/%m/%Y')} · "
        f"Gerado em: {resumo.gerado_em.strftime('%d/%m/%Y %H:%M')}",
        subtitle_style,
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC")))
    elements.append(Spacer(1, 0.3*cm))

    elements.append(Paragraph("Dados Clínicos", section_style))
    ig_str = f"{resumo.ig_semanas}s" if resumo.ig_semanas is not None else "—"
    dados = [
        ["Tipo de Consulta", resumo.tipo_consulta, "IG", ig_str],
        ["Peso", f"{resumo.peso_kg} kg" if resumo.peso_kg else "—", "Pressão Arterial", resumo.pa or "—"],
    ]
    t = Table(dados, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F8F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)

    if resumo.score_risco is not None:
        elements.append(Paragraph("Análise de Risco", section_style))
        score_data = [["Score Geral", "Faixa de Risco"], [str(resumo.score_risco), resumo.faixa_risco or "—"]]
        ts = Table(score_data, colWidths=[8.5*cm, 8.5*cm])
        ts.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
            ("TEXTCOLOR", (1, 1), (1, 1), faixa_color),
            ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(ts)

    elements.append(Paragraph("Conduta", section_style))
    elements.append(Paragraph(resumo.conduta, body_style))

    if resumo.encaminhamentos:
        elements.append(Paragraph("Encaminhamentos", section_style))
        for enc in resumo.encaminhamentos:
            elements.append(Paragraph(f"• {enc}", body_style))

    elements.append(Paragraph("Próximo Retorno", section_style))
    elements.append(Paragraph(resumo.data_proximo_retorno.strftime("%d/%m/%Y"), body_style))

    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    elements.append(Paragraph(
        "Documento gerado automaticamente pelo sistema CASF. Não substitui o prontuário oficial.",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#999999"), spaceBefore=4),
    ))
    doc.build(elements)
    return buf.getvalue()


@router.post(
    "/{id_consulta}/encerrar",
    response_model=EncerramentoOut,
    status_code=201,
    response_model_by_alias=True,
)
def encerrar_consulta(
    id_consulta: UUID,
    payload: EncerramentoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = _get_consulta_or_404(id_consulta, db)

    if consulta.status == "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta já encerrada")

    existente = db.query(ConsultaEncerramento).filter(ConsultaEncerramento.id_consulta == id_consulta).first()
    if existente:
        raise HTTPException(status_code=409, detail="Encerramento já registrado")

    enc = ConsultaEncerramento(
        id_consulta=id_consulta,
        conduta=payload.conduta,
        encaminhamentos=payload.encaminhamentos,
        data_proximo_retorno=payload.data_proximo_retorno,
        observacoes=payload.observacoes,
        encerrado_por=current_user.id,
    )
    db.add(enc)

    consulta.status = "ENCERRADA"
    consulta.encerrada_em = datetime.now(timezone.utc)

    db.commit()
    db.refresh(enc)
    return EncerramentoOut.model_validate(enc)


@router.get(
    "/{id_consulta}/encerramento",
    response_model=EncerramentoOut,
    response_model_by_alias=True,
)
def obter_encerramento(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    enc = db.query(ConsultaEncerramento).filter(ConsultaEncerramento.id_consulta == id_consulta).first()
    if not enc:
        raise HTTPException(status_code=404, detail="Encerramento não encontrado")
    return EncerramentoOut.model_validate(enc)


@router.get(
    "/{id_consulta}/resumo-pec",
    response_model=ResumoPecOut,
    response_model_by_alias=True,
)
def obter_resumo_pec(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = _get_consulta_or_404(id_consulta, db)
    if consulta.status != "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta ainda não encerrada")

    enc = db.query(ConsultaEncerramento).filter(ConsultaEncerramento.id_consulta == id_consulta).first()
    if not enc:
        raise HTTPException(status_code=404, detail="Dados de encerramento não encontrados")

    triagem = db.query(ConsultaTriagem).filter(ConsultaTriagem.id_consulta == id_consulta).first()
    resultado = db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()

    peso_kg = float(triagem.peso_kg) if triagem else None
    pa = f"{triagem.pa_sistolica}/{triagem.pa_diastolica} mmHg" if triagem else None

    return ResumoPecOut(
        id_consulta=id_consulta,
        tipo_consulta=consulta.tipo_consulta,
        data_consulta=consulta.aberta_em.date(),
        ig_semanas=consulta.ig_semanas,
        ig_dias=consulta.ig_dias,
        peso_kg=peso_kg,
        pa=pa,
        score_risco=resultado.score_geral if resultado else None,
        faixa_risco=resultado.faixa_risco if resultado else None,
        conduta=enc.conduta,
        encaminhamentos=enc.encaminhamentos or [],
        data_proximo_retorno=enc.data_proximo_retorno,
        gerado_em=datetime.now(timezone.utc),
    )


@router.get("/{id_consulta}/resumo-pec/pdf")
def baixar_resumo_pec_pdf(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    resumo = obter_resumo_pec(id_consulta=id_consulta, db=db, current_user=current_user)
    pdf_bytes = _gerar_pdf(resumo)
    filename = f"resumo_pec_{id_consulta}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
