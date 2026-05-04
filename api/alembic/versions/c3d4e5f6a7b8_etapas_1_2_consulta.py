"""etapas 1 e 2 consulta simplificada

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-01 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE consultas_identidade ADD COLUMN IF NOT EXISTS dum DATE")
    op.execute("ALTER TABLE consultas_identidade ADD COLUMN IF NOT EXISTS ig_semanas SMALLINT")
    op.execute("ALTER TABLE consultas_identidade ADD COLUMN IF NOT EXISTS ig_dias SMALLINT")
    op.execute(
        "ALTER TABLE consultas_identidade ADD COLUMN IF NOT EXISTS triagem_concluida BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE consultas_identidade ADD COLUMN IF NOT EXISTS triagem_concluida_em TIMESTAMPTZ"
    )
    op.execute("ALTER TABLE consultas_identidade ADD COLUMN IF NOT EXISTS medico_id UUID")
    op.execute("ALTER TABLE consultas_identidade ADD COLUMN IF NOT EXISTS assumida_em TIMESTAMPTZ")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS consulta_triagem (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta UUID NOT NULL UNIQUE,
            peso_kg NUMERIC(5,2) NOT NULL,
            pa_sistolica SMALLINT NOT NULL,
            pa_diastolica SMALLINT NOT NULL,
            registrado_por UUID NOT NULL,
            registrado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS consulta_relato (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta UUID NOT NULL UNIQUE,
            relato_texto TEXT,
            parecer_medico TEXT,
            registrado_por UUID NOT NULL,
            registrado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS consulta_audio (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta UUID NOT NULL,
            transcricao TEXT,
            status_processamento VARCHAR NOT NULL DEFAULT 'AGUARDANDO',
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deletar_em TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS consulta_resultado (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_consulta UUID NOT NULL UNIQUE,
            score_geral SMALLINT NOT NULL,
            faixa_risco VARCHAR NOT NULL,
            indicadores JSONB NOT NULL,
            resumo_ia TEXT,
            calculado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            confirmado BOOLEAN NOT NULL DEFAULT FALSE,
            confirmado_em TIMESTAMPTZ
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS consulta_resultado")
    op.execute("DROP TABLE IF EXISTS consulta_audio")
    op.execute("DROP TABLE IF EXISTS consulta_relato")
    op.execute("DROP TABLE IF EXISTS consulta_triagem")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS assumida_em")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS medico_id")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS triagem_concluida_em")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS triagem_concluida")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS ig_dias")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS ig_semanas")
