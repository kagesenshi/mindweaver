# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ranger_url = os.environ["RANGER_URL"].rstrip('/')
auth_header = "Basic " + os.environ["RANGER_AUTH_B64"]
headers = {
    "Authorization": auth_header,
    "Content-Type": "application/json"
}

service_name = os.environ["SERVICE_NAME"]
action = os.environ["ACTION"]
ranger_pass = os.environ["RANGER_PASS"]
namespace = os.environ["NAMESPACE"]

if action == "create":
    get_url = f"{ranger_url}/service/public/v2/api/service/name/{service_name}"
    payload = {
        "name": service_name,
        "type": "trino",
        "configs": {
            "username": "ranger",
            "password": ranger_pass,
            "jdbc.driverClassName": "io.trino.jdbc.TrinoDriver",
            "jdbc.url": f"jdbc:trino://{service_name}.{namespace}.svc.cluster.local:8443?SSL=true",
            "ranger.plugin.super.users": "trino,ranger",
            "commonNameForCertificate": service_name
        }
    }

    existing_id = None
    try:
        req = urllib.request.Request(get_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                existing_id = data.get("id")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"Error checking service: {e}")

    try:
        if existing_id is not None:
            payload["id"] = existing_id
            put_url = f"{ranger_url}/service/public/v2/api/service/{existing_id}"
            req = urllib.request.Request(put_url, data=json.dumps(payload).encode(), headers=headers, method="PUT")
            with urllib.request.urlopen(req, context=ctx) as response:
                print(f"Updated service, response code: {response.status}")
        else:
            post_url = f"{ranger_url}/service/public/v2/api/service"
            req = urllib.request.Request(post_url, data=json.dumps(payload).encode(), headers=headers, method="POST")
            with urllib.request.urlopen(req, context=ctx) as response:
                print(f"Created service, response code: {response.status}")
    except Exception as e:
        print(f"Failed to manage service: {e}")
        raise e

elif action == "delete":
    delete_url = f"{ranger_url}/service/public/v2/api/service/name/{service_name}"
    try:
        req = urllib.request.Request(delete_url, headers=headers, method="DELETE")
        with urllib.request.urlopen(req, context=ctx) as response:
            print(f"Deleted service, response code: {response.status}")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"Error deleting service: {e}")
            raise e
        else:
            print("Service already deleted or not found.")
    except Exception as e:
        print(f"Failed to delete service: {e}")
        raise e
