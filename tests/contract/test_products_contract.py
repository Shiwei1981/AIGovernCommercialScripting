def test_products_page_contract(auth_client):
    resp = auth_client.get("/api/products")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 4
    assert data["total_count"] >= len(data["items"])
    assert len(data["items"]) <= 4
    item = data["items"][0]
    assert {"product_id", "product_name", "category_name"}.issubset(item.keys())


def test_products_pagination_contract(auth_client):
    resp = auth_client.get("/api/products?page=2&page_size=4")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["page_size"] == 4
    assert len(data["items"]) <= 4
