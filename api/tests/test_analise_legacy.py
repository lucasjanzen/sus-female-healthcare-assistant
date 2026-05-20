"""
Testes unitários para módulos auxiliares de análise
----------------------------------------------------
Cobre: encerramento_service (cálculo de data de retorno e encaminhamentos)
       analise_llm_service (_fallback_local sem rede)
"""
import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.encerramento_service import (
    calcular_data_sugerida,
    encaminhamentos_sugeridos,
)


# ---------------------------------------------------------------------------
# encerramento_service
# ---------------------------------------------------------------------------

class TestCalcularDataSugerida:
    def test_verde_30_dias(self):
        resultado = calcular_data_sugerida("VERDE", ig_semanas=None)
        assert resultado == date.today() + timedelta(days=30)

    def test_amarelo_14_dias(self):
        resultado = calcular_data_sugerida("AMARELO", ig_semanas=None)
        assert resultado == date.today() + timedelta(days=14)

    def test_laranja_7_dias(self):
        resultado = calcular_data_sugerida("LARANJA", ig_semanas=None)
        assert resultado == date.today() + timedelta(days=7)

    def test_vermelho_2_dias(self):
        resultado = calcular_data_sugerida("VERMELHO", ig_semanas=None)
        assert resultado == date.today() + timedelta(days=2)

    def test_ig_alta_limita_retorno(self):
        # IG >= 37 semanas → max_ig = 7 dias
        resultado = calcular_data_sugerida("VERDE", ig_semanas=38)
        assert resultado == date.today() + timedelta(days=7)

    def test_ig_entre_28_e_36_limita_a_14(self):
        resultado = calcular_data_sugerida("VERDE", ig_semanas=32)
        assert resultado == date.today() + timedelta(days=14)

    def test_ig_menor_28_nao_limita_verde(self):
        # IG < 28 → max_ig = 28; VERDE = 30 → usa 28
        resultado = calcular_data_sugerida("VERDE", ig_semanas=20)
        assert resultado == date.today() + timedelta(days=28)

    def test_vermelho_com_ig_alta_mantem_2_dias(self):
        # min(2, 7) = 2
        resultado = calcular_data_sugerida("VERMELHO", ig_semanas=38)
        assert resultado == date.today() + timedelta(days=2)


class TestEncaminhamentosSugeridos:
    def test_verde_sem_encaminhamentos(self):
        assert encaminhamentos_sugeridos("VERDE") == []

    def test_amarelo_sem_encaminhamentos(self):
        assert encaminhamentos_sugeridos("AMARELO") == []

    def test_laranja_retorna_psicologia_e_assistencia(self):
        enc = encaminhamentos_sugeridos("LARANJA")
        assert "PSICOLOGIA" in enc
        assert "ASSISTENCIA_SOCIAL" in enc

    def test_vermelho_retorna_caps_e_cvr(self):
        enc = encaminhamentos_sugeridos("VERMELHO")
        assert "CAPS" in enc
        assert "CVR" in enc

    def test_retorna_copia_independente(self):
        enc1 = encaminhamentos_sugeridos("LARANJA")
        enc2 = encaminhamentos_sugeridos("LARANJA")
        enc1.append("EXTRA")
        assert "EXTRA" not in enc2


# ---------------------------------------------------------------------------
# analise_llm_service — _fallback_local (sem rede)
# ---------------------------------------------------------------------------

try:
    import openai  # noqa: F401
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

_skip_if_no_openai = pytest.mark.skipif(
    not _OPENAI_AVAILABLE,
    reason="pacote 'openai' não instalado neste ambiente",
)


@_skip_if_no_openai
class TestFallbackLocal:
    """Valida que o fallback por palavras-chave é invocado quando o LLM falha."""

    def _make_ctx(self, relato: str = "", transcricao: str = "") -> dict:
        return {
            "relato_texto": relato,
            "transcricao": transcricao,
            "sentimento_voz": None,
            "dados_consulta": {},
            "historico_consultas": [],
            "historico_peso": [],
            "fontes_utilizadas": {
                "relato": bool(relato),
                "transcricao": bool(transcricao),
                "sentimento_voz": False,
                "dados_consulta": False,
                "historico": False,
            },
        }

    def test_fallback_com_texto_neutro(self):
        from app.services.analise_llm_service import _fallback_local

        resultado = _fallback_local(self._make_ctx("consulta de rotina"))
        assert resultado["score_geral"] == 0
        assert resultado["faixa_risco"] == "VERDE"
        assert resultado["modo_fallback"] is True  # via sumario_estruturado

    def test_fallback_com_violencia_detecta_vermelho_ou_laranja(self):
        from app.services.analise_llm_service import _fallback_local

        resultado = _fallback_local(
            self._make_ctx("ele bateu em mim e me ameaça")
        )
        assert resultado["faixa_risco"] in ("LARANJA", "VERMELHO")
        assert resultado["tokens_utilizados"] == 0

    def test_fallback_retorna_modo_fallback_true(self):
        from app.services.analise_llm_service import _fallback_local

        resultado = _fallback_local(self._make_ctx())
        assert resultado["sumario_estruturado"]["modo_fallback"] is True

    def test_analisar_com_llm_usa_fallback_quando_openai_falha(self):
        from app.services import analise_llm_service

        fake_db = MagicMock()
        # coletar_contexto retorna contexto mínimo sem bater no banco
        ctx = self._make_ctx("tristeza e solidao")

        with (
            patch.object(analise_llm_service, "coletar_contexto", return_value=ctx),
            patch.object(
                analise_llm_service,
                "chamar_gpt4o",
                side_effect=Exception("timeout"),
            ),
        ):
            resultado = analise_llm_service.analisar_com_llm(
                id_consulta=uuid4(), db=fake_db
            )

        assert resultado["sumario_estruturado"]["modo_fallback"] is True
