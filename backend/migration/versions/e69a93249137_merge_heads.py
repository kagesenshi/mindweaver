"""merge heads

Revision ID: e69a93249137
Revises: 8685321b5a3e, e1a2b3c4d5e6
Create Date: 2026-06-10 07:07:27.673121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'e69a93249137'
down_revision: Union[str, Sequence[str], None] = ('8685321b5a3e', 'e1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
