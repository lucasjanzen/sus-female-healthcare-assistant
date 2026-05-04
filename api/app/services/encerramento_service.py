import io
from datetime import date, timedelta
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.consulta import ResumoPecOut

_DIAS_RETORNO_FAIXA: dict[str, int] = {
    "VERDE": 30,
    "AMARELO": 14,
    "LARANJA": 7,
    "VERMELHO": 2,
}

_ENCAMINHAMENTOS_FAIXA: dict[str, list[str]] = {
    "LARANJA": ["PSICOLOGIA", "ASSISTENCIA_SOCIAL"],
    "VERMELHO": ["CAPS", "CVR", "ASSISTENCIA_SOCIAL"],
}

_COR_FAIXA: dict[str, colors.Color] = {
    "VERDE": colors.HexColor("#2e7d32"),
    "AMARELO": colors.HexColor("#f57f17"),
    "LARANJA": colors.HexColor("#e65100"),
    "VERMELHO": colors.HexColor("#b71c1c"),
}

_LABEL_FAIXA: dict[str, str] = {
    "VERDE": "Baixo Risco",
    "AMARELO": "Risco Moderado",
    "LARANJA": "Risco Elevado",
    "VERMELHO": "Risco Alto",
}

_LABEL_TIPO: dict[str, str] = {
    "PRENATAL": "Pré-natal",
    "GINECOLOGICA": "Ginecológica",
    "PUERPERIO": "Puerpério",
    "PLANEJAMENTO_FAMILIAR": "Planejamento Familiar",
}


def calcular_data_sugerida(faixa_risco: str, ig_semanas: Optional[int]) -> date:
    dias = _DIAS_RETORNO_FAIXA.get(faixa_risco, 30)
    if ig_semanas is not None:
        if ig_semanas < 28:
            max_ig = 28
        elif ig_semanas <= 36:
            max_ig = 14
        else:
            max_ig = 7
        dias = min(dias, max_ig)
    return date.today() + timedelta(days=dias)


def encaminhamentos_sugeridos(faixa_risco: str) -> list[str]:
    return list(_ENCAMINHAMENTOS_FAIXA.get(faixa_risco, []))


def gerar_pdf_resumo(resumo: ResumoPecOut) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    cor_faixa = _COR_FAIXA.get(resumo.faixa_risco, colors.grey)
    label_faixa = _LABEL_FAIXA.get(resumo.faixa_risco, resumo.faixa_risco)
    label_tipo = _LABEL_TIPO.get(resumo.tipo_consulta, resumo.tipo_consulta)

    titulo_style = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        textColor=colors.HexColor("#1a237e"),
        fontSize=16,
        spaceAfter=4,
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        textColor=colors.HexColor("#424242"),
        fontSize=10,
        spaceAfter=12,
    )
    secao_style = ParagraphStyle(
        "Secao",
        parent=styles["Heading3"],
        textColor=colors.HexColor("#1a237e"),
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
    )
    normal = styles["Normal"]
    bold_style = ParagraphStyle(
        "Bold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
    )

    elements = []

    # Cabeçalho
    elements.append(Paragraph("CASF — Centro de Assistência à Saúde Feminina", titulo_style))
    elements.append(Paragraph("Resumo da Consulta para e-SUS PEC", subtitulo_style))

    # Linha divisória via tabela de 1 linha
    elements.append(
        Table(
            [[""]],
            colWidths=[doc.width],
            style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#1a237e"))]),
        )
    )
    elements.append(Spacer(1, 8))

    # Dados da consulta
    elements.append(Paragraph("Dados da Consulta", secao_style))
    dados_consulta = [
        ["Tipo:", label_tipo],
        ["Data:", resumo.data_consulta.strftime("%d/%m/%Y")],
    ]
    if resumo.ig_semanas is not None:
        ig_str = f"{resumo.ig_semanas}s {resumo.ig_dias or 0}d"
        dados_consulta.append(["Idade Gestacional:", ig_str])
    if resumo.peso_kg:
        dados_consulta.append(["Peso:", f"{resumo.peso_kg:.1f} kg"])
    if resumo.pa:
        dados_consulta.append(["Pressão Arterial:", resumo.pa])

    table_dados = Table(dados_consulta, colWidths=[4 * cm, None])
    table_dados.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elements.append(table_dados)

    # Resultado da análise
    elements.append(Paragraph("Resultado da Análise IA", secao_style))

    score_style = ParagraphStyle(
        "Score",
        parent=styles["Normal"],
        textColor=cor_faixa,
        fontName="Helvetica-Bold",
        fontSize=14,
        spaceAfter=4,
    )
    elements.append(
        Paragraph(
            f"Score: {resumo.score_risco}/100 — {label_faixa}",
            score_style,
        )
    )

    if resumo.indicadores:
        elements.append(Paragraph("Indicadores detectados:", bold_style))
        for ind in resumo.indicadores:
            elements.append(Paragraph(f"• {ind}", normal))
    else:
        elements.append(Paragraph("Nenhum indicador de risco detectado.", normal))

    # Conduta
    elements.append(Paragraph("Conduta", secao_style))
    elements.append(Paragraph(resumo.conduta, normal))

    # Encaminhamentos
    if resumo.encaminhamentos:
        elements.append(Paragraph("Encaminhamentos", secao_style))
        for enc in resumo.encaminhamentos:
            elements.append(Paragraph(f"• {enc}", normal))

    # Próximo retorno
    elements.append(Paragraph("Próximo Retorno", secao_style))
    elements.append(Paragraph(resumo.data_proximo_retorno.strftime("%d/%m/%Y"), bold_style))

    # Rodapé
    elements.append(Spacer(1, 16))
    elements.append(
        Table(
            [[""]],
            colWidths=[doc.width],
            style=TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.grey)]),
        )
    )
    rodape_style = ParagraphStyle(
        "Rodape",
        parent=styles["Normal"],
        textColor=colors.grey,
        fontSize=8,
        spaceBefore=4,
    )
    elements.append(
        Paragraph(
            f"Gerado em {resumo.gerado_em.strftime('%d/%m/%Y às %H:%M')} UTC — CASF v2.0",
            rodape_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
