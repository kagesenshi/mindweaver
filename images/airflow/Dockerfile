# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM apache/airflow:3.2.2 AS base

USER root
RUN apt-get update && \
    apt install -y build-essential python3-dev libldap2-dev libsasl2-dev libssl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN uv pip install --system \
    psycopg2-binary python-ldap Authlib cryptography \
    trino pymysql elasticsearch-dbapi oracledb asyncpg pyhive impyla \
    apache-airflow-providers-amazon

# Patch: add missing ldap.filter import for LDAP auth (PR #68226)
# auth_user_ldap uses ldap.filter.escape_filter_chars but only imports ldap
RUN FILE=$(python -c "import airflow.providers.fab.auth_manager.security_manager.override; print(airflow.providers.fab.auth_manager.security_manager.override.__file__)") && \
    sed -i 's/^\([[:space:]]*\)import ldap$/\1import ldap\n\1import ldap.filter/' "$FILE"

COPY mindweaver_airflow_auth/ /opt/airflow/mindweaver_airflow_auth/
ENV PYTHONPATH=/opt/airflow

COPY scripts/create-user.sh /opt/airflow/scripts/create-user.sh
RUN chmod +x /opt/airflow/scripts/create-user.sh

USER airflow
