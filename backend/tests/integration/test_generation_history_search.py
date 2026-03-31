def test_history_search_by_session(client, bearer_headers):
    client.post(
        '/api/generations',
        json={'sessionId': 'hist-session', 'prompt': 'Store this generation', 'useRecentNews': True},
        headers=bearer_headers,
    )

    response = client.get('/api/generations?sessionId=hist-session', headers=bearer_headers)
    assert response.status_code == 200
    assert len(response.json()['items']) >= 1


def test_history_requires_search_key(client, bearer_headers):
    response = client.get('/api/generations', headers=bearer_headers)
    assert response.status_code == 400
