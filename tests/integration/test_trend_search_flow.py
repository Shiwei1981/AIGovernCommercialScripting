from types import SimpleNamespace
from urllib.parse import parse_qs, unquote_plus, urlparse


def test_trend_pipeline_citations(auth_client):
    resp = auth_client.post("/api/trends/search", json={"product_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    summary = body["summary"]
    assert body["search_query"]
    assert isinstance(summary["citations"], list)
    assert summary["valid_ratio"] >= 0.4


def test_trend_pipeline_uses_ai_generated_query(auth_client, monkeypatch):
    captured: dict[str, str] = {}

    def fake_model(_settings, prompt):  # noqa: ANN001
        if "Generate one broad Google News search query" in prompt:
            return "retail demand launch innovation"
        return "Trend summary with citations [1][2]."

    def fake_parse(url: str):
        captured["url"] = url
        entries = [
            {
                "title": "News A",
                "link": "https://news.google.com/articles/abc?url=https://publisher/a",
                "published": "Sat, 07 Mar 2026 08:00:00 GMT",
                "summary": "<p>Demand remains active for this product area.</p>",
                "source": {"title": "Publisher A", "href": "https://publisher/a"},
            }
        ]
        return SimpleNamespace(entries=entries, bozo=False)

    monkeypatch.setattr("app.services.news_trend_service.invoke_model", fake_model)
    monkeypatch.setattr("app.services.news_trend_service.feedparser.parse", fake_parse)
    resp = auth_client.post("/api/trends/search", json={"product_id": 1})

    assert resp.status_code == 200
    parsed_query = parse_qs(urlparse(captured["url"]).query)["q"][0]
    query_text = unquote_plus(parsed_query)
    assert "retail demand launch innovation" in query_text


def test_trend_pipeline_broadens_query_when_first_attempt_has_no_results(auth_client, monkeypatch):
    captured_queries: list[str] = []

    def fake_model(_settings, prompt):  # noqa: ANN001
        if "Generate one broad Google News search query" in prompt:
            return "narrow unreachable terms"
        return "Trend summary with citations [1][2]."

    def fake_parse(url: str):
        query_text = unquote_plus(parse_qs(urlparse(url).query)["q"][0])
        captured_queries.append(query_text)
        if query_text == "narrow unreachable terms":
            return SimpleNamespace(entries=[], bozo=False)
        entries = [
            {
                "title": "News A",
                "link": "https://news.google.com/articles/abc?url=https://publisher/a",
                "published": "Sat, 07 Mar 2026 08:00:00 GMT",
                "summary": "<p>Demand remains active for this product area.</p>",
                "source": {"title": "Publisher A", "href": "https://publisher/a"},
            }
        ]
        return SimpleNamespace(entries=entries, bozo=False)

    monkeypatch.setattr("app.services.news_trend_service.invoke_model", fake_model)
    monkeypatch.setattr("app.services.news_trend_service.feedparser.parse", fake_parse)

    resp = auth_client.post("/api/trends/search", json={"product_id": 1})

    assert resp.status_code == 200
    body = resp.json()
    assert captured_queries[0] == "narrow unreachable terms"
    assert body["search_query"] == "Model 1 Category 1"
    assert len(captured_queries) >= 2


def test_no_usable_rss_metadata_returns_fallback_message(auth_client, monkeypatch):
    monkeypatch.setattr(
        "app.services.news_trend_service.feedparser.parse",
        lambda _: SimpleNamespace(entries=[{"title": "", "link": ""}], bozo=False),
    )
    resp = auth_client.post("/api/trends/search", json={"product_id": 1})
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert "未检索到足够可用于总结的搜索结果" in summary["summary_text"]
    assert len(summary["fetch_errors"]) >= 1
