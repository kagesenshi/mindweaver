FROM apachesuperset.docker.scarf.sh/apache/superset:5.0.0 as base

USER root
RUN apt-get update && \
    apt install -y build-essential python3-dev libldap2-dev libsasl2-dev libssl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN uv pip install psycopg2-binary python-ldap
USER superset
