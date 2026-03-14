# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""add_pgbouncer_fields_to_pgsql_platform

Revision ID: 95a12ecbc5a1
Revises: 56e6735ed20e
Create Date: 2026-03-14 11:24:53.134805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision: str = '95a12ecbc5a1'
down_revision: Union[str, Sequence[str], None] = '56e6735ed20e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adds pgbouncer_pool_mode and pgbouncer_pool_size columns to mw_pgsql_platform."""
    op.add_column('mw_pgsql_platform', sa.Column('pgbouncer_pool_mode', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='transaction'))
    op.add_column('mw_pgsql_platform', sa.Column('pgbouncer_pool_size', sa.Integer(), nullable=False, server_default='50'))


def downgrade() -> None:
    """Removes pgbouncer_pool_mode and pgbouncer_pool_size columns from mw_pgsql_platform."""
    op.drop_column('mw_pgsql_platform', 'pgbouncer_pool_size')
    op.drop_column('mw_pgsql_platform', 'pgbouncer_pool_mode')
