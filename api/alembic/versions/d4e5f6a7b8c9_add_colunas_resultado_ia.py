"""add colunas resultado ia em consulta_resultado

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE consulta_resultado ADD COLUMN IF NOT EXISTS sentimento_voz JSONB")
    op.execute("ALTER TABLE consulta_resultado ADD COLUMN IF NOT EXISTS sumario_estruturado JSONB")
    op.execute("ALTER TABLE consulta_resultado ADD COLUMN IF NOT EXISTS texto_clinico TEXT")
    op.execute("ALTER TABLE consulta_resultado ADD COLUMN IF NOT EXISTS fontes_utilizadas JSONB")
    op.execute("ALTER TABLE consulta_resultado ADD COLUMN IF NOT EXISTS tokens_utilizados INTEGER")


def downgrade() -> None:
    op.execute("ALTER TABLE consulta_resultado DROP COLUMN IF EXISTS tokens_utilizados")
    op.execute("ALTER TABLE consulta_resultado DROP COLUMN IF EXISTS fontes_utilizadas")
    op.execute("ALTER TABLE consulta_resultado DROP COLUMN IF EXISTS texto_clinico")
    op.execute("ALTER TABLE consulta_resultado DROP COLUMN IF EXISTS sumario_estruturado")
    op.execute("ALTER TABLE consulta_resultado DROP COLUMN IF EXISTS sentimento_voz")
