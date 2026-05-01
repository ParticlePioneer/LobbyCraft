import pytest 
import uuid
from fastapi.testclient import TestClient 
from main import app 
 
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def get_uniq_user(prefix="u"):
    return f"{prefix}_{uuid.uuid4().hex[:6]}"
 
def test_create_player(client): 
    r = client.post('/players/', json={'username': get_uniq_user('t1'), 'region': 'AS-EAST'}) 
    assert r.status_code == 201 
    assert 'player_id' in r.json() 
    assert r.json()['current_mmr'] == 1000 
 
def test_duplicate_username_rejected(client): 
    uname = get_uniq_user('dup')
    client.post('/players/', json={'username': uname, 'region': 'EU-WEST'}) 
    r = client.post('/players/', json={'username': uname, 'region': 'EU-WEST'}) 
    assert r.status_code >= 400 
 
def test_create_party(client): 
    p1 = client.post('/players/', json={'username': get_uniq_user('p1'), 'region': 'AS-EAST'}).json() 
    p2 = client.post('/players/', json={'username': get_uniq_user('p2'), 'region': 'AS-EAST'}).json() 
    r = client.post('/parties/', json={ 
        'party_type': 'duo', 
        'player_ids': [p1['player_id'], p2['player_id']] 
    }) 
    assert r.status_code == 201 
    assert 'party_id' in r.json() 
 
def test_enqueue(client): 
    p = client.post('/players/', json={'username': get_uniq_user('eq1'), 'region': 'AS-EAST'}).json() 
    party = client.post('/parties/', json={'party_type':'solo','player_ids':[p['player_id']]}).json() 
    r = client.post('/queue/', json={'party_id': party['party_id'], 'mode_id': 1}) 
    assert r.status_code == 202 
    assert 'queue_no' in r.json() 
 
def test_duplicate_queue_rejected(client): 
    p = client.post('/players/', json={'username': get_uniq_user('dq'), 'region': 'AS-EAST'}).json() 
    party = client.post('/parties/', json={'party_type':'solo','player_ids':[p['player_id']]}).json() 
    client.post('/queue/', json={'party_id': party['party_id'], 'mode_id': 1}) 
    r = client.post('/queue/', json={'party_id': party['party_id'], 'mode_id': 1}) 
    assert r.status_code == 409 
 
def test_mmr_history_empty(client): 
    p = client.post('/players/', json={'username': get_uniq_user('hist'), 'region': 'EU-WEST'}).json() 
    r = client.get(f'/players/{p["player_id"]}/mmr-history') 
    assert r.status_code == 200 
    assert r.json() == [] 
 
def test_expire_timeouts(client): 
    r = client.post('/queue/expire-timeouts') 
    assert r.status_code == 200 
    assert 'expired' in r.json() 
 
def test_leaderboard(client): 
    r = client.get('/matches/leaderboard/kills?mode_type=battle_royale&limit=5') 
    assert r.status_code == 200 
    assert isinstance(r.json(), list)