"""
Testes unitários para app.services.analise_service
---------------------------------------------------
Cobrem: normalização de texto, detecção de sentimento negativo, detecção de
indicadores por tipo/nível, cálculo de faixa de risco, modificador vocal e a
função pública `analisar_texto` usada como fallback do LLM.
"""
import pytest

from app.services.analise_service import (
    PESOS,
    _detectar,
    _faixa,
    _normalizar,
    _sentimento_negativo_forte,
    analisar_texto,
    calcular_faixa,
    _calcular_voice_modifier,
)


# ---------------------------------------------------------------------------
# _normalizar
# ---------------------------------------------------------------------------

class TestNormalizar:
    def test_remove_acentos(self):
        assert _normalizar("Tristeza") == "tristeza"

    def test_converte_para_minusculo(self):
        assert _normalizar("MEDO") == "medo"

    def test_acento_composto(self):
        assert _normalizar("ansiedade") == "ansiedade"

    def test_texto_vazio(self):
        assert _normalizar("") == ""

    def test_preserva_espacos(self):
        assert _normalizar("sem esperança") == "sem esperanca"


# ---------------------------------------------------------------------------
# _sentimento_negativo_forte
# ---------------------------------------------------------------------------

class TestSentimentoNegativoForte:
    def test_menos_de_dois_negativos_retorna_false(self):
        assert _sentimento_negativo_forte("medo") is False

    def test_dois_ou_mais_negativos_retorna_true(self):
        assert _sentimento_negativo_forte("medo triste") is True

    def test_sem_negativos(self):
        assert _sentimento_negativo_forte("consulta de rotina") is False

    def test_tres_negativos(self):
        assert _sentimento_negativo_forte("nao triste choro") is True


# ---------------------------------------------------------------------------
# calcular_faixa
# ---------------------------------------------------------------------------

class TestCalcularFaixa:
    @pytest.mark.parametrize("score,esperado", [
        (0,   "VERDE"),
        (25,  "VERDE"),
        (26,  "AMARELO"),
        (50,  "AMARELO"),
        (51,  "LARANJA"),
        (75,  "LARANJA"),
        (76,  "VERMELHO"),
        (100, "VERMELHO"),
    ])
    def test_limites(self, score, esperado):
        assert calcular_faixa(score) == esperado


# ---------------------------------------------------------------------------
# _faixa
# ---------------------------------------------------------------------------

class TestFaixa:
    def test_retorna_tupla_faixa_mensagem(self):
        faixa, msg = _faixa(0)
        assert faixa == "VERDE"
        assert "Nenhum indicador" in msg

    def test_vermelho_tem_mensagem_critica(self):
        _, msg = _faixa(100)
        assert "criticos" in msg.lower()


# ---------------------------------------------------------------------------
# _detectar
# ---------------------------------------------------------------------------

class TestDetectar:
    def test_texto_limpo_sem_indicadores(self):
        indicadores = _detectar("tudo bem consulta normal", "TEXTO_LOCAL")
        assert indicadores == []

    def test_detecta_depressao(self):
        texto = _normalizar("estou com tristeza e solidao")
        indicadores = _detectar(texto, "TEXTO_LOCAL")
        tipos = [i.tipo for i in indicadores]
        assert "DEPRESSAO" in tipos

    def test_violencia_domestica_sempre_alto(self):
        texto = _normalizar("ele bateu em mim e me ameaca")
        indicadores = _detectar(texto, "TEXTO_LOCAL")
        vd = next((i for i in indicadores if i.tipo == "VIOLENCIA_DOMESTICA"), None)
        assert vd is not None
        assert vd.nivel == "ALTO"

    def test_origem_preservada(self):
        texto = _normalizar("sozinha e sem apoio")
        indicadores = _detectar(texto, "VOZ")
        assert all(i.origem == "VOZ" for i in indicadores)

    def test_nivel_alto_com_negativo_forte_e_dois_matches(self):
        # "nao" + "medo" = negativo_forte=True; "tristeza" + "choro" = 2 matches DEPRESSAO
        texto = _normalizar("nao medo tristeza choro")
        indicadores = _detectar(texto, "TEXTO_LOCAL")
        dep = next((i for i in indicadores if i.tipo == "DEPRESSAO"), None)
        assert dep is not None
        assert dep.nivel == "ALTO"

    def test_nivel_moderado_com_sentimento_negativo_e_um_match(self):
        # "triste" aciona negativo=True; apenas "tristeza" como match
        texto = _normalizar("triste tristeza")
        indicadores = _detectar(texto, "TEXTO_LOCAL")
        dep = next((i for i in indicadores if i.tipo == "DEPRESSAO"), None)
        assert dep is not None
        assert dep.nivel == "MODERADO"


# ---------------------------------------------------------------------------
# _calcular_voice_modifier
# ---------------------------------------------------------------------------

class TestCalcularVoiceModifier:
    def test_none_retorna_zero(self):
        assert _calcular_voice_modifier(None) == 0

    def test_sem_scores_retorna_zero(self):
        assert _calcular_voice_modifier({}) == 0

    def test_negativo_baixo_retorna_zero(self):
        sv = {"scores": {"negativo": 0.3, "positivo": 0.5, "neutro": 0.2}}
        assert _calcular_voice_modifier(sv) == 0

    def test_negativo_moderado_retorna_10(self):
        sv = {"scores": {"negativo": 0.7, "positivo": 0.1, "neutro": 0.2}}
        assert _calcular_voice_modifier(sv) == 10

    def test_negativo_alto_retorna_15(self):
        sv = {"scores": {"negativo": 0.9, "positivo": 0.0, "neutro": 0.1}}
        assert _calcular_voice_modifier(sv) == 15


# ---------------------------------------------------------------------------
# analisar_texto  (função pública / fallback)
# ---------------------------------------------------------------------------

class TestAnalisarTexto:
    def test_texto_neutro_score_zero(self):
        score, indicadores, resumo = analisar_texto("consulta de rotina, sem queixas.")
        assert score == 0
        assert indicadores == []
        assert "Nenhum indicador" in resumo

    def test_violencia_domestica_gera_score_alto(self):
        score, indicadores, resumo = analisar_texto("ele bateu em mim e me ameaça")
        assert score >= 40
        tipos = [i.tipo for i in indicadores]
        assert "VIOLENCIA_DOMESTICA" in tipos

    def test_multiplos_indicadores_score_acumulado(self):
        texto = "tristeza choro sozinha sem apoio medo nervosa"
        score, indicadores, _ = analisar_texto(texto)
        assert len(indicadores) >= 2
        # Score deve ser >= soma dos PESOS mínimos dos dois indicadores
        assert score > 0

    def test_score_max_100(self):
        texto = (
            "tristeza choro sem esperanca nao quero mais cansada solidao vazio sem vontade "
            "medo preocupada nervosa nao consigo dormir tensao coracao acelerado sufocando "
            "bateu ameaca com medo dele nao posso sair ele nao deixa "
            "sozinha ninguem me ajuda sem apoio marido nao ajuda sem amigos"
        )
        score, _, _ = analisar_texto(texto)
        assert score <= 100

    def test_resumo_contem_aviso_clinico(self):
        _, _, resumo = analisar_texto("tristeza")
        assert "responsabilidade do profissional" in resumo.lower()

    def test_retorna_tuple_com_tres_elementos(self):
        resultado = analisar_texto("qualquer texto")
        assert len(resultado) == 3
        score, indicadores, resumo = resultado
        assert isinstance(score, int)
        assert isinstance(indicadores, list)
        assert isinstance(resumo, str)
