#!/bin/bash
set -e

HADOOP_VERSION=3.4.1
METASTORE_VERSION=4.2.0
POSTGRES_JDBC_VERSION=42.7.2

mkdir -p downloads
cd downloads

echo "Downloading Hadoop $HADOOP_VERSION..."
if [ ! -f "hadoop-${HADOOP_VERSION}.tar.gz" ]; then
    wget -q --show-progress --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz"
else
    echo "hadoop-${HADOOP_VERSION}.tar.gz already exists."
fi

echo "Downloading Hive Standalone Metastore $METASTORE_VERSION..."
if [ ! -f "hive-standalone-metastore-${METASTORE_VERSION}-bin.tar.gz" ]; then
    wget -q --show-progress --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 "https://dlcdn.apache.org/hive/hive-standalone-metastore-${METASTORE_VERSION}/hive-standalone-metastore-${METASTORE_VERSION}-bin.tar.gz"
else
    echo "hive-standalone-metastore-${METASTORE_VERSION}-bin.tar.gz already exists."
fi

echo "Downloading PostgreSQL JDBC Driver $POSTGRES_JDBC_VERSION..."
if [ ! -f "postgresql-${POSTGRES_JDBC_VERSION}.jar" ]; then
    wget -q --show-progress --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 "https://jdbc.postgresql.org/download/postgresql-${POSTGRES_JDBC_VERSION}.jar"
else
    echo "postgresql-${POSTGRES_JDBC_VERSION}.jar already exists."
fi

echo "Done downloading components."
