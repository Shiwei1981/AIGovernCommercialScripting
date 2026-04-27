def test_trend_search_contract(auth_client):
    resp = auth_client.post("/api/trends/search", json={"product_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert "search_query" in body
    assert "news_items" in body
    assert "generated_prompt" in body
    assert "summary" in body


def test_trend_preview_and_execute_contract(auth_client):
    preview = auth_client.post("/api/trends/search/preview", json={"product_id": 1})
    assert preview.status_code == 200
    preview_body = preview.json()
    assert "search_query" in preview_body
    assert "news_items" in preview_body
    assert "generated_prompt" in preview_body

    execute = auth_client.post(
        "/api/trends/search/execute",
        json=preview_body,
    )
    assert execute.status_code == 200
    assert "summary" in execute.json()


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
    assert "generated_prompt" in ad.json()
    reset = auth_client.post("/api/reset")
    assert reset.status_code == 200
    assert reset.json()["status"] == "ok"


def test_ad_copy_preview_and_execute_contract(auth_client):
    payload = {
        "customer_description": "retail buyer",
        "customer_id": 1,
        "product_id": 1,
        "trend_summary": "summary",
    }
    preview = auth_client.post("/api/ad-copy/preview", json=payload)
    assert preview.status_code == 200
    generated_prompt = preview.json()["generated_prompt"]
    assert generated_prompt

    execute = auth_client.post(
        "/api/ad-copy/execute",
        json={"generated_prompt": generated_prompt},
    )
    assert execute.status_code == 200
    assert "ad_copy_text" in execute.json()
