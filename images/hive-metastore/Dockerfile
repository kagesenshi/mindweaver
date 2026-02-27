FROM apache/hive:standalone-metastore-4.2.0

ENV POSTGRES_JDBC_VERSION=42.7.2

COPY downloads/postgresql-${POSTGRES_JDBC_VERSION}.jar ${HIVE_HOME}/lib/postgresql-jdbc.jar
