def test_get_audit_contract_shape(client, bearer_headers):
    create = client.post(
        '/api/generations',
        json={'sessionId': 'audit-session', 'prompt': 'Audit this generation', 'useRecentNews': True},
        headers=bearer_headers,
    )
    generation_id = create.json()['generationId']

    response = client.get(f'/api/generations/{generation_id}/audit', headers=bearer_headers)
    assert response.status_code == 200
    payload = response.json()
    assert {'generationId', 'auditEvents', 'sourceReferences'}.issubset(payload.keys())
