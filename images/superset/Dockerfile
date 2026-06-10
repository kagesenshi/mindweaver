# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM apachesuperset.docker.scarf.sh/apache/superset:6.1.0 AS base

USER root
RUN apt-get update && \
    apt install -y build-essential python3-dev libldap2-dev libsasl2-dev libssl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN uv pip install psycopg2-binary python-ldap Authlib cryptography trino ibm-db-sa pymysql elasticsearch-dbapi oracledb asyncpg pyhive impyla
USER superset
