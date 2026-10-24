"""
Deterministic supplements when Gemini JSON extraction returns sparse layout metrics.

Parses feet/inches and common phrases from user prompt + CAD DSL so IRC screening
can score when text explicitly states dimensions (even if vision extraction misses).
"""

from __future__ import annotations

import re
from typing import Any

_WIDTH_RE = re.compile(r"\b(\d{2})\s*[\"\u2033″]")
_FT_IN_PAIR_RE = re.compile(
    r"(\d+)\s*[-']?\s*(\d+)\s*[\"\u2033″]\s*[x×]\s*(\d+)\s*[-']?\s*(\d+)\s*[\"\u2033″]",
    re.IGNORECASE,
)
# Typical CAD strings: 14'-0" x 12'-0" (prime between ft and inches)
_FT_PRIME_PAIR_RE = re.compile(
    r"(\d+)\s*'\s*-?\s*(\d+)\s*[\"\u2033″]\s*[x×]\s*(\d+)\s*'\s*-?\s*(\d+)\s*[\"\u2033″]",
    re.IGNORECASE,
)
_FT_SIMPLE_PAIR_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*ft\s*(?:by|[x×])\s*(\d+(?:\.\d+)?)\s*ft",
    re.IGNORECASE,
)
_CEILING_RE = re.compile(
    r"(?:ceiling|ceil\.?)\s*(?:height)?\s*[:\s]*(\d+)\s*[-']?\s*(\d+)\s*[\"\u2033″]",
    re.IGNORECASE,
)
_CEILING_FT_RE = re.compile(
    r"(?:ceiling|ceil\.?)\s*(?:height)?\s*[:\s]*(\d+)\s*(?:ft|'(?!\d))",
    re.IGNORECASE,
)
_EGRESS_NEAR_RE = re.compile(
    r"(?:egress|clear\s+opening)[^\n]{0,120}?(\d+(?:\.\d+)?)\s*(?:sq\.?\s*)?(?:ft|sq\s*ft)",
    re.IGNORECASE,
)
# WxH in inches on the same line as egress / net clear callouts → sq ft (width × height / 144).
_INCH_PAIR_RE = re.compile(
    r"(\d{1,2})\s*[\"\u2033″]\s*(?:[wW]\s*)?[x×]\s*(\d{1,2})\s*[\"\u2033″]",
    re.IGNORECASE,
)
_EGRESS_LINE_HINT = re.compile(
    r"(?:egress|net\s+clear|clear\s+opening|opening\s+for\s+screening)",
    re.IGNORECASE,
)
_STAIR_RISE_RE = re.compile(
    r"(?:rise|r\.)\s*[:\s]*(\d+(?:\.\d+)?)\s*[\"\u2033″]",
    re.IGNORECASE,
)
_STAIR_TREAD_RE = re.compile(
    r"(?:tread|t\.)\s*[:\s]*(\d+(?:\.\d+)?)\s*[\"\u2033″]",
    re.IGNORECASE,
)


def _dims_ft_in_to_area_sqft(snippet: str) -> float | None:
    for rx in (_FT_PRIME_PAIR_RE, _FT_IN_PAIR_RE):
        m = rx.search(snippet)
        if m:
            L = float(m.group(1)) + float(m.group(2)) / 12.0
            W = float(m.group(3)) + float(m.group(4)) / 12.0
            return round(L * W, 2)
    m2 = _FT_SIMPLE_PAIR_RE.search(snippet)
    if m2:
        return round(float(m2.group(1)) * float(m2.group(2)), 2)
    return None


def _extract_bedroom_area_sqft(full_text: str) -> float | None:
    """Prefer dimensions in the same region as the word bedroom."""
    text = full_text.replace("\u201d", '"').replace("\u201c", '"')
    for match in re.finditer(r"bedroom", text, re.IGNORECASE):
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 220)
        chunk = text[start:end]
        area = _dims_ft_in_to_area_sqft(chunk)
        if area:
            return area
    # Fallback: first plausible dimension pair in full text if bedroom mentioned anywhere
    if re.search(r"bedroom", text, re.IGNORECASE):
        area = _dims_ft_in_to_area_sqft(text)
        return area
    return None


def _extract_ceiling_ft(full_text: str) -> float | None:
    text = full_text.replace("\u201d", '"').replace("\u201c", '"')
    m = _CEILING_RE.search(text)
    if m:
        ft = float(m.group(1)) + float(m.group(2)) / 12.0
        return round(ft, 3)
    m2 = _CEILING_FT_RE.search(text)
    if m2:
        return float(m2.group(1))
    # Loose phrases: "9 ft ceilings", "9-foot ceiling", "ceilings 9 ft"
    for rx in (
        re.compile(r"\b(\d+)\s+ft\s+(?:ceil(?:ings)?)\b", re.IGNORECASE),
        re.compile(r"\b(\d+)\s*'\s+(?:ceil(?:ings)?)\b", re.IGNORECASE),
        re.compile(r"\b(\d+)\s*-\s*(?:foot|feet)\s+(?:ceil(?:ing)?)\b", re.IGNORECASE),
        re.compile(r"\b(?:ceil(?:ings)?)\s+(?:of|at|around|~)?\s*(\d+)\s*(?:ft|')\b", re.IGNORECASE),
    ):
        mm = rx.search(text)
        if mm:
            return float(mm.group(1))
    return None


def _door_widths_in(text: str) -> list[float]:
    seen = set()
    out: list[float] = []
    width_patterns = (
        _WIDTH_RE,
        re.compile(r"\b(\d{2})\s*(?:inch(?:es)?)\b", re.IGNORECASE),
    )
    for rx in width_patterns:
        for m in rx.finditer(text):
            w = float(m.group(1))
            if 28.0 <= w <= 48.0 and w not in seen:
                seen.add(w)
                out.append(w)
    return out


def _inch_pair_to_sqft(w_in: float, h_in: float) -> float:
    return round(w_in * h_in / 144.0, 4)


def _egress_areas_from_explicit_sqft(text: str) -> list[float]:
    areas: list[float] = []
    for m in _EGRESS_NEAR_RE.finditer(text):
        areas.append(float(m.group(1)))
    return areas


def _egress_areas_from_inch_pairs_in_egress_lines(text: str) -> list[float]:
    """
    Infer opening sq ft from WxH in inches on lines that mention egress / net clear / opening.
    Handles both '18\" W x 36\" H ... NET CLEAR' and 'egress ... 18\" x 36\"'.
    """
    areas: list[float] = []
    for line in text.replace("\u201d", '"').replace("\u201c", '"').splitlines():
        if not _EGRESS_LINE_HINT.search(line):
            continue
        for m in _INCH_PAIR_RE.finditer(line):
            w_in, h_in = float(m.group(1)), float(m.group(2))
            if not (12 <= w_in <= 96 and 12 <= h_in <= 96):
                continue
            areas.append(_inch_pair_to_sqft(w_in, h_in))
    return areas


def _egress_areas_sqft(text: str) -> list[float]:
    explicit = _egress_areas_from_explicit_sqft(text)
    inch_derived = _egress_areas_from_inch_pairs_in_egress_lines(text)
    return explicit + inch_derived


_BEDROOM_AB_SQFT_RE = re.compile(
    r"(?:bedroom\s+([AB]))\s*[^0-9\n]{0,45}?~?\s*\*?\*?(\d+)\s*(?:sq\.?\s*)?(?:ft|sf)\b",
    re.IGNORECASE,
)


def _labeled_bedroom_areas(blob: str) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for m in _BEDROOM_AB_SQFT_RE.finditer(blob):
        out.append((f"Bedroom {m.group(1)}", float(m.group(2))))
    return out


def _bedroom_ab_dims_areas(blob: str) -> list[tuple[str, float]]:
    text = blob.replace("\u201d", '"').replace("\u201c", '"')
    out: list[tuple[str, float]] = []
    for m in re.finditer(r"(?:bedroom\s+([AB]))", text, re.IGNORECASE):
        chunk = text[m.start() : m.start() + 220]
        area = _dims_ft_in_to_area_sqft(chunk)
        if area is not None:
            out.append((f"Bedroom {m.group(1)}", area))
    return out


def _stairs_from_text(text: str) -> dict[str, float | None] | None:
    rise_m = _STAIR_RISE_RE.search(text)
    tread_m = _STAIR_TREAD_RE.search(text)
    if not rise_m and not tread_m:
        return None
    return {
        "rise_in": float(rise_m.group(1)) if rise_m else None,
        "tread_in": float(tread_m.group(1)) if tread_m else None,
    }


def merge_heuristic_layout(llm_raw: Any, user_prompt: str, cad_dsl: str) -> dict[str, Any]:
    """
    Merge Gemini JSON with regex/heuristic fills. Never removes LLM fields;
    only fills missing metrics useful for IRC MVP checks.
    """
    base: dict[str, Any] = dict(llm_raw) if isinstance(llm_raw, dict) else {}
    blob = f"{user_prompt or ''}\n{cad_dsl or ''}"

    area = _extract_bedroom_area_sqft(blob)
    ceil_ft = _extract_ceiling_ft(blob)
    doors_h = _door_widths_in(blob)
    egress_h = _egress_areas_sqft(blob)
    stair_d = _stairs_from_text(blob)

    hr_list: list[dict[str, Any]] = []
    labeled_pairs = _labeled_bedroom_areas(blob)
    dim_ab = _bedroom_ab_dims_areas(blob)
    if labeled_pairs:
        for name, sq in labeled_pairs:
            hr_list.append({"name": name, "area_sqft": sq, "ceiling_ft": ceil_ft})
    elif dim_ab:
        for name, sq in dim_ab:
            hr_list.append({"name": name, "area_sqft": sq, "ceiling_ft": ceil_ft})
    else:
        area_one = area  # from _extract_bedroom_area_sqft(blob) above
        if area_one is not None or ceil_ft is not None:
            hr_list.append({"name": "Bedroom", "area_sqft": area_one, "ceiling_ft": ceil_ft})

    rooms: list[dict[str, Any]] = list(base.get("rooms") or [])
    if hr_list:
        for hr in hr_list:
            key = (hr.get("name") or "").strip().lower()
            merged_into_existing = False
            for r in rooms:
                if (r.get("name") or "").strip().lower() == key:
                    if r.get("area_sqft") is None and hr.get("area_sqft") is not None:
                        r["area_sqft"] = hr["area_sqft"]
                    if r.get("ceiling_ft") is None and hr.get("ceiling_ft") is not None:
                        r["ceiling_ft"] = hr["ceiling_ft"]
                    merged_into_existing = True
                    break
            if not merged_into_existing:
                rooms.append(dict(hr))

    doors_llm: list[dict[str, Any]] = list(base.get("doors_inches") or [])
    existing = {d.get("width_in") for d in doors_llm if d.get("width_in") is not None}
    for w in doors_h:
        if w not in existing:
            doors_llm.append({"width_in": w})
            existing.add(w)

    egress_llm = list(base.get("egress_windows_sqft") or [])
    llm_has_egress = any(e.get("area_sqft") is not None for e in egress_llm)
    if egress_h:
        if not llm_has_egress:
            egress_llm = [{"area_sqft": a} for a in egress_h]
        else:
            seen = {e.get("area_sqft") for e in egress_llm if e.get("area_sqft") is not None}
            for a in egress_h:
                if a not in seen:
                    egress_llm.append({"area_sqft": a})
                    seen.add(a)

    stairs_llm = base.get("stairs")
    if stair_d:
        if not isinstance(stairs_llm, dict):
            stairs_llm = {}
        if stairs_llm.get("rise_in") is None and stair_d.get("rise_in") is not None:
            stairs_llm["rise_in"] = stair_d["rise_in"]
        if stairs_llm.get("tread_in") is None and stair_d.get("tread_in") is not None:
            stairs_llm["tread_in"] = stair_d["tread_in"]
        base["stairs"] = stairs_llm if stairs_llm else None

    base["rooms"] = rooms
    base["doors_inches"] = doors_llm
    base["egress_windows_sqft"] = egress_llm
    return base
