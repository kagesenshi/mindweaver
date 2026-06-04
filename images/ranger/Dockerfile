# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM apache/ranger:2.8.0

COPY ranger.sh /home/ranger/scripts/ranger.sh
COPY create-ranger-services.py /home/ranger/scripts/create-ranger-services.py
COPY downloads/LdapUserGroupBuilder.java /tmp/LdapUserGroupBuilder.java
COPY patch_ldap_builder.py /tmp/patch_ldap_builder.py

COPY plugin/ /tmp/plugin/

USER root
COPY downloads/ranger-2.8.0-usersync.tar.gz /opt/ranger/
RUN tar xvfz /opt/ranger/ranger-2.8.0-usersync.tar.gz --directory=/opt/ranger && \
    ln -s /opt/ranger/ranger-2.8.0-usersync /opt/ranger/usersync && \
    rm -f /opt/ranger/ranger-2.8.0-usersync.tar.gz && \
    python3 /tmp/patch_ldap_builder.py /tmp/LdapUserGroupBuilder.java && \
    mkdir -p /opt/ranger/usersync/patch && \
    /opt/java/openjdk/bin/javac -cp "/opt/ranger/usersync/dist/*:/opt/ranger/usersync/lib/*" -d /opt/ranger/usersync/patch /tmp/LdapUserGroupBuilder.java && \
    rm -f /tmp/LdapUserGroupBuilder.java /tmp/patch_ldap_builder.py && \
    sed -i 's|cp="${cdir}/dist/\*|cp="${cdir}/patch:${cdir}/dist/\*|g' /opt/ranger/usersync/ranger-usersync-services.sh && \
    python3 -c "import os; setup_py = '/opt/ranger/usersync/setup.py'; code = open(setup_py).read(); code = code.replace('ret[\'ranger.usersync.ldap.deltasync\'] = \"true\"', \"ret['ranger.usersync.ldap.deltasync'] = props.get('SYNC_LDAP_DELTASYNC', 'true')\"); code = code.replace('    if rangerUsersync_password != \"\" :\\n        output = os.system(cmd)', '    if rangerUsersync_password != \"\" :\\n        import subprocess\\n        output = subprocess.call([\"python\", \"updatepolicymgrpassword.py\", rangerUsersync_name, rangerUsersync_password])'); open(setup_py, 'w').write(code); update_py = '/opt/ranger/usersync/updatepolicymgrpassword.py'; code = open(update_py).read(); target = 'cmd=\"%s -cp lib/* org.apache.ranger.credentialapi.buildks create %s -value %s  -provider jceks://file%s\" %(JAVA_BIN,SYNC_POLICY_MGR_ALIAS,SYNC_POLICY_MGR_PASSWORD,SYNC_LDAP_BIND_KEYSTOREPATH)\\n\\t\\tret=subprocess.call(shlex.split(cmd))'; replacement = 'cmd = [JAVA_BIN, \"-cp\", \"lib/*\", \"org.apache.ranger.credentialapi.buildks\", \"create\", SYNC_POLICY_MGR_ALIAS, \"-value\", SYNC_POLICY_MGR_PASSWORD, \"-provider\", f\"jceks://file{SYNC_LDAP_BIND_KEYSTOREPATH}\"]\\n\\t\\tret=subprocess.call(cmd)'; code = code.replace(target, replacement); open(update_py, 'w').write(code);" && \
    cp /opt/ranger/usersync/install.properties /home/ranger/scripts/ranger-usersync-install.properties && \
    mkdir -p /var/run/ranger /var/log/ranger/usersync /etc/ranger /etc/init.d && \
    touch /etc/init.d/ranger-admin /etc/init.d/ranger-usersync && \
    touch /etc/rc2.d/S99ranger-usersync /etc/rc2.d/K00ranger-usersync /etc/rc3.d/S99ranger-usersync /etc/rc3.d/K00ranger-usersync /usr/bin/ranger-usersync && \
    chown -R ranger:ranger /opt/ranger/ranger-2.8.0-usersync /opt/ranger/usersync /var/run/ranger /var/log/ranger /etc/ranger /etc/init.d/ranger-admin /etc/init.d/ranger-usersync /etc/rc2.d/S99ranger-usersync /etc/rc2.d/K00ranger-usersync /etc/rc3.d/S99ranger-usersync /etc/rc3.d/K00ranger-usersync /usr/bin/ranger-usersync /home/ranger/scripts/ranger-usersync-install.properties && \
    chmod +x /home/ranger/scripts/ranger.sh /home/ranger/scripts/create-ranger-services.py

RUN mkdir -p /opt/ranger/admin/ews/webapp/WEB-INF/classes/ranger-plugins/superset && \
    /opt/java/openjdk/bin/javac -cp "/opt/ranger/admin/ews/webapp/WEB-INF/lib/*" -d /opt/ranger/admin/ews/webapp/WEB-INF/classes/ /tmp/plugin/superset/RangerServiceSuperset.java && \
    chown -R ranger:ranger /opt/ranger/admin/ews/webapp/WEB-INF/classes/ranger-plugins/superset && \
    mv /tmp/plugin/superset/ranger-servicedef-superset.json /home/ranger/scripts/ranger-servicedef-superset.json && \
    chown ranger:ranger /home/ranger/scripts/ranger-servicedef-superset.json && \
    rm -rf /tmp/plugin

USER ranger
