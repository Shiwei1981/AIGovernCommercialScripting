def test_products_bootstrap_contract(auth_client):
    resp = auth_client.get("/api/products/bootstrap")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    item = data[0]
    assert {"product_id", "product_name", "category_name"}.issubset(item.keys())
