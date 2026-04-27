#!/bin/bash

# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


if [ ! -e ${RANGER_HOME}/.setupDone ]
then
  SETUP_RANGER=true
else
  SETUP_RANGER=false
fi

if [ "${SETUP_RANGER}" == "true" ]
then
  cp ${RANGER_SCRIPTS}/ranger-admin-install.properties ${RANGER_HOME}/admin/install.properties
  {
          echo "db_flavor=${RANGER_DB_TYPE:-postgres}"
          echo "db_host=${RANGER_DB_HOST}"
          echo "db_name=${RANGER_DB_NAME}"
          echo "db_user=${RANGER_DB_USER}"
          echo "db_password=${RANGER_DB_PASSWORD}"
          echo "db_root_user=${RANGER_DB_ROOT_USER:-postgres}"
          echo "db_root_password=${POSTGRES_PASSWORD}"
          echo "rangerAdmin_password=${RANGER_ADMIN_PASSWORD}"
          echo "rangerTagsync_password=${RANGER_TAGSYNC_PASSWORD}"
          echo "rangerUsersync_password=${RANGER_USERSYNC_PASSWORD}"
          echo "keyadmin_password=${RANGER_KEYADMIN_PASSWORD}"
  } >> ${RANGER_HOME}/admin/install.properties

  if [ -d ${RANGER_PROPS_DIR} ]
  then
    for f in ${RANGER_PROPS_DIR}/*.properties; do
        if [ -f "$f" ]; then
            cat "$f" >> ${RANGER_HOME}/admin/install.properties
        fi
    done
  fi

  cd ${RANGER_HOME}/admin || exit
  if ./setup.sh;
  then
        rm -f ${RANGER_HOME}/admin/install.properties
    touch "${RANGER_HOME}"/.setupDone
  else
    echo "Ranger Admin Setup Script didn't complete proper execution."
  fi
fi

cd ${RANGER_HOME}/admin && ./ews/ranger-admin-services.sh start

if [ "${SETUP_RANGER}" == "true" ]
then
  # Wait for Ranger Admin to become ready
  sleep 30
  python3 ${RANGER_SCRIPTS}/create-ranger-services.py
fi

RANGER_ADMIN_PID=`ps -ef  | grep -v grep | grep -i "org.apache.ranger.server.tomcat.EmbeddedServer" | awk '{print $2}'`

# prevent the container from exiting
if [ -z "$RANGER_ADMIN_PID" ]
then
  echo "Ranger Admin process probably exited, no process id found!"
else
  tail --pid=$RANGER_ADMIN_PID -f /dev/null
fi
