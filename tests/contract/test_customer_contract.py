def test_customer_query_contract(auth_client):
    resp = auth_client.post("/api/customers/query", json={"customer_description": "high value"})
    assert resp.status_code == 200
    body = resp.json()
    assert "generated_sql" in body
    assert "results" in body
    assert len(body["results"]) <= 10
    if body["results"]:
        assert "company_name" in body["results"][0]


def test_customer_analysis_contract(auth_client):
    resp = auth_client.post("/api/customers/1/analysis")
    assert resp.status_code == 200
    body = resp.json()
    assert "order_history" in body
    assert "analysis_text" in body
