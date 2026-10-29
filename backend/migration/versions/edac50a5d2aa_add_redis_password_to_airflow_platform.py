# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""add redis_password to airflow platform

Revision ID: edac50a5d2aa
Revises: 7c78fa71be7a
Create Date: 2026-10-29 18:50:57.123200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'edac50a5d2aa'
down_revision: Union[str, Sequence[str], None] = '7c78fa71be7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by adding redis_password column to mw_airflow_platform."""
    op.add_column(
        'mw_airflow_platform',
        sa.Column('redis_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=sa.text("''"))
    )


def downgrade() -> None:
    """Downgrade schema by dropping redis_password column from mw_airflow_platform."""
    op.drop_column('mw_airflow_platform', 'redis_password')

