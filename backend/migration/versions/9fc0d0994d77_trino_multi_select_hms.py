"""trino multi-select hms

Revision ID: 9fc0d0994d77
Revises: 14d4f5181f92
Create Date: 2026-03-14 10:44:02.266732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9fc0d0994d77'
down_revision: Union[str, Sequence[str], None] = '14d4f5181f92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mw_trino_platform', sa.Column('hms_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.execute(
        """
        UPDATE mw_trino_platform
        SET hms_ids = CASE 
            WHEN hms_id IS NOT NULL THEN json_build_array(hms_id)
            ELSE '[]'::json
        END
        """
    )
    op.alter_column('mw_trino_platform', 'hms_ids', nullable=False)
    op.drop_constraint('mw_trino_platform_hms_id_fkey', 'mw_trino_platform', type_='foreignkey')
    op.drop_column('mw_trino_platform', 'hms_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('mw_trino_platform', sa.Column('hms_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.execute(
        """
        UPDATE mw_trino_platform
        SET hms_id = CASE
            WHEN json_array_length(hms_ids) > 0 THEN (hms_ids->>0)::integer
            ELSE NULL
        END
        """
    )
    op.create_foreign_key('mw_trino_platform_hms_id_fkey', 'mw_trino_platform', 'mw_hive_metastore_platform', ['hms_id'], ['id'])
    op.drop_column('mw_trino_platform', 'hms_ids')
