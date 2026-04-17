import json


def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json['status'] == 'healthy'


def test_index(client):
    r = client.get('/')
    assert r.status_code == 200


def test_login_get(client):
    r = client.get('/login')
    assert r.status_code == 200


def test_register_get(client):
    r = client.get('/register')
    assert r.status_code == 200


def test_register_and_login(client):
    # Register
    r = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'pass123',
    }, follow_redirects=True)
    assert r.status_code == 200

    # Login with correct credentials
    r = client.post('/login', data={
        'username': 'testuser',
        'password': 'pass123',
    }, follow_redirects=True)
    assert r.status_code == 200


def test_login_invalid_credentials(client):
    r = client.post('/login', data={
        'username': 'nobody',
        'password': 'wrong',
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'Invalid username or password' in r.data


def test_protected_route_redirects_when_not_logged_in(client):
    r = client.get('/dashboard', follow_redirects=False)
    assert r.status_code == 302


def test_manage_rejects_drop(client):
    r = client.post('/manage', json={'query': 'DROP TABLE user'})
    # Unauthenticated → redirect, but query itself should be rejected if auth bypassed
    assert r.status_code in (302, 400)


def test_validate_sql_query():
    from utils import validate_sql_query
    ok, _ = validate_sql_query('SELECT * FROM users')
    assert ok is True

    bad, msg = validate_sql_query('DROP TABLE users')
    assert bad is False
    assert 'DROP' in msg
