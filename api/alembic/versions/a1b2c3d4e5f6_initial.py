"""initial

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            nome        VARCHAR     NOT NULL,
            email       VARCHAR     NOT NULL UNIQUE,
            senha_hash  VARCHAR     NOT NULL,
            role        VARCHAR     NOT NULL,
            ativo       BOOLEAN     NOT NULL DEFAULT TRUE,
            criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            cpf_hash            VARCHAR     NOT NULL UNIQUE,
            cns                 VARCHAR     UNIQUE,
            nome                VARCHAR     NOT NULL,
            data_nascimento     DATE        NOT NULL,
            telefone            VARCHAR     NOT NULL,
            email               VARCHAR,
            estado_civil        VARCHAR     NOT NULL,
            possui_filhos       BOOLEAN     NOT NULL DEFAULT FALSE,
            quantidade_filhos   SMALLINT,
            altura_cm           SMALLINT    NOT NULL,
            endereco            VARCHAR,
            ativo               BOOLEAN     NOT NULL DEFAULT TRUE,
            criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS pacientes_log (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            paciente_id     UUID        NOT NULL,
            atualizado_por  UUID        NOT NULL,
            atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS consultas_identidade (
            id_consulta             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            paciente_id             UUID        NOT NULL,
            profissional_id         UUID        NOT NULL,
            ubs_id                  UUID,
            estado_id               VARCHAR,
            tipo_consulta           VARCHAR     NOT NULL,
            status                  VARCHAR     NOT NULL DEFAULT 'ABERTA',
            dum                     DATE,
            ig_semanas              SMALLINT,
            ig_dias                 SMALLINT,
            triagem_concluida       BOOLEAN     NOT NULL DEFAULT FALSE,
            triagem_concluida_em    TIMESTAMPTZ,
            medico_id               UUID,
            assumida_em             TIMESTAMPTZ,
            aberta_em               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            encerrada_em            TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS consulta_triagem (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta     UUID        NOT NULL UNIQUE,
            peso_kg         NUMERIC(5,2) NOT NULL,
            pa_sistolica    SMALLINT    NOT NULL,
            pa_diastolica   SMALLINT    NOT NULL,
            registrado_por  UUID        NOT NULL,
            registrado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS consulta_relato (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta     UUID        NOT NULL UNIQUE,
            relato_texto    TEXT,
            parecer_medico  TEXT,
            registrado_por  UUID        NOT NULL,
            registrado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS consulta_audio (
            id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta             UUID        NOT NULL,
            transcricao             TEXT,
            status_processamento    VARCHAR     NOT NULL DEFAULT 'AGUARDANDO',
            criado_em               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deletar_em              TIMESTAMPTZ NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS consulta_resultado (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta     UUID        NOT NULL UNIQUE,
            score_geral     SMALLINT    NOT NULL,
            faixa_risco     VARCHAR     NOT NULL,
            indicadores     JSONB       NOT NULL,
            resumo_ia       TEXT,
            calculado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            confirmado      BOOLEAN     NOT NULL DEFAULT FALSE,
            confirmado_em   TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS consulta_encerramento (
            id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta             UUID        NOT NULL UNIQUE,
            conduta                 TEXT        NOT NULL,
            encaminhamentos         JSONB,
            data_proximo_retorno    DATE        NOT NULL,
            observacoes             TEXT,
            encerrado_por           UUID        NOT NULL,
            encerrado_em            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_acessos (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            profissional_id UUID        NOT NULL,
            unidade_id      UUID,
            cpf_hash        VARCHAR,
            tipo_acesso     VARCHAR     NOT NULL,
            justificativa   TEXT
        )
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION bloquear_edicao_auditoria()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Registros de auditoria não podem ser alterados ou removidos.';
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS audit_imutavel ON audit_acessos
    """)

    op.execute("""
        CREATE TRIGGER audit_imutavel
        BEFORE UPDATE OR DELETE ON audit_acessos
        FOR EACH ROW EXECUTE FUNCTION bloquear_edicao_auditoria()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_imutavel ON audit_acessos")
    op.execute("DROP FUNCTION IF EXISTS bloquear_edicao_auditoria")
    op.execute("DROP TABLE IF EXISTS audit_acessos")
    op.execute("DROP TABLE IF EXISTS consulta_encerramento")
    op.execute("DROP TABLE IF EXISTS consulta_resultado")
    op.execute("DROP TABLE IF EXISTS consulta_audio")
    op.execute("DROP TABLE IF EXISTS consulta_relato")
    op.execute("DROP TABLE IF EXISTS consulta_triagem")
    op.execute("DROP TABLE IF EXISTS consultas_identidade")
    op.execute("DROP TABLE IF EXISTS pacientes_log")
    op.execute("DROP TABLE IF EXISTS pacientes")
    op.execute("DROP TABLE IF EXISTS usuarios")
