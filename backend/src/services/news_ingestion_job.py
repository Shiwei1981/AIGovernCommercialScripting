from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class IngestionSummary:
    scanned: int
    indexed: int
    skipped: int


class NewsIngestionJob:
    def run(self, documents: list[dict]) -> IngestionSummary:
        six_month_cutoff = datetime.now(timezone.utc) - timedelta(days=183)
        scanned = len(documents)
        indexed = 0
        skipped = 0

        for item in documents:
            published = item.get('published_at_utc')
            canonical_url = item.get('canonical_url')
            if not canonical_url or not published:
                skipped += 1
                continue
            if published < six_month_cutoff:
                skipped += 1
                continue
            indexed += 1

        return IngestionSummary(scanned=scanned, indexed=indexed, skipped=skipped)
