def test_post_generations_contract_shape(client, bearer_headers):
    response = client.post(
        '/api/generations',
        json={'sessionId': 's1', 'prompt': 'Create a compliant script.', 'useRecentNews': True},
        headers=bearer_headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert {'generationId', 'status', 'createdAtUtc'}.issubset(payload.keys())
