from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


CANONICAL_DIMENSIONS = {"business_group", "product_line_5", "month", "overall"}

ENTITY_DISPLAY_LABELS = {
    "business_group": "事業群",
    "product_line_5": "產品線",
    "month": "月份",
    "overall": "總體",
    "platform": "事業群",
    "group": "事業群",
}

ENTITY_SYNONYMS = {
    "business_group": [
        "新事業群",
        "事業群",
        "BU",
        "bu",
        "Business Unit",
        "business unit",
        "平台",
        "平臺",
        "platform",
    ],
    "product_line_5": [
        "五大產品線",
        "產品線",
        "product line",
        "Product Line",
        "product_line",
    ],
    "month": ["月份", "month"],
    "overall": ["總體", "整體", "overall", "全部", "全體"],
}

BUILTIN_ENTITY_ALIASES = {
    "business_group": {
        "3通路方案": "3通路方案",
        "通路方案": "3通路方案",
        "1網通+技鋼": "1網通+技鋼",
        "網通+技鋼": "1網通+技鋼",
        "網通技鋼": "1網通+技鋼",
        "4筆電+盈嘉": "4筆電+盈嘉",
        "筆電+盈嘉": "4筆電+盈嘉",
        "筆電盈嘉": "4筆電+盈嘉",
        "2技宸": "2技宸",
        "技宸": "2技宸",
        "5百事益": "5百事益",
        "百事益": "5百事益",
        "6雲城": "6雲城",
        "雲城": "6雲城",
        "7製造": "7製造",
        "製造": "7製造",
    },
    "product_line_5": {
        "Server": "Server",
        "server": "Server",
        "SERVER": "Server",
        "IOT": "IOT",
        "iot": "IOT",
        "IoT": "IOT",
    },
}


@dataclass(frozen=True)
class EntityResolution:
    value: str | None
    ambiguous: bool = False
    candidates: tuple[str, ...] = ()


def display_label_for_dimension(dimension: str | None) -> str:
    return ENTITY_DISPLAY_LABELS.get(str(dimension or ""), str(dimension or ""))


def normalize_entity_dimension(value: str | None) -> str | None:
    if value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered in {"platform", "group", "business_group"}:
        return "business_group"
    if lowered in {"product_line_5", "product line", "product_line"}:
        return "product_line_5"
    if lowered in {"month", "月份"}:
        return "month"
    if lowered in {"overall", "總體", "整體"}:
        return "overall"
    for dimension, synonyms in ENTITY_SYNONYMS.items():
        if any(lowered == synonym.lower() for synonym in synonyms):
            return dimension
    return None


def text_has_dimension_synonym(text: str, dimension: str) -> bool:
    lowered = text.lower()
    synonyms = ENTITY_SYNONYMS.get(dimension, [])
    return any(synonym.lower() in lowered or synonym in text for synonym in synonyms)


def normalize_entity_text(value: str | None) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_\-+／/\\|()（）\[\]{}]", "", text)
    return text


def resolve_entity_value(
    input_text: str,
    entity_dimension: str,
    candidates: Iterable[str] | None = None,
) -> str | None:
    return resolve_entity_value_with_status(input_text, entity_dimension, candidates).value


def resolve_entity_value_with_status(
    input_text: str,
    entity_dimension: str,
    candidates: Iterable[str] | None = None,
) -> EntityResolution:
    dimension = normalize_entity_dimension(entity_dimension) or entity_dimension
    text = str(input_text or "").strip()
    normalized_text = normalize_entity_text(text)
    if not text:
        return EntityResolution(value=None)

    aliases = BUILTIN_ENTITY_ALIASES.get(dimension, {})
    for alias, canonical in aliases.items():
        if alias in text or normalize_entity_text(alias) in normalized_text:
            return EntityResolution(value=canonical)

    candidate_values = [str(candidate) for candidate in (candidates or []) if str(candidate or "").strip()]
    if not candidate_values:
        return EntityResolution(value=None)

    exact = [candidate for candidate in candidate_values if text == candidate]
    if len(exact) == 1:
        return EntityResolution(value=exact[0])
    if len(exact) > 1:
        return EntityResolution(value=None, ambiguous=True, candidates=tuple(sorted(set(exact))))

    normalized_matches = [
        candidate for candidate in candidate_values if normalize_entity_text(candidate) == normalized_text
    ]
    if len(normalized_matches) == 1:
        return EntityResolution(value=normalized_matches[0])
    if len(normalized_matches) > 1:
        return EntityResolution(value=None, ambiguous=True, candidates=tuple(sorted(set(normalized_matches))))

    contains_matches = [
        candidate
        for candidate in candidate_values
        if normalized_text and normalized_text in normalize_entity_text(candidate)
    ]
    if len(contains_matches) == 1:
        return EntityResolution(value=contains_matches[0])
    if len(contains_matches) > 1:
        return EntityResolution(value=None, ambiguous=True, candidates=tuple(sorted(set(contains_matches))))

    reverse_contains = [
        candidate
        for candidate in candidate_values
        if normalize_entity_text(candidate) and normalize_entity_text(candidate) in normalized_text
    ]
    if len(reverse_contains) == 1:
        return EntityResolution(value=reverse_contains[0])
    if len(reverse_contains) > 1:
        return EntityResolution(value=None, ambiguous=True, candidates=tuple(sorted(set(reverse_contains))))

    return EntityResolution(value=None)
