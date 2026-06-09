# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM trinodb/trino:481

USER root

# Add jetty-client jar for Ranger Solr audit destination
# Required to resolve: java.lang.NoClassDefFoundError: org/eclipse/jetty/client/api/Authentication
RUN curl -fsSL -o /usr/lib/trino/plugin/jetty-client.jar \
    "https://repo1.maven.org/maven2/org/eclipse/jetty/jetty-client/12.0.15/jetty-client-12.0.15.jar"

USER trino

