def test_nl2sql_select_only_and_ranked_results(auth_client, monkeypatch):
    monkeypatch.setattr(
        "app.services.nl2sql_service.invoke_model",
        lambda *_: (
            "SELECT CustomerID AS customer_id, CompanyName AS customer_name, "
            "1.0 AS relevance_score FROM Customer"
        ),
    )
    resp = auth_client.post("/api/customers/query", json={"customer_description": "high value"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["generated_sql"].upper().startswith("SELECT")
    assert len(data["results"]) <= 4
    if data["results"]:
        assert "company_name" in data["results"][0]
        assert data["results"][0]["address_display"]
    scores = [r["relevance_score"] for r in data["results"]]
    assert scores == sorted(scores, reverse=True)


def test_reject_non_select_sql(auth_client, monkeypatch):
    monkeypatch.setattr("app.services.nl2sql_service.invoke_model", lambda *_: "DELETE FROM Customer")
    resp = auth_client.post("/api/customers/query", json={"customer_description": "bad"})
    assert resp.status_code == 400
