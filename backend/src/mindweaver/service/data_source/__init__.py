# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import DataSourceService, DataSource
import mindweaver.service.data_source.views

router = DataSourceService.router()

__all__ = ["DataSourceService", "DataSource", "router"]
