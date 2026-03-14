"""trino iceberg hms

Revision ID: bbaba09ce176
Revises: 9fc0d0994d77
Create Date: 2026-03-14 10:50:49.383721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bbaba09ce176'
down_revision: Union[str, Sequence[str], None] = '9fc0d0994d77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mw_trino_platform', sa.Column('hms_iceberg_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.execute("UPDATE mw_trino_platform SET hms_iceberg_ids = '[]'::json")
    op.alter_column('mw_trino_platform', 'hms_iceberg_ids', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('mw_trino_platform', 'hms_iceberg_ids')
