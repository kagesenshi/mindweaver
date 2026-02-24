# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio


def run_async(coro):
    """Utility to run async coroutines in a sync context."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.create_task(coro)
    else:
        return loop.run_until_complete(coro)
