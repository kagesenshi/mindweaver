# Stage 1: Dependency Resolver
FROM maven:3.9-eclipse-temurin-17 AS ship
WORKDIR /resolver

# We create a minimal pom.xml to fetch the missing YARN utilities
RUN echo '<project><modelVersion>4.0.0</modelVersion>\
    <groupId>com.local</groupId><artifactId>dep-resolver</artifactId><version>1</version>\
    <dependencies>\
        <dependency>\
            <groupId>org.apache.hadoop</groupId>\
            <artifactId>hadoop-yarn-common</artifactId>\
            <version>3.4.1</version>\
        </dependency>\
    </dependencies></project>' > pom.xml

# Download dependencies into a local folder
RUN mvn dependency:copy-dependencies -DoutputDirectory=/resolver/deps

# Stage 2: Final Image
FROM apache/hive:standalone-metastore-4.2.0

ENV POSTGRES_JDBC_VERSION=42.7.2

COPY --from=ship /resolver/deps/*.jar ${HIVE_HOME}/lib/

COPY downloads/postgresql-${POSTGRES_JDBC_VERSION}.jar ${HIVE_HOME}/lib/postgresql-jdbc.jar
COPY entrypoint.sh /entrypoint.sh
