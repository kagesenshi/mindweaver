# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .model import WebSource
from .service import WebSourceService
import mindweaver.datasource_service.web_source.views  # noqa: F401

__all__ = ["WebSource", "WebSourceService"]
