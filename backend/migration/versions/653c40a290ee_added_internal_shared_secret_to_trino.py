"""added internal_shared_secret to trino

Revision ID: 653c40a290ee
Revises: df81a3c06832
Create Date: 2026-03-15 09:46:00.199832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '653c40a290ee'
down_revision: Union[str, Sequence[str], None] = 'df81a3c06832'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mw_trino_platform', sa.Column('internal_shared_secret', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('mw_trino_platform', 'internal_shared_secret')
