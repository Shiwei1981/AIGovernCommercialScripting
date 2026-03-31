import json
from pathlib import Path

from jsonschema import validate


def test_generation_record_schema_compatibility(client, bearer_headers):
    create = client.post(
        '/api/generations',
        json={'sessionId': 'schema-session', 'prompt': 'Validate generation schema', 'useRecentNews': True},
        headers=bearer_headers,
    )
    generation_id = create.json()['generationId']

    detail = client.get(f'/api/generations/{generation_id}', headers=bearer_headers)
    schema_path = Path(__file__).resolve().parents[3] / 'specs' / '001-governed-script-workflow' / 'contracts' / 'generation-record.schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))

    assert detail.status_code == 200
    validate(instance=detail.json(), schema=schema)


def test_audit_record_schema_compatibility(client, bearer_headers):
    create = client.post(
        '/api/generations',
        json={'sessionId': 'schema-session', 'prompt': 'Validate audit schema', 'useRecentNews': True},
        headers=bearer_headers,
    )
    generation_id = create.json()['generationId']

    trace = client.get(f'/api/generations/{generation_id}/audit', headers=bearer_headers)
    schema_path = Path(__file__).resolve().parents[3] / 'specs' / '001-governed-script-workflow' / 'contracts' / 'audit-record.schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))

    assert trace.status_code == 200
    for item in trace.json()['auditEvents']:
        validate(instance=item, schema=schema)
