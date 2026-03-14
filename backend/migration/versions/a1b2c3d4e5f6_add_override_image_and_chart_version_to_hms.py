# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+
"""add_override_image_and_chart_version_to_hms

Revision ID: a1b2c3d4e5f6
Revises: 95a12ecbc5a1
Create Date: 2026-03-14 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "95a12ecbc5a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add override_image and chart_version columns to mw_hive_metastore_platform."""
    op.add_column(
        "mw_hive_metastore_platform",
        sa.Column("chart_version", sa.String(), nullable=False, server_default="latest"),
    )
    op.add_column(
        "mw_hive_metastore_platform",
        sa.Column("override_image", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Remove override_image and chart_version columns from mw_hive_metastore_platform."""
    op.drop_column("mw_hive_metastore_platform", "override_image")
    op.drop_column("mw_hive_metastore_platform", "chart_version")
