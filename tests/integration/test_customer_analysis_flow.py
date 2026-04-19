def test_customer_analysis_word_limit(auth_client, monkeypatch):
    monkeypatch.setattr(
        "app.services.customer_analysis_service.invoke_model",
        lambda *_: "word " * 700,
    )
    resp = auth_client.post("/api/customers/1/analysis")
    assert resp.status_code == 200
    analysis = resp.json()["analysis_text"]
    assert len(analysis.split()) <= 500


def test_customer_analysis_cjk_length_limit(auth_client, monkeypatch):
    monkeypatch.setattr(
        "app.services.customer_analysis_service.invoke_model",
        lambda *_: "测" * 700,
    )
    resp = auth_client.post("/api/customers/1/analysis")
    assert resp.status_code == 200
    analysis = resp.json()["analysis_text"]
    assert len(analysis) <= 500
