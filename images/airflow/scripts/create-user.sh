#!/bin/bash
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+
#
# Creates or resets the Airflow admin user.
# Reads credentials from environment variables.
# Designed for use as the createUserJob command in the Helm chart.

set -e

USERNAME="${AIRFLOW_USER:-admin}"
PASSWORD="${AIRFLOW_PASSWORD:?AIRFLOW_PASSWORD environment variable is required}"
EMAIL="${AIRFLOW_EMAIL:-admin@example.com}"
FIRSTNAME="${AIRFLOW_FIRSTNAME:-admin}"
LASTNAME="${AIRFLOW_LASTNAME:-user}"
ROLE="${AIRFLOW_ROLE:-Admin}"

# Create user if not exists (fails silently if already present)
airflow users create \
    -u "$USERNAME" \
    -p "$PASSWORD" \
    -e "$EMAIL" \
    -f "$FIRSTNAME" \
    -l "$LASTNAME" \
    -r "$ROLE" 2>/dev/null || true

# Reset password to ensure it matches the desired value
exec airflow users reset-password \
    -u "$USERNAME" \
    -p "$PASSWORD"
