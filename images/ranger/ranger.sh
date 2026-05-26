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

set_property() {
  local key="$1"
  local value="$2"
  local file="$3"
  if grep -q "^[[:space:]]*${key}[[:space:]]*=" "${file}"; then
    local escaped_value=$(echo "${value}" | sed 's/[&/\]/\\&/g')
    sed -i "s|^[[:space:]]*${key}[[:space:]]*=.*|${key}=${escaped_value}|" "${file}"
  else
    echo "${key}=${value}" >> "${file}"
  fi
}

RANGER_COMPONENT=${RANGER_COMPONENT:-admin}

if [ "${RANGER_COMPONENT}" == "usersync" ]
then
  if [ ! -e ${RANGER_HOME}/usersync/.setupDone ]
  then
    SETUP_USERSYNC=true
  else
    SETUP_USERSYNC=false
  fi

  if [ "${SETUP_USERSYNC}" == "true" ]
  then
    cp ${RANGER_SCRIPTS}/ranger-usersync-install.properties ${RANGER_HOME}/usersync/install.properties
    set_property "POLICY_MGR_URL" "${RANGER_ADMIN_URL:-http://localhost:6080}" "${RANGER_HOME}/usersync/install.properties"
    set_property "rangerUsersync_password" "${RANGER_USERSYNC_PASSWORD}" "${RANGER_HOME}/usersync/install.properties"
    
    # Append all custom properties (including SYNC_*) to usersync install.properties
    if [ -d ${RANGER_PROPS_DIR} ]
    then
      for f in ${RANGER_PROPS_DIR}/*.properties; do
          if [ -f "$f" ]; then
              while IFS='=' read -r key value || [ -n "$key" ]; do
                  [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
                  key=$(echo "$key" | xargs)
                  value=$(echo "$value" | xargs)
                  set_property "$key" "$value" "${RANGER_HOME}/usersync/install.properties"
              done < "$f"
          fi
      done
    fi
    
    cd ${RANGER_HOME}/usersync || exit
    if ./setup.sh;
    then
      rm -f ${RANGER_HOME}/usersync/install.properties
      touch "${RANGER_HOME}/usersync"/.setupDone
    else
      echo "Ranger UserSync Setup Script didn't complete proper execution."
      exit 1
    fi
  fi

  cd ${RANGER_HOME}/usersync && ./ranger-usersync-services.sh start
  
  USERSYNC_PID_DIR_PATH=${USERSYNC_PID_DIR_PATH:-/var/run/ranger}
  USERSYNC_PID_NAME=${USERSYNC_PID_NAME:-usersync.pid}
  RANGER_USERSYNC_PID_FILE="${USERSYNC_PID_DIR_PATH}/${USERSYNC_PID_NAME}"

  for i in {1..10}
  do
    if [ -f "${RANGER_USERSYNC_PID_FILE}" ]
    then
      RANGER_USERSYNC_PID=$(cat "${RANGER_USERSYNC_PID_FILE}")
      if [ -n "$RANGER_USERSYNC_PID" ]
      then
        echo "PID ${RANGER_USERSYNC_PID} found"
        break
      fi
    fi
    echo "PID ${RANGER_USERSYNC_PID} not found, trying again in 1 second"
    sleep 1
  done

  if [ -z "$RANGER_USERSYNC_PID" ]
  then
    echo "Ranger UserSync process probably exited, no process id found in ${RANGER_USERSYNC_PID_FILE}!"
    exit 1
  else
    echo "Ranger UserSync is running with PID ${RANGER_USERSYNC_PID}"
    tail --pid=$RANGER_USERSYNC_PID -F ${RANGER_HOME}/usersync/logs/auth.log ${RANGER_HOME}/usersync/logs/usersync-$(hostname)-.log
  fi

else
  if [ ! -e ${RANGER_HOME}/.setupDone ]
  then
    SETUP_RANGER=true
  else
    SETUP_RANGER=false
  fi

  if [ "${SETUP_RANGER}" == "true" ]
  then
    cp ${RANGER_SCRIPTS}/ranger-admin-install.properties ${RANGER_HOME}/admin/install.properties
    if [ -n "${RANGER_DEFAULT_CONF_DIR}" ] && [ -d "${RANGER_DEFAULT_CONF_DIR}" ]
    then
        cp "${RANGER_DEFAULT_CONF_DIR}"/* "${RANGER_HOME}/conf/"
    fi
    set_property "db_flavor" "${RANGER_DB_TYPE:-postgres}" "${RANGER_HOME}/admin/install.properties"
    set_property "db_host" "${RANGER_DB_HOST}" "${RANGER_HOME}/admin/install.properties"
    set_property "db_name" "${RANGER_DB_NAME}" "${RANGER_HOME}/admin/install.properties"
    set_property "db_user" "${RANGER_DB_USER}" "${RANGER_HOME}/admin/install.properties"
    set_property "db_password" "${RANGER_DB_PASSWORD}" "${RANGER_HOME}/admin/install.properties"
    set_property "db_root_user" "${RANGER_DB_ROOT_USER:-postgres}" "${RANGER_HOME}/admin/install.properties"
    set_property "db_root_password" "${POSTGRES_PASSWORD}" "${RANGER_HOME}/admin/install.properties"
    set_property "rangerAdmin_password" "${RANGER_ADMIN_PASSWORD}" "${RANGER_HOME}/admin/install.properties"
    set_property "rangerTagsync_password" "${RANGER_TAGSYNC_PASSWORD}" "${RANGER_HOME}/admin/install.properties"
    set_property "rangerUsersync_password" "${RANGER_USERSYNC_PASSWORD}" "${RANGER_HOME}/admin/install.properties"
    set_property "keyadmin_password" "${RANGER_KEYADMIN_PASSWORD}" "${RANGER_HOME}/admin/install.properties"

    if [ -d ${RANGER_PROPS_DIR} ]
    then
      for f in ${RANGER_PROPS_DIR}/*.properties; do
          if [ -f "$f" ]; then
              while IFS='=' read -r key value || [ -n "$key" ]; do
                  [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
                  key=$(echo "$key" | xargs)
                  value=$(echo "$value" | xargs)
                  set_property "$key" "$value" "${RANGER_HOME}/admin/install.properties"
              done < "$f"
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
      exit 1
    fi
  fi

  cd ${RANGER_HOME}/admin && ./ews/ranger-admin-services.sh start

  if [ "${SETUP_RANGER}" == "true" ]
  then
    # Wait for Ranger Admin to become ready
    sleep 30
    python3 ${RANGER_SCRIPTS}/create-ranger-services.py
  fi

  RANGER_ADMIN_PID=$(ps -ef | grep -v grep | grep -i "org.apache.ranger.server.tomcat.EmbeddedServer" | awk '{print $2}')

  # prevent the container from exiting
  if [ -z "$RANGER_ADMIN_PID" ]
  then
    echo "Ranger Admin process probably exited, no process id found!"
    exit 1
  else
    tail --pid=$RANGER_ADMIN_PID -f /dev/null
  fi
fi
