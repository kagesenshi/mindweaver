#!/bin/bash
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+
set -e

RANGER_VERSION=2.8.0

mkdir -p downloads
cd downloads

echo "Downloading Ranger Usersync $RANGER_VERSION..."
if [ ! -f "ranger-${RANGER_VERSION}-usersync.tar.gz" ]; then
    wget -q --show-progress --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 "https://archive.apache.org/dist/ranger/${RANGER_VERSION}/services/usersync/ranger-${RANGER_VERSION}-usersync.tar.gz"
else
    echo "ranger-${RANGER_VERSION}-usersync.tar.gz already exists."
fi

echo "Downloading LdapUserGroupBuilder.java from release-ranger-2.8.0..."
if [ ! -f "LdapUserGroupBuilder.java" ]; then
    wget -q --show-progress --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 "https://raw.githubusercontent.com/apache/ranger/release-ranger-2.8.0/ugsync/src/main/java/org/apache/ranger/ldapusersync/process/LdapUserGroupBuilder.java"
else
    echo "LdapUserGroupBuilder.java already exists."
fi

echo "Done downloading components."

