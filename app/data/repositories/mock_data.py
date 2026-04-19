PRODUCTS = [
    {
        "product_id": idx + 1,
        "product_name": f"Demo Product {idx+1}",
        "category_name": f"Category {idx+1}",
        "model_name": f"Model {idx+1}",
        "description": f"Description {idx+1}",
    }
    for idx in range(10)
]

CUSTOMERS = [
    {
        "customer_id": 1,
        "customer_name": "Contoso Retail",
        "company_name": "Contoso Retail",
        "location": "Seattle, WA",
        "relevance_score": 0.95,
        "match_reason": "High spend in selected category",
        "order_count": 8,
        "lifetime_value": 122000.0,
    },
    {
        "customer_id": 2,
        "customer_name": "Fabrikam Stores",
        "company_name": "Fabrikam Stores",
        "location": "Portland, OR",
        "relevance_score": 0.88,
        "match_reason": "Frequent orders and growth trend",
        "order_count": 6,
        "lifetime_value": 97000.0,
    },
]

ORDERS = {
    1: [
        {"order_id": 101, "order_date": "2025-12-01", "total_due": 15000.0},
        {"order_id": 102, "order_date": "2026-01-15", "total_due": 21000.0},
    ],
    2: [
        {"order_id": 201, "order_date": "2025-11-10", "total_due": 9000.0},
    ],
}
