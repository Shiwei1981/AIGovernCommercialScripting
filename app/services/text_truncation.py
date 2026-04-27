from __future__ import annotations

import re

_TOKEN_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]|[^\s\u3400-\u4dbf\u4e00-\u9fff]+")


def truncate_text_by_token_count(text: str, max_tokens: int) -> str:
    trimmed = text.strip()
    if not trimmed:
        return trimmed
    token_matches = list(_TOKEN_PATTERN.finditer(trimmed))
    if len(token_matches) <= max_tokens:
        return trimmed
    end_index = token_matches[max_tokens - 1].end()
    return trimmed[:end_index].rstrip()
