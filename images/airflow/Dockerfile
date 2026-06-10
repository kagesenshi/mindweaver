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

COPY scripts/create-user.sh /opt/airflow/scripts/create-user.sh
RUN chmod +x /opt/airflow/scripts/create-user.sh

USER airflow
