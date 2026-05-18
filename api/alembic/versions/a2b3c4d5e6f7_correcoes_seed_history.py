"""correcoes: parecer_medico, confirmado, consulta_encerramento

Revision ID: a2b3c4d5e6f7
Revises: 69c4df361ee9
Create Date: 2026-05-18 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "69c4df361ee9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("consulta_relato", sa.Column("parecer_medico", sa.Text(), nullable=True))

    op.add_column(
        "consulta_resultado",
        sa.Column("confirmado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "consulta_resultado",
        sa.Column("confirmado_em", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "consulta_encerramento",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("id_consulta", sa.UUID(), nullable=False),
        sa.Column("conduta", sa.Text(), nullable=False),
        sa.Column("encaminhamentos", sa.JSON(), nullable=True),
        sa.Column("data_proximo_retorno", sa.Date(), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("encerrado_por", sa.UUID(), nullable=False),
        sa.Column(
            "encerrado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_consulta"),
    )


def downgrade() -> None:
    op.drop_table("consulta_encerramento")
    op.drop_column("consulta_resultado", "confirmado_em")
    op.drop_column("consulta_resultado", "confirmado")
    op.drop_column("consulta_relato", "parecer_medico")
