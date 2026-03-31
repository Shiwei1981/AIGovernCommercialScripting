def test_acceptance_signin_generation_search_and_audit(client, bearer_headers):
    create = client.post(
        '/api/generations',
        json={'sessionId': 'acceptance-session', 'prompt': 'Acceptance end-to-end request', 'useRecentNews': True},
        headers=bearer_headers,
    )
    assert create.status_code == 201
    generation_id = create.json()['generationId']

    history = client.get('/api/generations?sessionId=acceptance-session', headers=bearer_headers)
    assert history.status_code == 200
    assert any(item['generationId'] == generation_id for item in history.json()['items'])

    audit = client.get(f'/api/generations/{generation_id}/audit', headers=bearer_headers)
    assert audit.status_code == 200
    assert audit.json()['generationId'] == generation_id
