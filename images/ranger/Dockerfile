# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM apache/ranger:2.8.0

COPY ranger.sh /home/ranger/scripts/ranger.sh
COPY create-ranger-services.py /home/ranger/scripts/create-ranger-services.py

USER root
RUN curl -LO https://archive.apache.org/dist/ranger/2.8.0/services/usersync/ranger-2.8.0-usersync.tar.gz && \
    tar xvfz ranger-2.8.0-usersync.tar.gz --directory=/opt/ranger && \
    ln -s /opt/ranger/ranger-2.8.0-usersync /opt/ranger/usersync && \
    rm -f ranger-2.8.0-usersync.tar.gz && \
    mkdir -p /var/run/ranger /var/log/ranger/usersync /etc/ranger && \
    chown -R ranger:ranger /opt/ranger/ranger-2.8.0-usersync /opt/ranger/usersync /var/run/ranger /var/log/ranger && \
    chmod +x /home/ranger/scripts/ranger.sh /home/ranger/scripts/create-ranger-services.py

USER ranger
