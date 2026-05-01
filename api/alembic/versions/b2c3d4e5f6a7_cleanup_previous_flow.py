"""cleanup previous consultation flow

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-01 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS consulta_triagem")
    op.execute("DROP TABLE IF EXISTS consulta_anamnese")
    op.execute("DROP TABLE IF EXISTS consulta_exame_fisico")
    op.execute("DROP TABLE IF EXISTS consulta_exames_lab")
    op.execute("DROP TABLE IF EXISTS consulta_rastreio_psicossocial")
    op.execute("DROP TABLE IF EXISTS consulta_parecer")
    op.execute("DROP TABLE IF EXISTS consulta_encerramento")
    op.execute("DROP TABLE IF EXISTS consulta_tcle_log")
    op.execute("DROP TABLE IF EXISTS consulta_audio")
    op.execute("DROP TABLE IF EXISTS consulta_resultado")

    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS triagem_concluida")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS triagem_concluida_em")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS medico_id")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS assumida_em")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS ig_semanas")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS ig_dias")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS tcle_assinado")
    op.execute("ALTER TABLE consultas_identidade DROP COLUMN IF EXISTS tcle_assinado_em")


def downgrade() -> None:
    pass
