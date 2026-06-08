# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""add solr additional credentials

Revision ID: e1a2b3c4d5e6
Revises: d092604db5a9
Create Date: 2026-06-09 05:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'd092604db5a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add k8s_oper_password and solr_user_password columns to mw_solr_platform_state."""
    op.add_column('mw_solr_platform_state', sa.Column('k8s_oper_password', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('mw_solr_platform_state', sa.Column('solr_user_password', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Remove k8s_oper_password and solr_user_password columns from mw_solr_platform_state."""
    op.drop_column('mw_solr_platform_state', 'solr_user_password')
    op.drop_column('mw_solr_platform_state', 'k8s_oper_password')
