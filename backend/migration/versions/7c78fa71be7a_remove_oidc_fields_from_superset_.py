# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""remove oidc fields from superset platform

Revision ID: 7c78fa71be7a
Revises: 12b0c65145f9
Create Date: 2026-10-28 23:33:36.791403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '7c78fa71be7a'
down_revision: Union[str, Sequence[str], None] = '12b0c65145f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('mw_superset_platform', 'oidc_enabled')
    op.drop_column('mw_superset_platform', 'oidc_client_secret')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('mw_superset_platform', sa.Column('oidc_client_secret', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=sa.text("''")))
    op.add_column('mw_superset_platform', sa.Column('oidc_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
