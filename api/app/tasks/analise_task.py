import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.session import SessionLocal
from app.models.consulta import ConsultaIdentidade, ConsultaRelato, ConsultaResultado
import app.services.analise_llm_service as analise_llm_service

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def _llm_indicadores_para_ia(indicadores_llm: list) -> list:
    result = []
    for ind in indicadores_llm:
        evidencias = ind.get("evidencias", [])
        result.append({
            "tipo": ind.get("tipo", ""),
            "nivel": ind.get("nivel", "BAIXO"),
            "descricao": "; ".join(evidencias) if evidencias else ind.get("recomendacao", ""),
            "origem": "LLM",
        })
    return result


def processar_analise(
    id_consulta_str: str,
    audio_bytes: Optional[bytes] = None,
    content_type: str = "audio/webm",
    tentativa: int = 0,
) -> None:
    """Processa a análise de IA para uma consulta encerrada."""
    from uuid import UUID
    id_consulta = UUID(id_consulta_str)
    db = SessionLocal()
    try:
        transcricao = ""
        sentimento_voz = None

        if audio_bytes:
            from app.services.azure_service import transcrever_e_analisar_voz
            resultado_voz = transcrever_e_analisar_voz(audio_bytes, content_type)
            transcricao = resultado_voz.get("transcricao", "")
            sentimento_voz = resultado_voz.get("sentimento_voz")
            logger.info("Transcrição obtida para consulta %s (%d chars)", id_consulta, len(transcricao))

        resultado_llm = analise_llm_service.analisar_com_llm(
            id_consulta, db, transcricao, sentimento_voz
        )

        resultado = (
            db.query(ConsultaResultado)
            .filter(ConsultaResultado.id_consulta == id_consulta)
            .first()
        )
        if not resultado:
            resultado = ConsultaResultado(id_consulta=id_consulta, indicadores=[])
            db.add(resultado)

        resultado.sentimento_voz = sentimento_voz
        resultado.score_geral = int(resultado_llm["score_geral"])
        resultado.faixa_risco = resultado_llm["faixa_risco"]
        resultado.resumo_ia = resultado_llm["resumo_ia"]
        resultado.indicadores = _llm_indicadores_para_ia(resultado_llm["indicadores"])
        resultado.sumario_estruturado = resultado_llm["sumario_estruturado"]
        resultado.texto_clinico = resultado_llm["texto_clinico"]
        resultado.fontes_utilizadas = resultado_llm["fontes_utilizadas"]
        resultado.tokens_utilizados = resultado_llm["tokens_utilizados"]
        resultado.prompt_enviado = resultado_llm.get("prompt_enviado")
        resultado.resposta_bruta_llm = resultado_llm.get("resposta_bruta_llm")
        resultado.calculado_em = datetime.now(timezone.utc)

        consulta = (
            db.query(ConsultaIdentidade)
            .filter(ConsultaIdentidade.id_consulta == id_consulta)
            .first()
        )
        if consulta:
            consulta.analise_concluida_em = datetime.now(timezone.utc)
            consulta.analise_erro = None

        db.commit()
        logger.info("Análise concluída para consulta %s", id_consulta)

    except Exception as exc:
        logger.error("Falha na análise para consulta %s (tentativa %d): %s", id_consulta, tentativa, exc)
        try:
            consulta = (
                db.query(ConsultaIdentidade)
                .filter(ConsultaIdentidade.id_consulta == id_consulta)
                .first()
            )
            if consulta:
                if tentativa < MAX_RETRIES:
                    # A próxima tentativa será disparada pelo caller
                    pass
                else:
                    consulta.analise_erro = str(exc)[:500]
            db.commit()
        except Exception:
            pass
    finally:
        db.close()
