# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Dict, Any

# Global registry to hold service classes by their model's table name
# to avoid circular dependencies during widget inference and validation.
SERVICE_REGISTRY: Dict[str, Any] = {}
