def test_get_generations_contract_shape(client, bearer_headers):
    client.post(
        '/api/generations',
        json={'sessionId': 'session-search', 'prompt': 'Generate contract sample', 'useRecentNews': True},
        headers=bearer_headers,
    )

    response = client.get('/api/generations?sessionId=session-search', headers=bearer_headers)
    assert response.status_code == 200
    payload = response.json()
    assert 'items' in payload
    if payload['items']:
        assert {'generationId', 'sessionId', 'userId', 'status', 'createdAtUtc'}.issubset(payload['items'][0].keys())
