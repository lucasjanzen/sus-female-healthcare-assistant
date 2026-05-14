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
"""

import hashlib
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
            assumida_em, aberta_em, encerrada_em
        ) VALUES (
            :id, :pid, :prof, :med, :ubs,
            :estado, :tipo, 'ENCERRADA',
            :dum, :ig_s, :ig_d,
            true, :aberta,
            :aberta, :aberta, :aberta
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
    import json

    indicadores = _indicadores_por_faixa(faixa_risco)
    conn.execute(
        text("""
        INSERT INTO consulta_resultado (
            id, id_consulta, score_geral, faixa_risco,
            indicadores, resumo_ia,
            calculado_em, confirmado, confirmado_em
        ) VALUES (
            :id, :ic, :score, :faixa,
            CAST(:ind AS jsonb), :resumo,
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


def _indicadores_por_faixa(faixa: str) -> list[dict]:
    base = {
        "VERDE": [],
        "AMARELO": [
            {
                "tipo": "ANSIEDADE",
                "nivel": "BAIXO",
                "evidencias": ["relatou preocupação com o trabalho"],
                "recomendacao": "Monitorar nas próximas consultas",
            }
        ],
        "LARANJA": [
            {
                "tipo": "DEPRESSAO",
                "nivel": "MODERADO",
                "evidencias": ["choro frequente", "relato de tristeza persistente"],
                "recomendacao": "Encaminhamento para acompanhamento psicológico",
            },
            {
                "tipo": "ISOLAMENTO_SOCIAL",
                "nivel": "MODERADO",
                "evidencias": ["mencionou estar se afastando de amigos"],
                "recomendacao": "Avaliar rede de apoio",
            },
        ],
        "VERMELHO": [
            {
                "tipo": "DEPRESSAO",
                "nivel": "ALTO",
                "evidencias": [
                    "sem vontade de sair da cama",
                    "pensamentos negativos frequentes",
                ],
                "recomendacao": "Encaminhamento urgente para CAPS",
            },
            {
                "tipo": "VIOLENCIA_DOMESTICA",
                "nivel": "ALTO",
                "evidencias": [
                    "hesitação ao falar do parceiro",
                    "relatou medo em casa",
                ],
                "recomendacao": "Acionar protocolo de violência doméstica",
            },
        ],
    }
    return base.get(faixa, [])


# -------------------------------------------------------
# DADOS DE TESTE POR PACIENTE
# -------------------------------------------------------


def seed_ana(conn, paciente_id, enfermeiro_id, medico_id):
    """
    Ana Silva — grávida, pré-natal, histórico de risco crescente.
    Contexto ideal para testar detecção de depressão perinatal.
    """
    print("  Ana Silva (pré-natal, risco crescente):")
    dum = data_passada(140)  # ~20 semanas atrás

    consultas = [
        dict(
            dias_atras=120,
            peso_kg=62.5,
            pa_sistolica=110,
            pa_diastolica=70,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Paciente refere estar bem de modo geral. Pequenas náuseas "
                "no primeiro trimestre já cederam. Dormindo bem. Marido presente."
            ),
            faixa_risco="VERDE",
            score_geral=10,
            resumo_ia="Paciente sem indicadores de risco nesta consulta.",
            encaminhamentos=[],
        ),
        dict(
            dias_atras=90,
            peso_kg=64.0,
            pa_sistolica=115,
            pa_diastolica=72,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Paciente relata cansaço intenso e dificuldade para dormir. "
                "Mencionou preocupação com as finanças da família após redução "
                "de renda do marido. Chorou durante a consulta."
            ),
            faixa_risco="AMARELO",
            score_geral=35,
            resumo_ia=(
                "Paciente apresenta sinais iniciais de sobrecarga emocional "
                "associados a estressor socioeconômico. Recomenda-se atenção "
                "nas próximas consultas."
            ),
            encaminhamentos=["ASSISTENCIA_SOCIAL"],
        ),
        dict(
            dias_atras=60,
            peso_kg=65.2,
            pa_sistolica=118,
            pa_diastolica=75,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Paciente verbaliza sentir-se sozinha. Marido passou a trabalhar "
                "fora e está ausente durante a semana. Relata choro sem motivo "
                "aparente quase todos os dias. Diz não sentir vontade de sair "
                "de casa nem de falar com amigas."
            ),
            faixa_risco="LARANJA",
            score_geral=58,
            resumo_ia=(
                "Paciente apresenta indicadores moderados de depressão perinatal "
                "e isolamento social. Ausência de rede de apoio imediata é fator "
                "de risco relevante. Recomenda-se encaminhamento para "
                "acompanhamento psicológico e avaliação do suporte social."
            ),
            encaminhamentos=["PSICOLOGIA", "ASSISTENCIA_SOCIAL"],
        ),
    ]

    for c in consultas:
        inserir_consulta(conn, paciente_id, enfermeiro_id, medico_id, **c)


def seed_maria(conn, paciente_id, enfermeiro_id, medico_id):
    """
    Maria Oliveira — consultas ginecológicas, histórico de ansiedade.
    Contexto para testar detecção de ansiedade sem contexto gestacional.
    """
    print("  Maria Oliveira (ginecológica, ansiedade):")

    consultas = [
        dict(
            dias_atras=180,
            peso_kg=68.0,
            pa_sistolica=120,
            pa_diastolica=78,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Paciente sem queixas específicas. Veio para consulta de rotina. "
                "Relata estar bem no trabalho e na vida pessoal."
            ),
            faixa_risco="VERDE",
            score_geral=8,
            resumo_ia="Consulta de rotina sem indicadores de risco.",
            encaminhamentos=[],
        ),
        dict(
            dias_atras=90,
            peso_kg=69.5,
            pa_sistolica=128,
            pa_diastolica=82,
            dum=None,
            tipo_consulta="GINECOLOGICA",
            relato_texto=(
                "Paciente relata dificuldade para dormir há 3 semanas. "
                "Nervosa com situação no emprego — possível demissão. "
                "Coração acelerado com frequência, sensação de sufocamento. "
                "Não consegue parar de pensar nos problemas."
            ),
            faixa_risco="LARANJA",
            score_geral=62,
            resumo_ia=(
                "Paciente apresenta sintomas compatíveis com ansiedade de "
                "intensidade moderada a elevada, associados a estressor "
                "ocupacional. Pressão arterial levemente elevada pode estar "
                "relacionada ao quadro ansioso. Recomenda-se avaliação "
                "psicológica e acompanhamento da PA."
            ),
            encaminhamentos=["PSICOLOGIA"],
        ),
    ]

    for c in consultas:
        inserir_consulta(conn, paciente_id, enfermeiro_id, medico_id, **c)


def seed_julia(conn, paciente_id, enfermeiro_id, medico_id):
    """
    Julia Santos — pré-natal, histórico de risco crítico.
    Contexto para testar detecção de violência doméstica + depressão.
    """
    print("  Julia Santos (pré-natal, risco crítico):")
    dum = data_passada(200)  # ~28 semanas atrás

    consultas = [
        dict(
            dias_atras=150,
            peso_kg=55.0,
            pa_sistolica=105,
            pa_diastolica=65,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Primeira consulta de pré-natal. Paciente jovem, gestação não "
                "planejada. Relata apoio do companheiro. Sem queixas relevantes."
            ),
            faixa_risco="VERDE",
            score_geral=12,
            resumo_ia="Primeira consulta sem indicadores de risco.",
            encaminhamentos=[],
        ),
        dict(
            dias_atras=90,
            peso_kg=54.2,
            pa_sistolica=108,
            pa_diastolica=68,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Paciente demonstrou hesitação ao responder sobre a relação com "
                "o companheiro. Relatou que ele 'às vezes perde a paciência' mas "
                "não quis detalhar. Apresentou-se cabisbaixa durante toda a "
                "consulta. Peso abaixo do esperado para a IG."
            ),
            faixa_risco="LARANJA",
            score_geral=65,
            resumo_ia=(
                "Paciente apresenta comportamento sugestivo de situação de "
                "violência doméstica. Hesitação ao falar do companheiro e "
                "resposta evasiva são sinais de alerta. Perda de peso para a IG "
                "também é preocupante. Recomenda-se abordagem individualizada "
                "e encaminhamento para serviço social."
            ),
            encaminhamentos=["SERVICO_SOCIAL", "CVR"],
        ),
        dict(
            dias_atras=30,
            peso_kg=53.8,
            pa_sistolica=112,
            pa_diastolica=70,
            dum=dum,
            tipo_consulta="PRENATAL",
            relato_texto=(
                "Paciente chegou à consulta com hematoma visível no braço. "
                "Ao ser questionada, atribuiu a uma queda mas mostrou-se "
                "visivelmente nervosa. Relatou não dormir bem, medo constante "
                "e que 'as coisas em casa estão difíceis'. Não quis elaborar "
                "mais. Peso continua abaixo do esperado. Choro durante a consulta."
            ),
            faixa_risco="VERMELHO",
            score_geral=85,
            resumo_ia=(
                "Paciente apresenta indicadores críticos de violência doméstica "
                "e depressão. Hematoma com justificativa inconsistente, medo "
                "verbalizado e perda de peso progressiva configuram situação de "
                "alto risco. Protocolo de violência doméstica deve ser acionado "
                "imediatamente. Encaminhamento urgente para CVR e CAPS."
            ),
            encaminhamentos=["CVR", "CAPS", "DELEGACIA_MULHER"],
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
    print("  Ana Silva      - pre-natal, risco crescente (VERDE > AMARELO > LARANJA)")
    print("  Maria Oliveira - ginecologica, ansiedade    (VERDE > LARANJA)")
    print("  Julia Santos   - pre-natal, risco critico  (VERDE > LARANJA > VERMELHO)")
    print(
        "\nA próxima consulta de cada paciente terá histórico rico para a LLM processar.\n"
    )


if __name__ == "__main__":
    main()
