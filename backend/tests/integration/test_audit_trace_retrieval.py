def test_audit_trace_retrieval(client, bearer_headers):
    create = client.post(
        '/api/generations',
        json={'sessionId': 'trace-session', 'prompt': 'Trace generation evidence', 'useRecentNews': True},
        headers=bearer_headers,
    )
    generation_id = create.json()['generationId']

    trace = client.get(f'/api/generations/{generation_id}/audit', headers=bearer_headers)
    assert trace.status_code == 200
    payload = trace.json()
    assert payload['generationId'] == generation_id
    assert isinstance(payload['auditEvents'], list)
