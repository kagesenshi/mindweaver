# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""update ranger chart version default to 0.1.25

Revision ID: 4d2f2fb255c5
Revises: b8b6e7675687
Create Date: 2026-06-06 10:02:53.221643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '4d2f2fb255c5'
down_revision: Union[str, Sequence[str], None] = 'b8b6e7675687'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE mw_ranger_platform SET chart_version = '0.1.25' WHERE chart_version = 'main'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE mw_ranger_platform SET chart_version = 'main' WHERE chart_version = '0.1.25'")

