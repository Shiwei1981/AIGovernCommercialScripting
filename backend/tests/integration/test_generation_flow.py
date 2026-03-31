from uuid import UUID


def test_generation_success_flow(client, bearer_headers):
    payload = {'sessionId': 'session-1', 'prompt': 'Summarize the latest business news.', 'useRecentNews': True}
    response = client.post('/api/generations', json=payload, headers=bearer_headers)

    assert response.status_code == 201
    body = response.json()
    UUID(body['generationId'])
    assert body['status'] == 'completed'
    assert body['createdAtUtc']


def test_generation_controlled_failure_input_validation(client, bearer_headers):
    payload = {'sessionId': 'session-1', 'prompt': '', 'useRecentNews': True}
    response = client.post('/api/generations', json=payload, headers=bearer_headers)

    assert response.status_code == 422
