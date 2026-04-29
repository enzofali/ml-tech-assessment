"""
Transcript format detection and parsing — converts structured formats to plain
text before normalization and LLM injection.

Pipeline: raw input → parse() → normalize() → LLM

Supported formats (auto-detected from content):
  plain  — free-form text, no transformation
  VTT    — WebVTT (Zoom, Teams, Google Meet native export)
  SRT    — SubRip (legacy, still common in transcription services)

Errors:
  ValueError                         — input is empty or whitespace-only
  UnsupportedTranscriptFormatError   — input carries VTT/SRT signatures but no
                                       readable cues can be recovered
"""

import re
from collections.abc import Iterable
from enum import Enum


class TranscriptFormat(str, Enum):
    PLAIN = "plain"
    VTT = "vtt"
    SRT = "srt"


class UnsupportedTranscriptFormatError(ValueError):
    """Raised when input looks like a structured format but cannot be parsed.

    Carries a user-facing message that asks for a re-upload in a supported
    format. Subclasses ValueError so existing `except ValueError` handlers
    continue to catch it.
    """

    def __init__(self, fmt: TranscriptFormat, reason: str) -> None:
        self.format = fmt
        self.reason = reason
        super().__init__(
            f"Could not parse transcript as {fmt.value.upper()}: {reason}. "
            "Please re-upload in a supported format (plain text, WebVTT, or SRT)."
        )


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# VTT cue timestamp: 00:00.000 --> or 00:00:00.000 -->
_VTT_TIMESTAMP = re.compile(r"^(?:\d+:)?\d{2}:\d{2}\.\d{3}\s*-->")

# SRT cue timestamp: 00:00:00,000 -->
_SRT_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}\s*-->")

# VTT voice tag: <v Speaker Name>text</v>  →  "Speaker Name: text"
_VTT_VOICE = re.compile(r"<v\s+([^>]+)>(.*?)</v>", re.DOTALL)

# Any remaining HTML-like tags (<b>, <i>, <c.class>, inline timestamps <00:00:01.000>)
_HTML_TAGS = re.compile(r"<[^>]+>")

# Cue blocks are separated by one or more blank lines (tolerate stray spaces).
_BLOCK_SEPARATOR = re.compile(r"\n[ \t]*\n+")

_BOM = "﻿"

# Format-specific hints embedded in UnsupportedTranscriptFormatError messages.
# Tells the user exactly what to check before re-uploading.
_MALFORMED_HINTS: dict[TranscriptFormat, str] = {
    TranscriptFormat.VTT: (
        "no readable cues found — check that each cue has a timestamp line "
        "in the form `HH:MM:SS.mmm --> HH:MM:SS.mmm` (decimal separator is `.`)"
    ),
    TranscriptFormat.SRT: (
        "no readable cues found — check that each sequence number is followed "
        "by a timestamp in the form `HH:MM:SS,mmm --> HH:MM:SS,mmm` (decimal separator is `,`)"
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_format(text: str) -> TranscriptFormat:
    """Infer transcript format from content signatures.

    Raises ValueError if the input is empty or whitespace-only.
    """
    cleaned = _preclean(text)
    if not cleaned:
        raise ValueError("Cannot detect format: transcript is empty or whitespace-only.")
    if cleaned.startswith("WEBVTT"):
        return TranscriptFormat.VTT
    if _looks_like_srt(cleaned):
        return TranscriptFormat.SRT
    return TranscriptFormat.PLAIN


def parse(text: str) -> str:
    """Auto-detect format and return clean plain text suitable for LLM injection.

    Raises:
        ValueError: input is empty or whitespace-only.
        UnsupportedTranscriptFormatError: input was identified as VTT or SRT
            but no readable cues could be recovered (malformed file).
    """
    cleaned = _preclean(text)
    fmt = detect_format(cleaned)

    if fmt is TranscriptFormat.VTT:
        return _parse_cues(cleaned, fmt=fmt, timestamp=_VTT_TIMESTAMP, voice_tags=True)
    if fmt is TranscriptFormat.SRT:
        return _parse_cues(cleaned, fmt=fmt, timestamp=_SRT_TIMESTAMP, voice_tags=False)
    return cleaned


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _preclean(text: str) -> str:
    """Strip BOM, normalize line endings, trim outer whitespace.

    Centralized so detection and parsing always operate on the same canonical
    form — avoids subtle mismatches between the two passes.
    """
    return text.lstrip(_BOM).replace("\r\n", "\n").replace("\r", "\n").strip()


def _looks_like_srt(text: str) -> bool:
    """SRT blocks start with a sequence number followed by an SRT timestamp line."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines[:-1]):
        if line.isdigit():
            return bool(_SRT_TIMESTAMP.match(lines[i + 1]))
    return False


def _parse_cues(
    text: str,
    *,
    fmt: TranscriptFormat,
    timestamp: re.Pattern[str],
    voice_tags: bool,
) -> str:
    """Shared cue-block parser for VTT and SRT.

    Splits on blank lines, locates the timestamp line in each block, extracts
    the content lines that follow, and strips markup. Headers (WEBVTT) and
    NOTE blocks are discarded.

    Raises UnsupportedTranscriptFormatError if no usable cue content is
    recovered — the input had the format's signature but is effectively empty
    or malformed.
    """
    parts: list[str] = []

    for block in _BLOCK_SEPARATOR.split(text):
        lines = block.strip().splitlines()
        if not lines:
            continue
        if lines[0].startswith(("WEBVTT", "NOTE")):
            continue

        ts_idx = next((i for i, l in enumerate(lines) if timestamp.match(l)), None)
        if ts_idx is None:
            continue

        content = _clean_lines(lines[ts_idx + 1:], voice_tags=voice_tags)
        if content:
            parts.append(content)

    if not parts:
        raise UnsupportedTranscriptFormatError(fmt, _MALFORMED_HINTS[fmt])

    return "\n\n".join(parts)


def _clean_lines(lines: Iterable[str], *, voice_tags: bool) -> str:
    processed: list[str] = []
    for line in lines:
        if voice_tags:
            line = _VTT_VOICE.sub(r"\1: \2", line)
        line = _HTML_TAGS.sub("", line).strip()
        if line:
            processed.append(line)
    return "\n".join(processed)
