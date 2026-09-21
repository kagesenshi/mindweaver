# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""add doris platform and state models

Revision ID: e8b19a823c14
Revises: 2775767ca20d
Create Date: 2026-09-21 10:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'e8b19a823c14'
down_revision: Union[str, Sequence[str], None] = '2775767ca20d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'mw_doris_platform',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('fe_replicas', sa.Integer(), nullable=False),
        sa.Column('be_replicas', sa.Integer(), nullable=False),
        sa.Column('fe_storage_size', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('be_storage_size', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('fe_cpu_request', sa.Float(), nullable=False),
        sa.Column('fe_cpu_limit', sa.Float(), nullable=False),
        sa.Column('fe_mem_request', sa.Float(), nullable=False),
        sa.Column('fe_mem_limit', sa.Float(), nullable=False),
        sa.Column('be_cpu_request', sa.Float(), nullable=False),
        sa.Column('be_cpu_limit', sa.Float(), nullable=False),
        sa.Column('be_mem_request', sa.Float(), nullable=False),
        sa.Column('be_mem_limit', sa.Float(), nullable=False),
        sa.Column('admin_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['mw_project.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_mw_doris_platform_project_id'), 'mw_doris_platform', ['project_id'], unique=False)

    op.create_table(
        'mw_doris_platform_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('node_ports', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('cluster_nodes', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('extra_data', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('query_uri', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('fe_http_uri', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('admin_user', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('admin_password', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(['platform_id'], ['mw_doris_platform.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mw_doris_platform_state_platform_id'), 'mw_doris_platform_state', ['platform_id'], unique=False)
    op.create_index(op.f('ix_mw_doris_platform_state_status'), 'mw_doris_platform_state', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mw_doris_platform_state_status'), table_name='mw_doris_platform_state')
    op.drop_index(op.f('ix_mw_doris_platform_state_platform_id'), table_name='mw_doris_platform_state')
    op.drop_table('mw_doris_platform_state')
    op.drop_index(op.f('ix_mw_doris_platform_project_id'), table_name='mw_doris_platform')
    op.drop_table('mw_doris_platform')
