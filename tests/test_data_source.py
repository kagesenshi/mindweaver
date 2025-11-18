from fastapi.testclient import TestClient

def test_datasource(client: TestClient):
    resp = client.get('/')
    print(resp.content)
    