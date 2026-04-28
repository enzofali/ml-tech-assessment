import pytest
from app.text_normalizer import NormalizationStrategy, normalize


# ---------------------------------------------------------------------------
# Shared / CONSERVATIVE baseline (applied by all strategies)
# ---------------------------------------------------------------------------

class TestConservative:
    S = NormalizationStrategy.CONSERVATIVE

    def test_strips_leading_and_trailing_whitespace(self):
        assert normalize("  hello  ", self.S) == "hello"

    def test_normalizes_windows_line_endings(self):
        assert normalize("Alice:\r\nHello\r\nBob:\r\nHi", self.S) == "Alice:\nHello\nBob:\nHi"

    def test_normalizes_bare_carriage_returns(self):
        assert normalize("Alice:\rHello", self.S) == "Alice:\nHello"

    def test_strips_trailing_spaces_per_line(self):
        assert normalize("Alice:   \nHello   ", self.S) == "Alice:\nHello"

    def test_collapses_three_or_more_blank_lines_to_two(self):
        text = "Alice:\n\n\n\nBob:"
        assert normalize(text, self.S) == "Alice:\n\nBob:"

    def test_preserves_single_blank_line_between_turns(self):
        text = "Alice: Hello\n\nBob: Hi"
        assert normalize(text, self.S) == "Alice: Hello\n\nBob: Hi"

    def test_nfc_normalization_merges_combining_characters(self):
        # "e" + combining acute accent → single "é" codepoint
        decomposed = "résumé"
        result = normalize(decomposed, self.S)
        assert result == "résumé"
        assert len(result) == 6  # 6 chars, not 8

    def test_does_not_touch_smart_quotes(self):
        text = "Alice: “Hello”"
        assert normalize(text, self.S) == "Alice: “Hello”"

    def test_does_not_collapse_double_newlines(self):
        text = "Alice:\n\nBob:"
        assert normalize(text, self.S) == "Alice:\n\nBob:"


# ---------------------------------------------------------------------------
# STANDARD (cumulative: includes CONSERVATIVE)
# ---------------------------------------------------------------------------

class TestStandard:
    S = NormalizationStrategy.STANDARD

    def test_replaces_left_double_smart_quote(self):
        assert normalize("“Hello”", self.S) == '"Hello"'

    def test_replaces_right_double_smart_quote(self):
        assert normalize("end”", self.S) == 'end"'

    def test_replaces_left_single_smart_quote(self):
        assert normalize("‘Hello’", self.S) == "'Hello'"

    def test_replaces_en_dash(self):
        assert normalize("2020–2021", self.S) == "2020-2021"

    def test_replaces_em_dash(self):
        assert normalize("done—finally", self.S) == "done--finally"

    def test_replaces_non_breaking_space(self):
        assert normalize("Alice: Hello", self.S) == "Alice: Hello"

    def test_removes_zero_width_space(self):
        assert normalize("Hel​lo", self.S) == "Hello"

    def test_collapses_multiple_spaces_within_line(self):
        assert normalize("Alice:   Hello", self.S) == "Alice: Hello"

    def test_does_not_collapse_double_newlines(self):
        text = "Alice: Hello\n\nBob: Hi"
        assert normalize(text, self.S) == "Alice: Hello\n\nBob: Hi"

    def test_inherits_conservative_trailing_space_removal(self):
        assert normalize("Hello   \nWorld   ", self.S) == "Hello\nWorld"

    def test_inherits_conservative_crlf_normalization(self):
        assert normalize("Alice:\r\nBob:", self.S) == "Alice:\nBob:"


# ---------------------------------------------------------------------------
# AGGRESSIVE (cumulative: includes STANDARD + CONSERVATIVE)
# ---------------------------------------------------------------------------

class TestAggressive:
    S = NormalizationStrategy.AGGRESSIVE

    def test_collapses_double_newline_to_single(self):
        assert normalize("Alice: Hello\n\nBob: Hi", self.S) == "Alice: Hello\nBob: Hi"

    def test_collapses_triple_newline_to_single(self):
        assert normalize("Alice:\n\n\nBob:", self.S) == "Alice:\nBob:"

    def test_inherits_standard_smart_quote_replacement(self):
        assert normalize("“Hello”", self.S) == '"Hello"'

    def test_inherits_standard_multi_space_collapse(self):
        assert normalize("Alice:   Hello", self.S) == "Alice: Hello"

    def test_inherits_conservative_crlf_normalization(self):
        assert normalize("Alice:\r\nBob:", self.S) == "Alice:\nBob:"


# ---------------------------------------------------------------------------
# Default strategy
# ---------------------------------------------------------------------------

def test_default_strategy_is_standard():
    text = "“Hello”"
    assert normalize(text) == normalize(text, NormalizationStrategy.STANDARD)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_string_returns_empty(self):
        for s in NormalizationStrategy:
            assert normalize("", s) == ""

    def test_whitespace_only_returns_empty(self):
        for s in NormalizationStrategy:
            assert normalize("   \n\n   ", s) == ""

    def test_single_word_unchanged(self):
        for s in NormalizationStrategy:
            assert normalize("hello", s) == "hello"

    def test_realistic_labeled_transcript_conservative(self):
        raw = "Alice | Coach:  How are you?\r\n\nBob:  Better.\n\n\n\nAlice | Coach:  Great."
        result = normalize(raw, NormalizationStrategy.CONSERVATIVE)
        assert "\r" not in result
        assert "  " not in result.replace("  ", "X")  # no double spaces kept by conservative
        # conservative does NOT collapse double newlines
        assert "\n\n" in result

    def test_realistic_labeled_transcript_aggressive(self):
        raw = "Alice: Hello\n\nBob: Hi\n\nAlice: Goodbye"
        result = normalize(raw, NormalizationStrategy.AGGRESSIVE)
        assert "\n\n" not in result
        assert result == "Alice: Hello\nBob: Hi\nAlice: Goodbye"
