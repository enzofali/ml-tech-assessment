import pytest
from app.transcript_parser import (
    TranscriptFormat,
    UnsupportedTranscriptFormatError,
    detect_format,
    parse,
)


# ---------------------------------------------------------------------------
# detect_format — auto-detection from content signatures
# ---------------------------------------------------------------------------

class TestDetectFormat:
    def test_plain_text_detected(self):
        assert detect_format("Alice: Hello\n\nBob: Hi.") is TranscriptFormat.PLAIN

    def test_vtt_detected_by_webvtt_header(self):
        assert detect_format("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello.") is TranscriptFormat.VTT

    def test_vtt_detected_with_leading_whitespace(self):
        assert detect_format("  \nWEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello.") is TranscriptFormat.VTT

    def test_vtt_detected_with_bom(self):
        assert detect_format("﻿WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello.") is TranscriptFormat.VTT

    def test_vtt_detected_with_metadata_on_header_line(self):
        assert detect_format("WEBVTT Kind: captions\n\n00:00:01.000 --> 00:00:04.000\nHello.") is TranscriptFormat.VTT

    def test_srt_detected_by_sequence_and_timestamp(self):
        srt = "1\n00:00:01,000 --> 00:00:04,000\nHello."
        assert detect_format(srt) is TranscriptFormat.SRT

    def test_srt_detected_with_multiple_cues(self):
        srt = "1\n00:00:01,000 --> 00:00:04,000\nHello.\n\n2\n00:00:05,000 --> 00:00:08,000\nWorld."
        assert detect_format(srt) is TranscriptFormat.SRT

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            detect_format("")

    def test_plain_with_numbers_not_confused_for_srt(self):
        # A plain transcript that happens to start with a number
        assert detect_format("1 thing I want to discuss today:\nAlice: Let's go.") is TranscriptFormat.PLAIN

    def test_digit_line_followed_by_non_timestamp_is_plain(self):
        # Standalone digit line, but the next line isn't an SRT timestamp.
        assert detect_format("1\nAlice: just a numbered note, not SRT.") is TranscriptFormat.PLAIN

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            detect_format("   \n\t  ")


# ---------------------------------------------------------------------------
# parse() — auto-detect and transform
# ---------------------------------------------------------------------------

class TestParsePlain:
    def test_returns_text_unchanged(self):
        text = "Alice: Hello\n\nBob: Hi there."
        assert parse(text) == text

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            parse("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            parse("   \n\t\n  ")


class TestParseVTT:
    _BASIC = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:04.000\n"
        "Alice | Coach: How have you been?\n\n"
        "00:00:05.000 --> 00:00:08.000\n"
        "Bob: Much better, thanks."
    )

    def test_strips_webvtt_header(self):
        assert "WEBVTT" not in parse(self._BASIC)

    def test_strips_timestamp_lines(self):
        assert "-->" not in parse(self._BASIC)

    def test_preserves_speaker_text(self):
        result = parse(self._BASIC)
        assert "Alice | Coach: How have you been?" in result
        assert "Bob: Much better, thanks." in result

    def test_speaker_turns_separated_by_blank_line(self):
        assert "\n\n" in parse(self._BASIC)

    def test_voice_tags_converted_to_speaker_label(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:04.000\n"
            "<v Alice>How have you been?</v>\n\n"
            "00:00:05.000 --> 00:00:08.000\n"
            "<v Bob>Much better.</v>"
        )
        result = parse(vtt)
        assert "Alice: How have you been?" in result
        assert "Bob: Much better." in result

    def test_html_formatting_tags_stripped(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:04.000\n"
            "<b>Alice</b>: This is <i>important</i>."
        )
        result = parse(vtt)
        assert "<b>" not in result
        assert "<i>" not in result
        assert "Alice" in result
        assert "important" in result

    def test_cue_identifiers_before_timestamp_ignored(self):
        vtt = (
            "WEBVTT\n\n"
            "intro\n"
            "00:00:01.000 --> 00:00:04.000\n"
            "Alice: Hello.\n\n"
            "42\n"
            "00:00:05.000 --> 00:00:08.000\n"
            "Bob: Hi."
        )
        result = parse(vtt)
        assert "intro" not in result
        assert "42" not in result
        assert "Alice: Hello." in result
        assert "Bob: Hi." in result

    def test_note_blocks_discarded(self):
        vtt = (
            "WEBVTT\n\n"
            "NOTE This is a comment\n\n"
            "00:00:01.000 --> 00:00:04.000\n"
            "Alice: Hello."
        )
        result = parse(vtt)
        assert "NOTE" not in result
        assert "Alice: Hello." in result

    def test_short_timestamp_format_mm_ss(self):
        vtt = "WEBVTT\n\n00:01.000 --> 00:04.000\nAlice: Short format."
        result = parse(vtt)
        assert "-->" not in result
        assert "Alice: Short format." in result

    def test_timestamp_with_positioning_settings_stripped(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:04.000 align:start position:0%\n"
            "Alice: Positioned cue.\n\n"
            "00:00:05.000 --> 00:00:08.000 line:90%\n"
            "Bob: Another cue."
        )
        result = parse(vtt)
        assert "-->" not in result
        assert "align:start" not in result
        assert "Alice: Positioned cue." in result
        assert "Bob: Another cue." in result

    def test_inline_timestamp_cue_tags_stripped(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:05.000\n"
            "Alice: Good <00:00:01.500>morning, <00:00:02.000>everyone."
        )
        result = parse(vtt)
        assert "<00:" not in result
        assert "Alice: Good morning, everyone." in result

    def test_multi_line_cue_preserved(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:06.000\n"
            "Alice: First line of the turn.\n"
            "Alice: Second line of the same turn."
        )
        result = parse(vtt)
        assert "First line of the turn." in result
        assert "Second line of the same turn." in result

    def test_webvtt_header_with_metadata_discarded(self):
        vtt = "WEBVTT Kind: captions\n\n00:00:01.000 --> 00:00:04.000\nAlice: Hello."
        result = parse(vtt)
        assert "WEBVTT" not in result
        assert "Kind" not in result
        assert "Alice: Hello." in result

    def test_realistic_zoom_vtt(self):
        vtt = (
            "WEBVTT\n\n"
            "1\n"
            "00:00:00.000 --> 00:00:04.120 align:start\n"
            "Coach: How have <00:00:01.500>you been since our last session?\n\n"
            "2\n"
            "00:00:04.500 --> 00:00:08.000 align:start\n"
            "Client: <00:00:04.800>Much better. I finished the report.\n\n"
            "3\n"
            "00:00:08.500 --> 00:00:12.000 align:start\n"
            "Coach: <00:00:09.000>Great. What helped you push through?"
        )
        result = parse(vtt)
        assert "WEBVTT" not in result
        assert "-->" not in result
        assert "<00:" not in result
        assert "align:start" not in result
        assert "Coach: How have you been since our last session?" in result
        assert "Client: Much better. I finished the report." in result
        assert "Coach: Great. What helped you push through?" in result

    def test_empty_vtt_raises_unsupported_format(self):
        with pytest.raises(UnsupportedTranscriptFormatError, match="no readable cues"):
            parse("WEBVTT\n\n")

    def test_vtt_with_only_stripped_content_raises(self):
        # Cue exists but its content is entirely markup that gets stripped to nothing.
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<b></b>"
        with pytest.raises(UnsupportedTranscriptFormatError):
            parse(vtt)

    def test_vtt_with_no_valid_timestamp_raises(self):
        # Header present but every block lacks a timestamp line.
        vtt = "WEBVTT\n\nintro\nAlice: stray content with no timestamp"
        with pytest.raises(UnsupportedTranscriptFormatError):
            parse(vtt)

    def test_vtt_with_crlf_line_endings(self):
        vtt = "WEBVTT\r\n\r\n00:00:01.000 --> 00:00:04.000\r\nAlice: Hi."
        result = parse(vtt)
        assert "Alice: Hi." in result
        assert "\r" not in result


class TestParseSRT:
    _BASIC = (
        "1\n"
        "00:00:01,000 --> 00:00:04,000\n"
        "Alice | Coach: How have you been?\n\n"
        "2\n"
        "00:00:05,000 --> 00:00:08,000\n"
        "Bob: Much better, thanks."
    )

    def test_strips_sequence_numbers(self):
        lines = parse(self._BASIC).splitlines()
        assert not any(line.strip().isdigit() for line in lines)

    def test_strips_timestamp_lines(self):
        assert "-->" not in parse(self._BASIC)

    def test_preserves_speaker_text(self):
        result = parse(self._BASIC)
        assert "Alice | Coach: How have you been?" in result
        assert "Bob: Much better, thanks." in result

    def test_speaker_turns_separated_by_blank_line(self):
        assert "\n\n" in parse(self._BASIC)

    def test_html_tags_stripped(self):
        srt = "1\n00:00:01,000 --> 00:00:04,000\n<b>Alice</b>: This is <i>key</i>."
        result = parse(srt)
        assert "<b>" not in result
        assert "<i>" not in result
        assert "Alice" in result
        assert "key" in result

    def test_multi_line_cue_preserved(self):
        srt = (
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "Alice: First line.\n"
            "Alice: Second line."
        )
        result = parse(srt)
        assert "First line." in result
        assert "Second line." in result

    def test_empty_srt_raises(self):
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            parse("")

    def test_srt_with_only_stripped_content_raises(self):
        srt = "1\n00:00:01,000 --> 00:00:04,000\n<b></b>"
        with pytest.raises(UnsupportedTranscriptFormatError):
            parse(srt)


# ---------------------------------------------------------------------------
# Cross-format: output is always markup-free plain text
# ---------------------------------------------------------------------------

def test_vtt_output_contains_no_markup():
    vtt = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:10.000\n"
        "<v Coach>What are your goals?</v>\n\n"
        "00:00:11.000 --> 00:00:15.000\n"
        "<v Client>Ship the Q2 feature.</v>"
    )
    result = parse(vtt)
    assert "WEBVTT" not in result
    assert "-->" not in result
    assert "<v" not in result
    assert "Coach: What are your goals?" in result
    assert "Client: Ship the Q2 feature." in result


class TestUnsupportedFormatError:
    """The error contract the API relies on for graceful 422 responses."""

    def test_subclasses_value_error(self):
        # routes.py uses `except ValueError` — the new error must be caught by it.
        assert issubclass(UnsupportedTranscriptFormatError, ValueError)

    def test_message_guides_user_to_reupload(self):
        with pytest.raises(UnsupportedTranscriptFormatError) as exc_info:
            parse("WEBVTT\n\n")
        message = str(exc_info.value)
        assert "re-upload" in message.lower()
        assert "VTT" in message or "SRT" in message

    def test_carries_detected_format(self):
        with pytest.raises(UnsupportedTranscriptFormatError) as exc_info:
            parse("WEBVTT\n\n")
        assert exc_info.value.format is TranscriptFormat.VTT


def test_srt_output_contains_no_markup():
    srt = (
        "1\n00:00:01,000 --> 00:00:04,000\nCoach: Hello.\n\n"
        "2\n00:00:05,000 --> 00:00:08,000\nClient: Hi."
    )
    result = parse(srt)
    assert "-->" not in result
    assert not any(l.strip().isdigit() for l in result.splitlines())
    assert "Coach: Hello." in result
    assert "Client: Hi." in result
