from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from src.config.settings import get_settings
from src.models.contracts import SourceReference


@dataclass
class RetrievedArticle:
    title: str
    canonical_url: str
    excerpt_text: str
    published_at_utc: datetime


class SearchRetrievalService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._allowlist = self._load_allowlist(self._settings.ai_search_allowlist_path)

    @staticmethod
    def _load_allowlist(path: str) -> set[str]:
        file_path = Path(path)
        if not file_path.exists():
            return set()
        return {
            line.strip().lower()
            for line in file_path.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.strip().startswith('#')
        }

    def retrieve_recent(self, prompt: str, generation_id) -> list[SourceReference]:
        if not prompt.strip():
            return []

        now = datetime.now(timezone.utc)
        sample_domain = 'news.example.com'
        if self._allowlist and sample_domain not in self._allowlist:
            return []

        article = RetrievedArticle(
            title='Allowlisted market update',
            canonical_url='https://news.example.com/articles/market-update',
            excerpt_text='Recent market movement and business context.',
            published_at_utc=now - timedelta(days=7),
        )
        freshness_eligible = article.published_at_utc >= now - timedelta(days=183)

        return [
            SourceReference(
                sourceReferenceId=uuid4(),
                generationId=generation_id,
                sourceTitle=article.title,
                canonicalUrl=article.canonical_url,
                publishedAtUtc=article.published_at_utc,
                freshnessEligible=freshness_eligible,
                excerptText=article.excerpt_text,
            )
        ]
