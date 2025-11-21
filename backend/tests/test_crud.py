from fastapi.testclient import TestClient
from mindweaver.config import logger
import copy

def test_crud(crud_client: TestClient):
    client = crud_client

    resp = client.post('/models', json={
        'name': 'my-model',
        'title': 'My Model',
    })

    resp.raise_for_status()
    data = resp.json()
    record_id = data['record']['id']

    resp = client.get(f'/models/{record_id}')

    resp.raise_for_status()

    result = resp.json()
    assert result['record']['id'] == record_id
    assert result['record']['name'] == data['record']['name']

    record = data['record']
    update_request = copy.deepcopy(record)

    update_request['id'] = 2 # should be ignored
    update_request['title'] = 'New title'
    update_request['name'] = 'new-name' #should be ignored
    resp = client.put(f'/models/{record_id}', json=update_request) 

    resp.raise_for_status()

    updated_record = resp.json()['record']

    # should remain the same
    assert updated_record['id'] == record['id']
    assert updated_record['uuid'] == record['uuid']
    assert updated_record['name'] == record['name']
    assert updated_record['created'] == record['created']

    # should change
    assert updated_record['title'] == 'New title'
    assert updated_record['modified'] >= record['modified']

    resp = client.delete(f'/models/{record_id}')

    resp.raise_for_status()

    resp = client.get(f'/models/{record_id}')

    assert resp.status_code == 404