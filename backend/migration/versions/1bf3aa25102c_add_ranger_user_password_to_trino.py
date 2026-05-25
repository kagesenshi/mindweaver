# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""add ranger_user_password to trino

Revision ID: 1bf3aa25102c
Revises: 45e95b334192
Create Date: 2026-05-24 09:17:50.184216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '1bf3aa25102c'
down_revision: Union[str, Sequence[str], None] = '45e95b334192'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mw_trino_platform', sa.Column('ranger_user_password', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('mw_trino_platform', 'ranger_user_password')
