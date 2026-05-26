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
    cp /opt/ranger/usersync/install.properties /home/ranger/scripts/ranger-usersync-install.properties && \
    mkdir -p /var/run/ranger /var/log/ranger/usersync /etc/ranger /etc/init.d && \
    touch /etc/init.d/ranger-admin /etc/init.d/ranger-usersync && \
    touch /etc/rc2.d/S99ranger-usersync /etc/rc2.d/K00ranger-usersync /etc/rc3.d/S99ranger-usersync /etc/rc3.d/K00ranger-usersync /usr/bin/ranger-usersync && \
    chown -R ranger:ranger /opt/ranger/ranger-2.8.0-usersync /opt/ranger/usersync /var/run/ranger /var/log/ranger /etc/ranger /etc/init.d/ranger-admin /etc/init.d/ranger-usersync /etc/rc2.d/S99ranger-usersync /etc/rc2.d/K00ranger-usersync /etc/rc3.d/S99ranger-usersync /etc/rc3.d/K00ranger-usersync /usr/bin/ranger-usersync /home/ranger/scripts/ranger-usersync-install.properties && \
    chmod +x /home/ranger/scripts/ranger.sh /home/ranger/scripts/create-ranger-services.py

USER ranger
