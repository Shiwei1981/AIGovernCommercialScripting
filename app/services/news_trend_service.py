from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, quote_plus, urlparse

import feedparser
from bs4 import BeautifulSoup

from app.config import Settings
from app.errors import AppError
from app.services.ai_client import invoke_model
from app.services.ai_logging_service import AILoggingService

logger = logging.getLogger("ai-commercial-assistant.news-trend")
_QUERY_LABEL_RE = re.compile(r"^(?:google\s+news\s+query|search\s+query|query)\s*:\s*", re.IGNORECASE)
_INVALID_QUERY_PHRASES = ("here is", "trend summary", "with citations", "sources:")
_DESCRIPTION_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "your",
    "their",
    "there",
    "has",
    "have",
    "been",
    "will",
    "allows",
    "allow",
    "using",
    "used",
    "offers",
    "offer",
    "more",
    "less",
    "line",
    "custom",
    "newly",
    "redesigned",
}


def _resolve_publisher_url(link: str) -> str:
    parsed = urlparse(link)
    if "news.google.com" not in parsed.netloc:
        return link
    q = parse_qs(parsed.query).get("url", [])
    if q:
        return q[0]
    return link


def _normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _strip_variant_suffix(value: str | None) -> str:
    normalized = _normalize_space(value)
    if not normalized:
        return ""
    return normalized.split(",", 1)[0].strip()


def _singularize_token(token: str) -> str:
    lowered = token.lower()
    if lowered.endswith("ies") and len(lowered) > 3:
        return lowered[:-3] + "y"
    if lowered.endswith("s") and not lowered.endswith("ss") and len(lowered) > 1:
        return lowered[:-1]
    return lowered


def _extract_description_terms(description: str | None, limit: int = 3) -> list[str]:
    terms: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", _normalize_space(description).lower()):
        if token in _DESCRIPTION_STOPWORDS:
            continue
        if token in terms:
            continue
        terms.append(token)
        if len(terms) >= limit:
            break
    return terms


def _tokenize_terms(value: str | None) -> set[str]:
    return {_singularize_token(token) for token in re.findall(r"[a-z0-9]+", _normalize_space(value).lower())}


def _dedupe_terms(terms: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        normalized = _normalize_space(term)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped


def _lookup_mapping_value(value: object, key: str) -> str | None:
    if isinstance(value, dict):
        result = value.get(key)
    else:
        result = getattr(value, key, None)
    if result is None:
        return None
    return str(result)


def _extract_summary_snippet(summary_html: str | None, title: str, source_name: str) -> str:
    if not summary_html:
        return ""
    text = _normalize_space(BeautifulSoup(summary_html, "html.parser").get_text(" ", strip=True))
    lowered = text.lower()
    normalized_title = _normalize_space(title)
    if normalized_title and lowered.startswith(normalized_title.lower()):
        text = text[len(normalized_title) :].strip(" -:|")
    normalized_source = _normalize_space(source_name)
    if normalized_source and text.lower().endswith(normalized_source.lower()):
        text = text[: -len(normalized_source)].strip(" -:|")
    return _normalize_space(text)


def _category_fully_covered(primary_term: str | None, category_name: str | None) -> bool:
    primary_tokens = _tokenize_terms(primary_term)
    category_tokens = _tokenize_terms(category_name)
    return bool(category_tokens) and category_tokens.issubset(primary_tokens)


def _build_fallback_news_query(product: dict) -> str:
    primary_term = (
        _strip_variant_suffix(product.get("model_name"))
        or _strip_variant_suffix(product.get("product_name"))
        or _normalize_space(product.get("category_name"))
    )
    category_name = _normalize_space(product.get("category_name"))
    terms = [primary_term]
    if category_name and not _category_fully_covered(primary_term, category_name):
        terms.append(category_name)
    if len(_tokenize_terms(" ".join(terms))) <= 1:
        terms.extend(_extract_description_terms(product.get("description"), limit=1))
    return " ".join(_dedupe_terms(terms))


def _build_broader_news_query(product: dict) -> str:
    return (
        _strip_variant_suffix(product.get("model_name"))
        or _strip_variant_suffix(product.get("product_name"))
        or _normalize_space(product.get("category_name"))
    )


def _sanitize_search_query(raw_query: str) -> str:
    lines = [line.strip().strip("`") for line in str(raw_query).splitlines() if line.strip()]
    if not lines:
        return ""
    text = _QUERY_LABEL_RE.sub("", lines[0]).strip(" \"'.")
    text = _normalize_space(text)
    if not text:
        return ""
    words = text.split()
    if len(words) > 8:
        words = words[:8]
    return " ".join(words)


def _is_valid_search_query(query: str) -> bool:
    normalized = _normalize_space(query).lower()
    if not normalized:
        return False
    if any(phrase in normalized for phrase in _INVALID_QUERY_PHRASES):
        return False
    if "when:" in normalized:
        return False
    return len(normalized.split()) >= 1


def _build_citations(items: list[dict]) -> list[dict[str, str]]:
    return [{"title": x["title"], "url": x.get("publisher_url") or x["rss_link"]} for x in items]


def _truncate_summary_text(text: str, max_words: int = 500) -> str:
    trimmed = _normalize_space(text)
    if not trimmed:
        return trimmed
    words = trimmed.split()
    if len(words) <= max_words:
        return trimmed
    return " ".join(words[:max_words]).strip()


def _build_rss_evidence_item(entry: dict) -> dict:
    title = _normalize_space(entry.get("title"))
    rss_link = _normalize_space(entry.get("link"))
    publisher_url = _resolve_publisher_url(rss_link) if rss_link else ""
    source = entry.get("source")
    source_name = _normalize_space(_lookup_mapping_value(source, "title"))
    published_at = _normalize_space(entry.get("published"))
    summary_snippet = _extract_summary_snippet(entry.get("summary"), title, source_name)
    is_valid_evidence = bool(title and (summary_snippet or source_name or published_at or publisher_url))
    error_message = None if is_valid_evidence else "Insufficient search result metadata"
    return {
        "title": title,
        "rss_link": rss_link,
        "publisher_url": publisher_url or None,
        "source_name": source_name or None,
        "published_at": published_at or None,
        "summary_snippet": summary_snippet or None,
        "fetch_status": "rss_ready" if is_valid_evidence else "skipped",
        "is_valid_evidence": is_valid_evidence,
        "error_message": error_message,
    }


def _build_trend_prompt(product: dict, search_query: str, items: list[dict]) -> str:
    evidence_lines: list[str] = []
    for idx, item in enumerate(items, start=1):
        evidence_lines.append(
            "\n".join(
                [
                    f"{idx}. title: {item['title']}",
                    f"   source: {item.get('source_name') or 'Unknown source'}",
                    f"   published: {item.get('published_at') or 'Unknown date'}",
                    f"   snippet: {item.get('summary_snippet') or 'No snippet available'}",
                    f"   url: {item.get('publisher_url') or item['rss_link']}",
                ]
            )
        )
    return (
        "You are preparing a product trend brief for a business user.\n"
        "Use only the search-result metadata below (title, source, date, snippet, URL). "
        "Do not invent facts beyond the provided results.\n"
        "Write a concise plain-language summary in <=220 words. "
        "Focus on business-relevant demand signals, launches, innovation, competition, adoption, "
        "or market movement related to the selected product.\n"
        "If evidence looks weak, generic, or mixed, say that plainly in the summary.\n"
        "Do not output JSON.\n"
        f"Search query used: {search_query}\n"
        f"Selected product: {product}\n"
        "Search results:\n"
        + "\n".join(evidence_lines)
    )


class NewsTrendService:
    def __init__(self, settings: Settings, ai_logging_service: AILoggingService):
        self._settings = settings
        self._ai_logging_service = ai_logging_service

    def _generate_search_query(self, product: dict, user_identity: str) -> str:
        fallback_query = _build_fallback_news_query(product)
        prompt = (
            "Generate one broad Google News search query for product-related business trend research.\n"
            "Goal: maximize recall while staying relevant to the selected product.\n"
            "Prefer a broader query over an overly specific one.\n"
            "Use 2 to 5 high-signal terms when possible.\n"
            "Do not include dates, years, time filters, or explanations.\n"
            "Avoid long adjective chains copied from the product description.\n"
            "Use category or model only when needed to disambiguate generic product names.\n"
            "Return exactly one plain-text query string. No markdown.\n"
            f"Selected product: product_name={product.get('product_name')}; "
            f"category_name={product.get('category_name')}; "
            f"model_name={product.get('model_name')}; "
            f"description={product.get('description')}\n"
            f"If metadata are sparse, use this fallback style: {fallback_query}\n"
        )
        raw_query = self._ai_logging_service.call_with_logging(
            step_name="trend_query",
            model_name=self._settings.openai_deployment,
            ai_input_raw=prompt,
            logged_in_user_identity=user_identity,
            callback=lambda: invoke_model(self._settings, prompt),
        )
        search_query = _sanitize_search_query(raw_query)
        if _is_valid_search_query(search_query):
            return search_query
        logger.warning(
            "AI trend query invalid; using fallback. product_id=%s raw_query=%s fallback_query=%s",
            product.get("product_id"),
            raw_query,
            fallback_query,
        )
        return fallback_query

    def _parse_rss_results(self, search_query: str):
        query = quote_plus(search_query)
        rss_url = (
            f"{self._settings.google_news_rss_base_url}?q={query}&hl=en-US&gl=US&ceid=US:en"
        )
        parsed = feedparser.parse(rss_url)
        if getattr(parsed, "bozo", False) and not parsed.entries:
            logger.error("RSS dependency failure for query=%s url=%s", search_query, rss_url)
            raise AppError("RSS dependency failure. Please retry or reset.", 502)
        return parsed

    def search_trends(self, product: dict, user_identity: str) -> dict:
        attempted_queries = _dedupe_terms(
            [
                self._generate_search_query(product, user_identity),
                _build_fallback_news_query(product),
                _build_broader_news_query(product),
            ]
        )
        parsed = None
        search_query = ""
        for idx, candidate_query in enumerate(attempted_queries, start=1):
            logger.info(
                "Trend search query attempt: product_id=%s product_name=%s attempt=%s query=%s",
                product.get("product_id"),
                product.get("product_name"),
                idx,
                candidate_query,
            )
            parsed = self._parse_rss_results(candidate_query)
            search_query = candidate_query
            if parsed.entries:
                break
            logger.info(
                "Trend search query returned zero RSS entries: product_id=%s attempt=%s query=%s",
                product.get("product_id"),
                idx,
                candidate_query,
            )
        if parsed is None:
            raise AppError("Trend search failed before RSS lookup.", 500)
        news_items = [_build_rss_evidence_item(entry) for entry in parsed.entries[:10]]
        valid_items = [item for item in news_items if item["is_valid_evidence"]]
        fetch_errors = [
            f"{item.get('title') or 'Untitled result'}: {item['error_message']}"
            for item in news_items
            if item.get("error_message")
        ]
        if not news_items:
            fetch_errors.append(f"No RSS results returned for query: {search_query}")
        valid_ratio = len(valid_items) / max(len(news_items), 1)
        citations = _build_citations(valid_items)

        if not valid_items:
            summary_text = "未检索到足够可用于总结的搜索结果，请尝试重新搜索或更换产品。"
            logger.warning(
                "Trend search returned no usable RSS metadata: product=%s query=%s total_items=%s",
                product.get("product_id"),
                search_query,
                len(news_items),
            )
        else:
            prompt = _build_trend_prompt(product, search_query, valid_items)
            summary_text = self._ai_logging_service.call_with_logging(
                step_name="trend_summary",
                model_name=self._settings.openai_deployment,
                ai_input_raw=prompt,
                logged_in_user_identity=user_identity,
                callback=lambda: invoke_model(self._settings, prompt),
            )
            summary_text = _truncate_summary_text(summary_text)

        return {
            "search_query": search_query,
            "news_items": news_items,
            "summary": {
                "summary_text": summary_text,
                "citations": citations,
                "valid_ratio": valid_ratio,
                "fetch_errors": fetch_errors,
            },
        }
