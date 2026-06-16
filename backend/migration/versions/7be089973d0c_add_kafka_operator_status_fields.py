# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""add kafka operator status fields

Revision ID: 7be089973d0c
Revises: 6b64d26a7c46
Create Date: 2026-06-16 09:52:57.595444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '7be089973d0c'
down_revision: Union[str, Sequence[str], None] = '4006a49ba489'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mw_k8s_cluster_status', sa.Column('kafka_operator_installed', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('mw_k8s_cluster_status', sa.Column('kafka_operator_version', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('mw_k8s_cluster_status', 'kafka_operator_version')
    op.drop_column('mw_k8s_cluster_status', 'kafka_operator_installed')

