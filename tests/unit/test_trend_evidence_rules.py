from app.services.news_trend_service import (
    _build_broader_news_query,
    _build_citations,
    _build_fallback_news_query,
    _is_valid_search_query,
    _sanitize_search_query,
)


def test_build_citations():
    items = [
        {"title": "A", "rss_link": "https://x", "publisher_url": "https://p/a"},
        {"title": "B", "rss_link": "https://y", "publisher_url": ""},
    ]
    citations = _build_citations(items)
    assert citations[0]["url"] == "https://p/a"
    assert citations[1]["url"] == "https://y"


def test_build_fallback_news_query_uses_product_metadata():
    product = {
        "product_name": "Mountain-100 Silver, 38",
        "category_name": "Mountain Bikes",
        "model_name": "Mountain-100",
        "description": "Top-of-the-line competition mountain bike with front suspension.",
    }

    query = _build_fallback_news_query(product)

    assert "Mountain-100" in query
    assert "Mountain Bikes" in query
    assert "when:" not in query


def test_build_broader_news_query_prefers_primary_product_term():
    product = {
        "product_name": "LL Crankset",
        "category_name": "Cranksets",
        "model_name": "LL Crankset",
    }

    query = _build_broader_news_query(product)

    assert query == "LL Crankset"


def test_sanitize_search_query_strips_label_without_appending_time_filter():
    query = _sanitize_search_query("Query: retail demand launch innovation")

    assert query == "retail demand launch innovation"


def test_invalid_summary_like_text_is_rejected_as_search_query():
    query = _sanitize_search_query("Trend summary with citations [1][2].")

    assert not _is_valid_search_query(query)
