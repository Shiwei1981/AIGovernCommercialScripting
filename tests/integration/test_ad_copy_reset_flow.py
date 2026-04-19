def test_ad_copy_generation_and_reset(auth_client):
    trend = auth_client.post("/api/trends/search", json={"product_id": 1}).json()["summary"]["summary_text"]
    resp = auth_client.post(
        "/api/ad-copy/generate",
        json={
            "customer_description": "buyer",
            "customer_id": 1,
            "product_id": 1,
            "trend_summary": trend,
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()["ad_copy_text"].split()) <= 500
    reset = auth_client.post("/api/reset")
    assert reset.status_code == 200
