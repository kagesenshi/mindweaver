# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .database_source import DatabaseSource, DatabaseSourceService
from .web_source import WebSource, WebSourceService
from .api_source import APISource, APISourceService
from .streaming_source import StreamingSource, StreamingSourceService

db_router = DatabaseSourceService.router()
web_router = WebSourceService.router()
api_router = APISourceService.router()
streaming_router = StreamingSourceService.router()

__all__ = [
    "DatabaseSource",
    "WebSource",
    "APISource",
    "StreamingSource",
    "DatabaseSourceService",
    "WebSourceService",
    "APISourceService",
    "StreamingSourceService",
    "db_router",
    "web_router",
    "api_router",
    "streaming_router",
]
