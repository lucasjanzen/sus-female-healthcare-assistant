"""adicionar foreign keys nas tabelas de consulta

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-05-19 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_consultas_identidade_paciente_id",
        "consultas_identidade", "pacientes",
        ["paciente_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_consultas_identidade_medico_id",
        "consultas_identidade", "usuarios",
        ["medico_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_consultas_identidade_profissional_id",
        "consultas_identidade", "usuarios",
        ["profissional_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_consulta_triagem_id_consulta",
        "consulta_triagem", "consultas_identidade",
        ["id_consulta"], ["id_consulta"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_consulta_triagem_registrado_por",
        "consulta_triagem", "usuarios",
        ["registrado_por"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_consulta_relato_id_consulta",
        "consulta_relato", "consultas_identidade",
        ["id_consulta"], ["id_consulta"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_consulta_relato_registrado_por",
        "consulta_relato", "usuarios",
        ["registrado_por"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_consulta_resultado_id_consulta",
        "consulta_resultado", "consultas_identidade",
        ["id_consulta"], ["id_consulta"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_consulta_resultado_id_consulta", "consulta_resultado", type_="foreignkey")
    op.drop_constraint("fk_consulta_relato_registrado_por", "consulta_relato", type_="foreignkey")
    op.drop_constraint("fk_consulta_relato_id_consulta", "consulta_relato", type_="foreignkey")
    op.drop_constraint("fk_consulta_triagem_registrado_por", "consulta_triagem", type_="foreignkey")
    op.drop_constraint("fk_consulta_triagem_id_consulta", "consulta_triagem", type_="foreignkey")
    op.drop_constraint("fk_consultas_identidade_profissional_id", "consultas_identidade", type_="foreignkey")
    op.drop_constraint("fk_consultas_identidade_medico_id", "consultas_identidade", type_="foreignkey")
    op.drop_constraint("fk_consultas_identidade_paciente_id", "consultas_identidade", type_="foreignkey")
