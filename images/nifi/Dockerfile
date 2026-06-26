# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM apache/nifi:2.9.0

USER root

# Download the Apache NiFi Ranger NAR for authorization
RUN curl -fsSL -o /opt/nifi/nifi-current/lib/nifi-ranger-nar-2.0.0-M2.nar \
    "https://repo1.maven.org/maven2/org/apache/nifi/nifi-ranger-nar/2.0.0-M2/nifi-ranger-nar-2.0.0-M2.nar" \
    && chown nifi:nifi /opt/nifi/nifi-current/lib/nifi-ranger-nar-2.0.0-M2.nar

USER nifi
