from __future__ import annotations

import json
import re
from typing import Any

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)


def clean_json_text(text: str) -> str:
    stripped_text = text.strip()

    fenced_match = _FENCED_JSON_RE.search(stripped_text)
    if fenced_match:
        return fenced_match.group(1).strip()

    if stripped_text.startswith("{") and stripped_text.endswith("}"):
        return stripped_text

    start_index = stripped_text.find("{")
    end_index = stripped_text.rfind("}")
    if start_index != -1 and end_index != -1 and end_index > start_index:
        return stripped_text[start_index : end_index + 1].strip()

    return stripped_text


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned_text = clean_json_text(text)
    return json.loads(cleaned_text)
