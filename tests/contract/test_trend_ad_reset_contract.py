def test_trend_search_contract(auth_client):
    resp = auth_client.post("/api/trends/search", json={"product_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert "search_query" in body
    assert "news_items" in body
    assert "summary" in body


def test_ad_copy_and_reset_contract(auth_client):
    ad = auth_client.post(
        "/api/ad-copy/generate",
        json={
            "customer_description": "retail buyer",
            "customer_id": 1,
            "product_id": 1,
            "trend_summary": "summary",
        },
    )
    assert ad.status_code == 200
    assert "ad_copy_text" in ad.json()
    reset = auth_client.post("/api/reset")
    assert reset.status_code == 200
    assert reset.json()["status"] == "ok"
