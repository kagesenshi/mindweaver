from fastapi.testclient import TestClient
from psycopg.connection import Connection
from mindweaver.config import logger
import copy

def test_datasource(client: TestClient):

    resp = client.post('/data_sources', json={
        'name': 'my-sftp-server',
        'title': 'My SFTP Server',
        'type': 'stfp',
        'parameters': {
            'host': 'localhost',
            'port': 2222,
            'path': '/'
        }
    })

    resp.raise_for_status()
