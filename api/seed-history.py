"""
CASF — seed_historico.py
Gera histórico de consultas encerradas + evolução de peso para as 3 pacientes
do seed.py principal. Permite testar a análise LLM com contexto histórico real.

USO:
    python seed_historico.py

PRÉ-REQUISITOS:
    - seed.py já executado (pacientes e usuários criados)
    - .env configurado com DATABASE_URL e SECRET_SALT

O script é idempotente — pode ser rodado múltiplas vezes sem duplicar dados.

Mapeamento dos casos de teste:
    Ana Silva      → Caso 3: ginecológica SEM problemas (VERDE → VERDE → VERDE)
    Maria Oliveira → Caso 2: ginecológica COM violência doméstica (AMARELO → LARANJA → VERMELHO)
    Julia Santos   → Caso 1: pré-natal COM depressão perinatal (VERDE → AMARELO → LARANJA)
"""

import hashlib
import json
import os
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_SALT = os.getenv("SECRET_SALT")

if not DATABASE_URL or not SECRET_SALT:
    raise RuntimeError("DATABASE_URL e SECRET_SALT devem estar configurados no .env")

engine = create_engine(DATABASE_URL)

# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------


def cpf_hash(cpf: str) -> str:
    return hashlib.sha256((cpf + SECRET_SALT).encode()).hexdigest()


def nova_id() -> str:
    return str(uuid.uuid4())


def data_passada(dias: int) -> date:
    return date.today() - timedelta(days=dias)


def dt_passada(dias: int, hora: int = 9) -> datetime:
    return (
        datetime.now()
        - timedelta(days=dias)
        + timedelta(hours=hora - datetime.now().hour)
    )


# -------------------------------------------------------
# CPF das pacientes (mesmo do seed.py)
# -------------------------------------------------------

CPF_ANA = "11122233344"
CPF_MARIA = "55566677788"
CPF_JULIA = "99988877766"

# UBS e estado fictícios (usados em todos os registros)
UBS_ID = "00000000-0000-0000-0000-000000000001"
ESTADO_ID = "SC"


def buscar_paciente_id(conn, cpf: str) -> str | None:
    row = conn.execute(
        text("SELECT id FROM pacientes WHERE cpf_hash = :h"), {"h": cpf_hash(cpf)}
    ).fetchone()
    return str(row.id) if row else None


def buscar_profissional_id(conn, email: str) -> str | None:
    row = conn.execute(
        text("SELECT id FROM usuarios WHERE email = :e"), {"e": email}
    ).fetchone()
    return str(row.id) if row else None


def consulta_ja_existe(conn, paciente_id: str, aberta_em: datetime) -> bool:
    row = conn.execute(
        text("""SELECT 1 FROM consultas_identidade
                WHERE paciente_id = :pid
                  AND DATE(aberta_em) = :d LIMIT 1"""),
        {"pid": paciente_id, "d": aberta_em.date()},
    ).fetchone()
    return row is not None


# -------------------------------------------------------
# INSERÇÃO DE UMA CONSULTA ENCERRADA COMPLETA
# -------------------------------------------------------


def inserir_consulta(
    conn,
    paciente_id: str,
    profissional_id: str,
    medico_id: str,
    tipo_consulta: str,
    dias_atras: int,
    peso_kg: float,
    pa_sistolica: int,
    pa_diastolica: int,
    dum: date | None,
    relato_texto: str,
    faixa_risco: str,
    score_geral: int,
    resumo_ia: str,
    encaminhamentos: list[str],
    indicadores: list[dict],
):
    aberta_em = dt_passada(dias_atras)

    if consulta_ja_existe(conn, paciente_id, aberta_em):
        print(f"    [skip] consulta de {aberta_em.date()} ja existe, pulando.")
        return

    id_consulta = nova_id()

    # IG calculada pela DUM
    ig_semanas, ig_dias = None, None
    if dum and tipo_consulta == "PRENATAL":
        delta = (aberta_em.date() - dum).days
        ig_semanas = delta // 7
        ig_dias = delta % 7

    # consultas_identidade
    conn.execute(
        text("""
        INSERT INTO consultas_identidade (
            id_consulta, paciente_id, profissional_id, medico_id, ubs_id,
            estado_id, tipo_consulta, status,
            dum, ig_semanas, ig_dias,
            triagem_concluida, triagem_concluida_em,
            assumida_em, aberta_em, encerrada_em,
            analise_revisada, encaminhado
        ) VALUES (
            :id, :pid, :prof, :med, :ubs,
            :estado, :tipo, 'ENCERRADA',
            :dum, :ig_s, :ig_d,
            true, :aberta,
            :aberta, :aberta, :aberta,
            true, :enc
        )
    """),
        {
            "id": id_consulta,
            "pid": paciente_id,
            "prof": profissional_id,
            "med": medico_id,
            "ubs": UBS_ID,
            "estado": ESTADO_ID,
            "tipo": tipo_consulta,
            "dum": dum,
            "ig_s": ig_semanas,
            "ig_d": ig_dias,
            "aberta": aberta_em,
            "enc": len(encaminhamentos) > 0,
        },
    )

    # consulta_triagem
    conn.execute(
        text("""
        INSERT INTO consulta_triagem (
            id, id_consulta, peso_kg, pa_sistolica, pa_diastolica,
            registrado_por, registrado_em
        ) VALUES (
            :id, :ic, :peso, :pas, :pad, :prof, :em
        )
    """),
        {
            "id": nova_id(),
            "ic": id_consulta,
            "peso": Decimal(str(peso_kg)),
            "pas": pa_sistolica,
            "pad": pa_diastolica,
            "prof": profissional_id,
            "em": aberta_em,
        },
    )

    # historico_peso
    conn.execute(
        text("""
        INSERT INTO historico_peso (id, paciente_id, id_consulta, peso_kg, registrado_em)
        VALUES (:id, :pid, :ic, :peso, :em)
        ON CONFLICT DO NOTHING
    """),
        {
            "id": nova_id(),
            "pid": paciente_id,
            "ic": id_consulta,
            "peso": Decimal(str(peso_kg)),
            "em": aberta_em,
        },
    )

    # consulta_relato
    conn.execute(
        text("""
        INSERT INTO consulta_relato (
            id, id_consulta, relato_texto, parecer_medico,
            registrado_por, registrado_em, atualizado_em
        ) VALUES (
            :id, :ic, :rel, :par, :prof, :em, :em
        )
    """),
        {
            "id": nova_id(),
            "ic": id_consulta,
            "rel": relato_texto,
            "par": resumo_ia,
            "prof": medico_id,
            "em": aberta_em,
        },
    )

    # consulta_resultado
    conn.execute(
        text("""
        INSERT INTO consulta_resultado (
            id, id_consulta, score_geral, faixa_risco,
            indicadores, resumo_ia,
            sumario_estruturado, texto_clinico, fontes_utilizadas,
            calculado_em, confirmado, confirmado_em
        ) VALUES (
            :id, :ic, :score, :faixa,
            CAST(:ind AS jsonb), :resumo,
            CAST(:sumario AS jsonb), :texto, CAST(:fontes AS jsonb),
            :em, true, :em
        )
    """),
        {
            "id": nova_id(),
            "ic": id_consulta,
            "score": score_geral,
            "faixa": faixa_risco,
            "ind": json.dumps(indicadores, ensure_ascii=False),
            "resumo": resumo_ia,
            "sumario": json.dumps(
                {
                    "indicadores": indicadores,
                    "score_geral": score_geral,
                    "faixa_risco": faixa_risco,
                    "pontos_atencao": [],
                    "encaminhamentos_sugeridos": encaminhamentos,
                    "contexto_historico": "Histórico gerado por seed de testes.",
                    "modo_fallback": False,
                },
                ensure_ascii=False,
            ),
            "texto": resumo_ia,
            "fontes": json.dumps(
                {
                    "relato": True,
                    "transcricao": False,
                    "sentimento_voz": False,
                    "historico": False,
                }
            ),
            "em": aberta_em,
        },
    )

    # consulta_encerramento
    conn.execute(
        text("""
        INSERT INTO consulta_encerramento (
            id, id_consulta, conduta, encaminhamentos,
            data_proximo_retorno, encerrado_por, encerrado_em
        ) VALUES (
            :id, :ic, :conduta, CAST(:enc AS jsonb),
            :retorno, :prof, :em
        )
    """),
        {
            "id": nova_id(),
            "ic": id_consulta,
            "conduta": resumo_ia,
            "enc": json.dumps(encaminhamentos, ensure_ascii=False),
            "retorno": aberta_em.date() + timedelta(days=30),
            "prof": medico_id,
            "em": aberta_em,
        },
    )

    print(
        f"    [OK] consulta {id_consulta[:8]}... inserida ({aberta_em.date()}, {faixa_risco})"
    )


# -------------------------------------------------------
# CASO 3 — ANA SILVA — Ginecológica SEM problemas
# -------------------------------------------------------


def seed_ana(conn, paciente_id, enfermeiro_id, medico_id):
    """
    Ana Silva — consultas ginecológicas de rotina, sem indicadores de risco.
    Contexto para validar ausência de falsos positivos.
    """
    print("  Ana Silva (ginecológica, sem problemas):")

    consultas = [
        dict(
            dias_atras=180,
            peso_kg=62.0,
            pa_sistolica=112,
            pa_diastolica=72,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Paciente veio para consulta de rotina anual. Sem queixas. "
                "Refere estar bem no trabalho e na vida pessoal. "
                "Relacionamento estável. Dorme bem, alimentação adequada."
            ),
            faixa_risco="VERDE",
            score_geral=5,
            resumo_ia="Paciente sem indicadores de risco nesta consulta. Consulta de rotina dentro da normalidade.",
            encaminhamentos=[],
            indicadores=[],
        ),
        dict(
            dias_atras=90,
            peso_kg=62.5,
            pa_sistolica=110,
            pa_diastolica=70,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Retorno de rotina. Paciente relata vida estável. "
                "Pratica caminhada três vezes por semana. "
                "Sem queixas ginecológicas. Humor preservado."
            ),
            faixa_risco="VERDE",
            score_geral=8,
            resumo_ia="Paciente em bom estado geral. Nenhum indicador psicossocial identificado.",
            encaminhamentos=[],
            indicadores=[],
        ),
        dict(
            dias_atras=30,
            peso_kg=63.0,
            pa_sistolica=114,
            pa_diastolica=74,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Consulta de acompanhamento. Paciente relata leve cansaço "
                "por excesso de trabalho nos últimos dias, porém sem impacto "
                "significativo no bem-estar. Sem alterações no humor. Dorme bem."
            ),
            faixa_risco="VERDE",
            score_geral=12,
            resumo_ia="Paciente apresenta cansaço pontual relacionado ao trabalho, sem indicadores de risco psicossocial.",
            encaminhamentos=[],
            indicadores=[
                {
                    "tipo": "OUTRO",
                    "nivel": "BAIXO",
                    "evidencias": ["cansaço pontual por excesso de trabalho"],
                    "recomendacao": "Monitorar nas próximas consultas",
                },
            ],
        ),
    ]

    for c in consultas:
        inserir_consulta(conn, paciente_id, enfermeiro_id, medico_id, **c)


# -------------------------------------------------------
# CASO 2 — MARIA OLIVEIRA — Ginecológica COM violência doméstica
# -------------------------------------------------------


def seed_maria(conn, paciente_id, enfermeiro_id, medico_id):
    """
    Maria Oliveira — consultas ginecológicas com sinais progressivos
    de violência doméstica. Contexto para testar detecção de VD.
    """
    print("  Maria Oliveira (ginecológica, violência doméstica progressiva):")

    consultas = [
        dict(
            dias_atras=210,
            peso_kg=67.0,
            pa_sistolica=118,
            pa_diastolica=76,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Primeira consulta na UBS. Paciente chegou quieta. "
                "Sem queixas específicas. Quando perguntada sobre a vida em casa, "
                "disse que estava tudo bem mas desviou o olhar. "
                "Não quis desenvolver o assunto."
            ),
            faixa_risco="AMARELO",
            score_geral=28,
            resumo_ia=(
                "Paciente demonstrou comportamento evasivo ao ser questionada "
                "sobre a vida doméstica. Recomenda-se atenção nas próximas consultas."
            ),
            encaminhamentos=[],
            indicadores=[
                {
                    "tipo": "VIOLENCIA_DOMESTICA",
                    "nivel": "BAIXO",
                    "evidencias": [
                        "comportamento evasivo ao falar sobre a vida em casa"
                    ],
                    "recomendacao": "Monitorar nas próximas consultas",
                },
            ],
        ),
        dict(
            dias_atras=120,
            peso_kg=65.5,
            pa_sistolica=122,
            pa_diastolica=80,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Paciente retornou com hematoma no braço, atribuiu a uma queda. "
                "Apresentou-se nervosa durante toda a consulta. "
                "Ao ser perguntada sobre o companheiro, disse que ele "
                "'às vezes perde a paciência'. Peso abaixo do esperado."
            ),
            faixa_risco="LARANJA",
            score_geral=62,
            resumo_ia=(
                "Paciente apresenta sinais sugestivos de violência doméstica. "
                "Hematoma com justificativa inconsistente e referência ao "
                "comportamento agressivo do companheiro são alertas importantes. "
                "Encaminhamento para serviço social recomendado."
            ),
            encaminhamentos=["SERVICO_SOCIAL", "CVR"],
            indicadores=[
                {
                    "tipo": "VIOLENCIA_DOMESTICA",
                    "nivel": "MODERADO",
                    "evidencias": [
                        "hematoma com justificativa inconsistente",
                        "referência ao companheiro perdendo a paciência",
                    ],
                    "recomendacao": "Encaminhamento para serviço social e CVR",
                },
                {
                    "tipo": "ISOLAMENTO_SOCIAL",
                    "nivel": "BAIXO",
                    "evidencias": [
                        "paciente evitou contato visual",
                        "respostas curtas e evasivas",
                    ],
                    "recomendacao": "Avaliar rede de apoio na próxima consulta",
                },
            ],
        ),
        dict(
            dias_atras=45,
            peso_kg=64.0,
            pa_sistolica=128,
            pa_diastolica=84,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Paciente chegou com óculos escuros. Ao retirar, apresentou "
                "equimose periorbital. Disse que bateu o rosto na porta. "
                "Ficou em silêncio por longos períodos. Quando perguntada "
                "diretamente se estava segura em casa, respondeu "
                "'preciso ir embora logo' sem dar explicação."
            ),
            faixa_risco="VERMELHO",
            score_geral=88,
            resumo_ia=(
                "Paciente apresenta indicadores críticos de violência doméstica. "
                "Equimose periorbital com justificativa implausível, comportamento "
                "de fuga e recusa em responder sobre segurança em casa configuram "
                "situação de alto risco. Protocolo de violência doméstica deve "
                "ser acionado imediatamente."
            ),
            encaminhamentos=["CVR", "DELEGACIA_MULHER", "ASSISTENCIA_SOCIAL"],
            indicadores=[
                {
                    "tipo": "VIOLENCIA_DOMESTICA",
                    "nivel": "ALTO",
                    "evidencias": [
                        "equimose periorbital com justificativa implausível",
                        "comportamento de fuga durante a consulta",
                        "recusa em responder sobre segurança em casa",
                    ],
                    "recomendacao": "Acionar protocolo de violência doméstica imediatamente",
                },
                {
                    "tipo": "DEPRESSAO",
                    "nivel": "MODERADO",
                    "evidencias": [
                        "longos períodos de silêncio",
                        "ausência de expressão emocional",
                    ],
                    "recomendacao": "Acompanhamento psicológico após garantir segurança",
                },
            ],
        ),
    ]

    for c in consultas:
        inserir_consulta(conn, paciente_id, enfermeiro_id, medico_id, **c)


# -------------------------------------------------------
# CASO 1 — JULIA SANTOS — Pré-natal COM depressão perinatal
# -------------------------------------------------------


def seed_julia(conn, paciente_id, enfermeiro_id, medico_id):
    """
    Julia Santos — pré-natal com sinais progressivos de depressão perinatal
    e isolamento social. Contexto para testar detecção de depressão gestacional.
    """
    print("  Julia Santos (pré-natal, depressão perinatal progressiva):")
    dum = data_passada(168)  # ~24 semanas atrás

    consultas = [
        dict(
            dias_atras=120,
            peso_kg=58.0,
            pa_sistolica=108,
            pa_diastolica=68,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Primeira consulta pré-natal. Paciente jovem, gestação planejada. "
                "Está animada com a gravidez. Refere apoio do marido e da família. "
                "Sem queixas."
            ),
            faixa_risco="VERDE",
            score_geral=8,
            resumo_ia="Primeira consulta sem indicadores de risco. Gestante em bom estado emocional com suporte familiar adequado.",
            encaminhamentos=[],
            indicadores=[],
        ),
        dict(
            dias_atras=70,
            peso_kg=59.5,
            pa_sistolica=112,
            pa_diastolica=70,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Paciente refere dificuldade para dormir desde a última semana. "
                "Acorda de madrugada com preocupações sobre o parto e se vai "
                "ser uma boa mãe. Chora com facilidade. "
                "Marido trabalha muito e está pouco presente."
            ),
            faixa_risco="AMARELO",
            score_geral=38,
            resumo_ia=(
                "Paciente apresenta sinais iniciais de ansiedade gestacional "
                "e insegurança em relação à maternidade. Ausência crescente "
                "do suporte do companheiro é fator de atenção."
            ),
            encaminhamentos=[],
            indicadores=[
                {
                    "tipo": "ANSIEDADE",
                    "nivel": "BAIXO",
                    "evidencias": [
                        "dificuldade para dormir",
                        "preocupações frequentes sobre o parto",
                    ],
                    "recomendacao": "Monitorar nas próximas consultas",
                },
                {
                    "tipo": "DEPRESSAO",
                    "nivel": "BAIXO",
                    "evidencias": [
                        "choro com facilidade",
                        "insegurança sobre a maternidade",
                    ],
                    "recomendacao": "Atenção ao suporte emocional",
                },
            ],
        ),
        dict(
            dias_atras=30,
            peso_kg=59.0,
            pa_sistolica=116,
            pa_diastolica=72,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Paciente chegou cabisbaixa. Refere que passou as últimas semanas "
                "praticamente sem sair de casa. Parou de responder mensagens "
                "de amigas. Marido viajou a trabalho por 15 dias e ela ficou "
                "sozinha. Chora todo dia, sem motivo claro. Disse que sente "
                "que não vai dar conta de cuidar do bebê. "
                "Perda de peso apesar de estar em período de ganho esperado."
            ),
            faixa_risco="LARANJA",
            score_geral=65,
            resumo_ia=(
                "Paciente apresenta indicadores moderados de depressão perinatal "
                "e isolamento social. Perda de peso atípica para o período "
                "gestacional reforça o quadro. Encaminhamento para acompanhamento "
                "psicológico recomendado."
            ),
            encaminhamentos=["PSICOLOGIA", "ASSISTENCIA_SOCIAL"],
            indicadores=[
                {
                    "tipo": "DEPRESSAO",
                    "nivel": "MODERADO",
                    "evidencias": [
                        "choro diário sem motivo aparente",
                        "isolamento em casa por semanas",
                        "sentimento de incapacidade para cuidar do bebê",
                    ],
                    "recomendacao": "Encaminhamento para acompanhamento psicológico",
                },
                {
                    "tipo": "ISOLAMENTO_SOCIAL",
                    "nivel": "MODERADO",
                    "evidencias": [
                        "parou de responder amigas",
                        "ficou sozinha por 15 dias",
                        "não sai de casa",
                    ],
                    "recomendacao": "Avaliar e fortalecer rede de apoio",
                },
            ],
        ),
    ]

    for c in consultas:
        inserir_consulta(conn, paciente_id, enfermeiro_id, medico_id, **c)


# -------------------------------------------------------
# EXECUÇÃO
# -------------------------------------------------------


def main():
    print("\n=== CASF — Seed de Histórico ===\n")

    with engine.begin() as conn:
        enfermeiro_id = buscar_profissional_id(conn, "enfermeiro@sfha.dev")
        medico_id = buscar_profissional_id(conn, "medico@sfha.dev")

        if not enfermeiro_id or not medico_id:
            raise RuntimeError(
                "Usuários não encontrados. Execute seed.py antes de seed_historico.py."
            )

        ana_id = buscar_paciente_id(conn, CPF_ANA)
        maria_id = buscar_paciente_id(conn, CPF_MARIA)
        julia_id = buscar_paciente_id(conn, CPF_JULIA)

        if not all([ana_id, maria_id, julia_id]):
            raise RuntimeError(
                "Pacientes não encontradas. Execute seed.py antes de seed_historico.py."
            )

        seed_ana(conn, ana_id, enfermeiro_id, medico_id)
        seed_maria(conn, maria_id, enfermeiro_id, medico_id)
        seed_julia(conn, julia_id, enfermeiro_id, medico_id)

    print("\n[OK] Historico gerado com sucesso.")
    print("\nPacientes disponiveis para teste:")
    print(
        "  Ana Silva      - caso 3: ginecologica sem problemas   (VERDE  > VERDE  > VERDE)"
    )
    print(
        "  Maria Oliveira - caso 2: violencia domestica          (AMARELO > LARANJA > VERMELHO)"
    )
    print(
        "  Julia Santos   - caso 1: pre-natal depressao perinatal (VERDE  > AMARELO > LARANJA)"
    )
    print(
        "\nA proxima consulta de cada paciente tera historico rico para a LLM processar.\n"
    )


if __name__ == "__main__":
    main()
