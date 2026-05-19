"""adicionar observacao_encaminhamento em consultas_identidade

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-05-19 00:00:01.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "consultas_identidade",
        sa.Column("observacao_encaminhamento", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("consultas_identidade", "observacao_encaminhamento")
