# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""add dependency tracker model

Revision ID: c7a18f2d5e93
Revises: bedf64fc5404
Create Date: 2026-10-26 21:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = 'c7a18f2d5e93'
down_revision: Union[str, Sequence[str], None] = 'bedf64fc5404'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'mw_dependency_tracker',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sqlalchemy_utils.types.uuid.UUIDType(binary=False), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
        sa.Column('service_uuid', sa.String(length=64), nullable=False),
        sa.Column('service_name', sa.String(length=128), nullable=False),
        sa.Column('service_type', sa.String(length=64), nullable=False),
        sa.Column('dependency_uuid', sa.String(length=64), nullable=False),
        sa.Column('dependency_name', sa.String(length=128), nullable=False),
        sa.Column('dependency_type', sa.String(length=64), nullable=False),
        sa.Column('relationship', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_mw_dependency_tracker_uuid'), 'mw_dependency_tracker', ['uuid'], unique=True)
    op.create_index(op.f('ix_mw_dependency_tracker_service_uuid'), 'mw_dependency_tracker', ['service_uuid'], unique=False)
    op.create_index(op.f('ix_mw_dependency_tracker_service_name'), 'mw_dependency_tracker', ['service_name'], unique=False)
    op.create_index(op.f('ix_mw_dependency_tracker_service_type'), 'mw_dependency_tracker', ['service_type'], unique=False)
    op.create_index(op.f('ix_mw_dependency_tracker_dependency_uuid'), 'mw_dependency_tracker', ['dependency_uuid'], unique=False)
    op.create_index(op.f('ix_mw_dependency_tracker_dependency_name'), 'mw_dependency_tracker', ['dependency_name'], unique=False)
    op.create_index(op.f('ix_mw_dependency_tracker_dependency_type'), 'mw_dependency_tracker', ['dependency_type'], unique=False)
    op.create_index(op.f('ix_mw_dependency_tracker_relationship'), 'mw_dependency_tracker', ['relationship'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mw_dependency_tracker_relationship'), table_name='mw_dependency_tracker')
    op.drop_index(op.f('ix_mw_dependency_tracker_dependency_type'), table_name='mw_dependency_tracker')
    op.drop_index(op.f('ix_mw_dependency_tracker_dependency_name'), table_name='mw_dependency_tracker')
    op.drop_index(op.f('ix_mw_dependency_tracker_dependency_uuid'), table_name='mw_dependency_tracker')
    op.drop_index(op.f('ix_mw_dependency_tracker_service_type'), table_name='mw_dependency_tracker')
    op.drop_index(op.f('ix_mw_dependency_tracker_service_name'), table_name='mw_dependency_tracker')
    op.drop_index(op.f('ix_mw_dependency_tracker_service_uuid'), table_name='mw_dependency_tracker')
    op.drop_index(op.f('ix_mw_dependency_tracker_uuid'), table_name='mw_dependency_tracker')
    op.drop_table('mw_dependency_tracker')
