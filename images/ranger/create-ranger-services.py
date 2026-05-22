# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
from apache_ranger.model.ranger_service import RangerService
from apache_ranger.client.ranger_client import RangerClient
from json import JSONDecodeError

# Read admin password from environment, fallback to rangerR0cks!
admin_password = os.environ.get("RANGER_ADMIN_PASSWORD", "rangerR0cks!")

# Use localhost since it runs inside the container
ranger_client = RangerClient('http://localhost:6080', ('admin', admin_password))

def service_not_exists(service):
    try:
        svc = ranger_client.get_service(service.name)
    except JSONDecodeError:
        return 1
    return 0 if svc is not None else 1

kafka = RangerService({'name': 'dev_kafka', 'type': 'kafka',
                       'configs': {'username': 'kafka', 'password': 'kafka',
                                   'zookeeper.connect': 'ranger-zk.example.com:2181'}})

trino = RangerService({'name': 'dev_trino',
                       'type': 'trino',
                       'configs': {
                           'username': 'trino',
                           'password': 'trino',
                           'jdbc.driverClassName': 'io.trino.jdbc.TrinoDriver',
                           'jdbc.url': 'jdbc:trino://ranger-trino:8080',
                       }})

elasticsearch = RangerService({'name': 'dev_elasticsearch',
                               'type': 'elasticsearch',
                               'configs': {
                                   'username': 'elastic',
                                   'password': 'changeit',
                                   'elasticsearch.url': 'http://elasticsearch:9200',
                               }})

nifi = RangerService({'name': 'dev_nifi',
                      'type': 'nifi',
                      'configs': {
                          'username': 'admin',
                          'password': 'changeit',
                          'nifi.url': 'http://nifi:8080',
                      }})

# Only keep kafka, trino, elasticsearch, and nifi enabled
services = [kafka, trino, elasticsearch, nifi]
for service in services:
    try:
        if service_not_exists(service):
            ranger_client.create_service(service)
            print(f" {service.name} service created!")
    except Exception as e:
        print(f"An exception occurred when creating service {service.name}: {e}")
