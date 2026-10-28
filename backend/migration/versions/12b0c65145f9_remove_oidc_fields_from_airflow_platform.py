# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""remove oidc fields from airflow platform

Revision ID: 12b0c65145f9
Revises: c7a18f2d5e93
Create Date: 2026-10-28 21:52:08.066838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '12b0c65145f9'
down_revision: Union[str, Sequence[str], None] = 'c7a18f2d5e93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('mw_airflow_platform', 'oidc_enabled')
    op.drop_column('mw_airflow_platform', 'oidc_client_secret')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('mw_airflow_platform', sa.Column('oidc_client_secret', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=sa.text("''")))
    op.add_column('mw_airflow_platform', sa.Column('oidc_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
