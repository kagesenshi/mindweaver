# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from pydantic_settings import BaseSettings, SettingsConfigDict


class ReleaserSettings(BaseSettings):
    """Configuration settings for MindWeaver Releaser."""

    registry: str = "ghcr.io/kagesenshi/mindweaver"
    chart_registry: str = "oci://ghcr.io/kagesenshi/mindweaver/charts"

    model_config = SettingsConfigDict(
        env_prefix="MW_",
        case_sensitive=False,
    )


settings = ReleaserSettings()
