"""Clean YouTube VTT/SRT subtitle text for machine processing."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

MIN_MEANINGFUL_CUE_SEC = 0.011

_RE_INLINE_TS = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>")
_RE_C_TAG = re.compile(r"</?c[^>]*>", re.I)
_RE_GENERIC_XMLISH = re.compile(r"<[^>]{1,48}>")
_RE_BRACKET_META = re.compile(r"\[[^\]]{1,32}\]")
_RE_MULTI_SPACE = re.compile(r"[ \t\u3000]+")


def clean_subtitle_plain_text(text: str, bracket_sound_policy: str) -> str:
    """Return plain text from one subtitle cue body."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = _RE_INLINE_TS.sub("", cleaned)
    cleaned = _RE_C_TAG.sub("", cleaned)
    cleaned = _RE_GENERIC_XMLISH.sub("", cleaned)
    if bracket_sound_policy == "remove":
        cleaned = _RE_BRACKET_META.sub("", cleaned)

    lines = []
    for line in cleaned.split("\n"):
        line = line.strip()
        line = re.sub(r"\balign\s*:\s*start\b.*$", "", line, flags=re.I)
        line = re.sub(r"\bposition\s*:\s*\d+%.*$", "", line, flags=re.I)
        line = line.strip()
        if line:
            lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = _RE_MULTI_SPACE.sub(" ", cleaned.replace("\n", " "))
    return cleaned.strip()


def normalize_text_for_dedupe(text: str) -> str:
    """Normalize subtitle text before adjacent duplicate checks."""
    return _RE_MULTI_SPACE.sub(" ", text.strip())


def srt_ts_to_seconds(timestamp: str) -> float:
    """Convert an SRT timestamp in HH:MM:SS,mmm format to seconds."""
    hh, mm, sec_ms = timestamp.split(":")
    sec, ms = sec_ms.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(sec) + int(ms) / 1000.0


def parse_srt_entries(srt_text: str) -> List[Tuple[str, str, str]]:
    """Parse numbered SRT cue blocks into (start, end, body) tuples."""
    entries: List[Tuple[str, str, str]] = []
    for raw_block in re.split(r"\n\s*\n", srt_text.strip()):
        lines = [line for line in raw_block.strip().split("\n") if line.strip()]
        if len(lines) < 2:
            continue

        offset = 0
        if re.fullmatch(r"\d+", lines[0].strip()):
            offset = 1
        if len(lines) <= offset:
            continue

        match = re.match(
            r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
            lines[offset].strip(),
        )
        if not match:
            continue

        body = "\n".join(lines[offset + 1 :]).strip()
        entries.append((match.group(1), match.group(2), body))
    return entries


def finalize_srt_machine_readable(
    srt_text: str, bracket_sound_policy: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """Clean, dedupe, and return machine-readable SRT and segment metadata."""
    entries = parse_srt_entries(srt_text)
    cleaned_steps: List[Tuple[str, str, str]] = []
    for start, end, body in entries:
        cleaned_body = clean_subtitle_plain_text(body, bracket_sound_policy)
        if cleaned_body:
            cleaned_steps.append((start, end, cleaned_body))

    merged: List[Tuple[str, str, str]] = []
    prev_norm: Optional[str] = None
    for start, end, text in cleaned_steps:
        start_sec = srt_ts_to_seconds(start)
        end_sec = srt_ts_to_seconds(end)
        duration = max(0.0, end_sec - start_sec)
        norm = normalize_text_for_dedupe(text)
        if not norm:
            continue
        if duration < MIN_MEANINGFUL_CUE_SEC:
            continue
        if prev_norm is not None and norm == prev_norm:
            continue

        merged.append((start, end, text))
        prev_norm = norm

    segments: List[Dict[str, Any]] = []
    lines_out: List[str] = []
    for index, (start, end, text) in enumerate(merged, start=1):
        lines_out.append(f"{index}\n{start} --> {end}\n{text}\n")
        segments.append(
            {
                "start": start,
                "end": end,
                "start_sec": round(srt_ts_to_seconds(start), 3),
                "end_sec": round(srt_ts_to_seconds(end), 3),
                "text": text,
            }
        )

    body = "\n".join(lines_out).strip()
    if body:
        body += "\n"
    return body, segments
