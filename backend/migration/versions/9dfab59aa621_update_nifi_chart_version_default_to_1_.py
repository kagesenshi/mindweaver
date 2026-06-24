# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""update nifi chart version default to 1.17.0

Revision ID: 9dfab59aa621
Revises: 6064e87e6331
Create Date: 2026-06-24 21:52:34.846932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '9dfab59aa621'
down_revision: Union[str, Sequence[str], None] = '6064e87e6331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE mw_nifi_platform SET chart_version = '1.17.0' WHERE chart_version = '0.1.0'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE mw_nifi_platform SET chart_version = '0.1.0' WHERE chart_version = '1.17.0'")

