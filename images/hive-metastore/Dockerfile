FROM eclipse-temurin:21-jre

ENV HADOOP_VERSION=3.4.1
ENV METASTORE_VERSION=4.2.0
ENV POSTGRES_JDBC_VERSION=42.7.2

ENV HADOOP_HOME=/opt/hadoop
ENV HIVE_HOME=/opt/hive-metastore

# Set a unified config directory, allowing one volume mount for both Hadoop and Hive configs
ENV HADOOP_CONF_DIR=/opt/conf
ENV HIVE_CONF_DIR=/opt/conf

ENV PATH=$HADOOP_HOME/bin:$HIVE_HOME/bin:$PATH

RUN apt-get update && apt-get install -y bash netcat-traditional && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt

COPY downloads/hadoop-${HADOOP_VERSION}.tar.gz /opt/
RUN tar -xzf /opt/hadoop-${HADOOP_VERSION}.tar.gz -C /opt && \
    mv /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} && \
    rm /opt/hadoop-${HADOOP_VERSION}.tar.gz && \
    rm -rf ${HADOOP_HOME}/share/doc

COPY downloads/hive-standalone-metastore-${METASTORE_VERSION}-bin.tar.gz /opt/
RUN tar -xzf /opt/hive-standalone-metastore-${METASTORE_VERSION}-bin.tar.gz -C /opt && \
    mv /opt/apache-hive-metastore-${METASTORE_VERSION}-bin ${HIVE_HOME} && \
    rm /opt/hive-standalone-metastore-${METASTORE_VERSION}-bin.tar.gz

COPY downloads/postgresql-${POSTGRES_JDBC_VERSION}.jar ${HIVE_HOME}/lib/postgresql-jdbc.jar

# Fix Guava version mismatch
RUN rm -f ${HIVE_HOME}/lib/guava-*.jar && \
    cp ${HADOOP_HOME}/share/hadoop/hdfs/lib/guava-*.jar ${HIVE_HOME}/lib/ || true

WORKDIR ${HIVE_HOME}

# Combine configuration folders to single location
RUN mkdir -p /opt/conf

# Expose a single volume for configuration files
VOLUME /opt/conf

RUN echo '#!/bin/bash\n\n\
if [ "$1" = "initSchema" ]; then\n\
  if bin/schematool -dbType postgres -info > /dev/null 2>&1; then\n\
    echo "Metastore schema already initialized."\n\
  else\n\
    bin/schematool -dbType postgres -initSchema\n\
  fi\n\
else\n\
  bin/start-metastore\n\
fi' > /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 9083

ENTRYPOINT ["/entrypoint.sh"]
