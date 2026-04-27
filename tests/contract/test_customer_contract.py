def test_customer_query_contract(auth_client):
    resp = auth_client.post("/api/customers/query", json={"customer_description": "high value"})
    assert resp.status_code == 200
    body = resp.json()
    assert "generated_sql" in body
    assert "results" in body
    assert len(body["results"]) <= 4
    if body["results"]:
        assert "company_name" in body["results"][0]
        assert "addresses" in body["results"][0]
        assert "address_display" in body["results"][0]


def test_customer_analysis_contract(auth_client):
    resp = auth_client.post("/api/customers/1/analysis")
    assert resp.status_code == 200
    body = resp.json()
    assert "order_history" in body
    assert "order_line_items" in body
    assert "generated_prompt" in body
    assert "analysis_text" in body


def test_customer_analysis_preview_and_execute_contract(auth_client):
    preview = auth_client.post(
        "/api/customers/1/analysis/preview",
        json={
            "selected_customer": {"customer_id": 1, "company_name": "Retail Co"},
            "selected_product": {"product_id": 2, "product_name": "Road Tire"},
        },
    )
    assert preview.status_code == 200
    preview_body = preview.json()
    assert "order_line_items" in preview_body
    assert "generated_prompt" in preview_body
    assert preview_body["generated_prompt"]
    assert "Retail Co" in preview_body["generated_prompt"]
    assert "Road Tire" in preview_body["generated_prompt"]

    execute = auth_client.post(
        "/api/customers/1/analysis/execute",
        json={"generated_prompt": preview_body["generated_prompt"]},
    )
    assert execute.status_code == 200
    assert "analysis_text" in execute.json()
