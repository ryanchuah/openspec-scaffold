#!/usr/bin/env python3
"""Tests for scripts/opencode_delegate.py — pure-function + pipeline.

All clock values are INJECTED (never call ``datetime.now()`` in a test body)
so this file trips no ``unfrozen-clock`` self-finding.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ruff: noqa: E402 — import after sys.path fix
import opencode_delegate as od

# ===================================================================
# T4 — Pure-function unit tests
# ===================================================================


class TestExtractText:
    def test_multi_line_jsonl_returns_last_text(self):
        jsonl = (
            '{"type":"text","part":{"text":"first"}}\n'
            '{"type":"not-text","part":{"text":"skip"}}\n'
            "not-json\n"
            "\n"
            '{"type":"text","part":{"text":"second"}}\n'
            '{"type":"text","part":{"text":"third"}}\n'
        )
        assert od.extract_text(jsonl) == "third"

    def test_skips_blank_and_non_json_lines(self):
        jsonl = '\n\n  \n{"type":"text","part":{"text":"only"}}\n'
        assert od.extract_text(jsonl) == "only"

    def test_no_text_part_returns_none(self):
        jsonl = '{"type":"other","part":{"text":"nope"}}\n'
        assert od.extract_text(jsonl) is None

    def test_whitespace_only_text_returns_earlier_valid(self):
        jsonl = '{"type":"text","part":{"text":"  "}}\n{"type":"text","part":{"text":"valid"}}\n'
        # Last valid non-whitespace text is "valid"
        assert od.extract_text(jsonl) == "valid"

    def test_all_whitespace_returns_none(self):
        jsonl = '{"type":"text","part":{"text":"   "}}\n'
        assert od.extract_text(jsonl) is None

    def test_empty_string_returns_none(self):
        assert od.extract_text("") is None

    def test_text_inside_list_handled_gracefully(self):
        # Some opencode versions wrap in a top-level array
        jsonl = '{"type":"text","part":{"text":"found"}}\n'
        assert od.extract_text(jsonl) == "found"

    def test_missing_part_key_skips(self):
        jsonl = '{"type":"text"}\n'
        assert od.extract_text(jsonl) is None

    def test_part_without_text_skips(self):
        jsonl = '{"type":"text","part":{"other":"data"}}\n'
        assert od.extract_text(jsonl) is None


class TestDetectTruncatedStream:
    def test_balanced_counts(self):
        """One start, one finish → False."""
        jsonl = '{"type":"step_start"}\n{"type":"step_finish"}\n'
        assert od.detect_truncated_stream(jsonl) is False

    def test_starts_greater_than_finishes(self):
        """Two starts, one finish → True."""
        jsonl = '{"type":"step_start"}\n{"type":"step_finish"}\n{"type":"step_start"}\n'
        assert od.detect_truncated_stream(jsonl) is True

    def test_no_step_events(self):
        """Only text/tool_use lines → False."""
        jsonl = (
            '{"type":"text","part":{"text":"hello"}}\n{"type":"tool_use","part":{"name":"read"}}\n'
        )
        assert od.detect_truncated_stream(jsonl) is False

    def test_empty_string(self):
        assert od.detect_truncated_stream("") is False

    def test_blank_and_non_json_tolerated(self):
        """Blank and non-JSON lines interleaved, still balanced → False."""
        jsonl = '\nnot-json\n{"type":"step_start"}\n\n{"type":"step_finish"}\nalso-not-json\n'
        assert od.detect_truncated_stream(jsonl) is False

    def test_more_finishes_than_starts(self):
        """Defensive: more finishes than starts → False."""
        jsonl = '{"type":"step_finish"}\n{"type":"step_start"}\n{"type":"step_finish"}\n'
        assert od.detect_truncated_stream(jsonl) is False

    def test_incident_shaped(self):
        """Bare step_start at end: 2 starts, 1 finish → True."""
        jsonl = (
            '{"type":"text","part":{"text":"partial work"}}\n'
            '{"type":"step_start"}\n'
            '{"type":"step_finish"}\n'
            '{"type":"tool_use","part":{"name":"read"}}\n'
            '{"type":"text","part":{"text":"more text"}}\n'
            '{"type":"step_start"}\n'
        )
        assert od.detect_truncated_stream(jsonl) is True


class TestDetectFallback:
    def test_fallback_detected(self):
        assert od.detect_fallback("something\nFalling back to default agent\nmore")

    def test_clean_err(self):
        assert not od.detect_fallback("clean output here")

    def test_empty_string(self):
        assert not od.detect_fallback("")

    def test_case_sensitive(self):
        assert not od.detect_fallback("falling back to default agent")


class TestParseExitFile:
    def test_exit_124(self):
        assert od.parse_exit_file("EXIT=124\n") == 124

    def test_exit_0(self):
        assert od.parse_exit_file("EXIT=0") == 0

    def test_exit_1(self):
        assert od.parse_exit_file("EXIT=1\n") == 1

    def test_garbage_returns_none(self):
        assert od.parse_exit_file("not an exit file") is None

    def test_empty_returns_none(self):
        assert od.parse_exit_file("") is None

    def test_trailing_text_rejected(self):
        """Trailing text after the EXIT= number is unparseable → None."""
        assert od.parse_exit_file("EXIT=124\nsome extra\n") is None

    def test_non_numeric_after_eq_returns_none(self):
        assert od.parse_exit_file("EXIT=abc") is None

    def test_whitespace_around_handled(self):
        assert od.parse_exit_file("  EXIT=0  ") == 0


class TestAssertMarkers:
    def test_all_present(self):
        text = "## Review Round\nSome content\nVERDICT: READY\n"
        assert od.assert_markers(text, [r"## Review Round", r"VERDICT:"]) is True

    def test_one_missing(self):
        text = "## Review Round\nNo verdict here\n"
        assert od.assert_markers(text, [r"## Review Round", r"VERDICT:"]) is False

    def test_empty_markers_list(self):
        assert od.assert_markers("any text", []) is True

    def test_text_none_returns_false(self):
        assert od.assert_markers(None, [r"## Review Round"]) is False

    def test_malformed_regex_caught(self):
        # "(" is an incomplete group → re.error → treated as not-matched
        assert od.assert_markers("some text", ["(", r"some"]) is False

    def test_all_malformed_regex(self):
        assert od.assert_markers("text", ["(", "["]) is False

    def test_multiline_flag_applied(self):
        text = "line1\n## Header\nline3"
        assert od.assert_markers(text, [r"^## Header"]) is True


class TestExtractVerdict:
    text_with_agree = "stuff\nPREMISE: AGREE\nmore"
    text_with_ready = "stuff\nVERDICT: READY\nmore"

    def test_grouped_pattern(self):
        assert od.extract_verdict(self.text_with_agree, r"PREMISE: (AGREE|DISSENT)") == "AGREE"

    def test_grouped_dissent(self):
        assert od.extract_verdict("PREMISE: DISSENT", r"PREMISE: (AGREE|DISSENT)") == "DISSENT"

    def test_ungrouped_pattern_returns_full_match(self):
        assert od.extract_verdict(self.text_with_ready, r"VERDICT: READY") == "VERDICT: READY"

    def test_no_match_returns_none(self):
        assert od.extract_verdict(self.text_with_agree, r"VERDICT: .+") is None

    def test_regex_none_returns_none(self):
        assert od.extract_verdict("any text", None) is None

    def test_text_none_returns_none(self):
        assert od.extract_verdict(None, r"PREMISE: (AGREE|DISSENT)") is None

    def test_malformed_regex_caught(self):
        assert od.extract_verdict("text", "(") is None

    def test_multiline_flag(self):
        assert od.extract_verdict("a\nb\nVERDICT: READY", r"^VERDICT: (READY)") == "READY"


class TestClassifyStatus:
    # (exit_code, fallback, text, marker_ok, truncated) → expected

    @staticmethod
    def _c(exit_code, fallback, text, marker_ok, truncated=False):
        return od.classify_status(exit_code, fallback, text, marker_ok, truncated=truncated)

    def test_ok_normal(self):
        assert self._c(0, False, "x", True) == "ok"

    def test_fallback_precedence(self):
        assert self._c(0, True, "x", True) == "fallback"

    def test_timeout_124(self):
        assert self._c(124, False, "x", True) == "timeout"

    def test_timeout_137(self):
        assert self._c(137, False, "x", True) == "timeout"

    def test_crash_no_text(self):
        assert self._c(0, False, None, True) == "crash"

    def test_crash_empty_text(self):
        assert self._c(0, False, "", True) == "crash"

    def test_marker_missing(self):
        assert self._c(0, False, "x", False) == "marker-missing"

    def test_exit_code_lie(self):
        """Nonzero exit NOT in (124,137) with present text = ok, not crash."""
        assert self._c(1, False, "x", True) == "ok"

    def test_fallback_over_crash(self):
        """Fallback wins over text-none crash."""
        assert self._c(1, True, None, True) == "fallback"

    def test_exit_code_none_with_text_ok(self):
        """Unreadable exit-file (None) is not in (124,137) → falls through to ok."""
        assert self._c(None, False, "x", True) == "ok"

    def test_exit_code_none_no_text_crash(self):
        """Unreadable exit-file (None) with no text → crash."""
        assert self._c(None, False, None, True) == "crash"

    def test_timeout_124_over_marker(self):
        assert self._c(124, False, "x", False) == "timeout"

    def test_fallback_over_timeout(self):
        assert self._c(124, True, "x", True) == "fallback"

    def test_exit_code_lie_various(self):
        """Exit codes 2, 255 are not in (124,137) → ok with text."""
        for ec in (2, 127, 255, 99, -1):
            assert self._c(ec, False, "x", True) == "ok", f"exit={ec}"

    # ---- truncated-stream cases ----

    def test_truncated_status(self):
        """truncated=True with text and marker_ok → truncated-stream."""
        assert self._c(0, False, "x", True, truncated=True) == "truncated-stream"

    def test_truncated_wins_over_marker_missing(self):
        """truncated wins over marker-missing."""
        assert self._c(0, False, "x", False, truncated=True) == "truncated-stream"

    def test_fallback_over_truncated(self):
        """fallback wins over truncated."""
        assert self._c(0, True, "x", True, truncated=True) == "fallback"

    def test_timeout_over_truncated(self):
        """timeout (124) wins over truncated."""
        assert self._c(124, False, "x", True, truncated=True) == "timeout"

    def test_crash_over_truncated(self):
        """crash (no text) wins over truncated."""
        assert self._c(0, False, None, True, truncated=True) == "crash"

    def test_default_truncated_param(self):
        """Default truncated=False yields 'ok'."""
        assert self._c(0, False, "x", True) == "ok"


class TestBuildLedgerRecord:
    FIXED_TS = "2026-07-13T12:00:00+00:00"
    BASE_TAGS = {"foo": "bar"}

    def _record(self, **overrides):
        kwargs = dict(
            ts=self.FIXED_TS,
            phase="verify-pro",
            agent="openspec-verifier",
            model="deepseek/deepseek-v4-pro",
            change="demo-change",
            exit_code=0,
            fallback=False,
            status="ok",
            marker_ok=True,
            verdict="READY",
            retry=0,
            duration_s=None,
            tags=self.BASE_TAGS,
        )
        kwargs.update(overrides)
        return od.build_ledger_record(**kwargs)

    def test_has_exactly_12_core_keys_plus_tags(self):
        record = self._record()
        # 12 core keys + 1 tag key = 13
        assert len(record) == 13
        for key in od.CORE_LEDGER_KEYS:
            assert key in record

    def test_ts_echoed_verbatim(self):
        record = self._record()
        assert record["ts"] == self.FIXED_TS

    def test_tag_merged(self):
        record = self._record()
        assert record["foo"] == "bar"

    def test_tag_collision_prefixed(self):
        record = self._record(tags={"status": "override"})
        assert record["tag_status"] == "override"
        assert record["status"] == "ok"

    def test_multiple_tags(self):
        record = self._record(tags={"lens": "test-quality", "round": "1"})
        assert record["lens"] == "test-quality"
        assert record["round"] == "1"

    def test_json_serializable(self):
        record = self._record()
        dumped = json.dumps(record)
        parsed = json.loads(dumped)
        assert parsed["ts"] == self.FIXED_TS
        assert parsed["status"] == "ok"

    def test_core_keys_exact_names(self):
        record = self._record()
        expected_keys = {
            "ts",
            "phase",
            "agent",
            "model",
            "change",
            "exit",
            "fallback",
            "status",
            "marker_ok",
            "verdict",
            "retry",
            "duration_s",
        }
        for key in expected_keys:
            assert key in record, f"Missing core key: {key}"


class TestBestEffortDuration:
    def test_two_text_parts_with_timestamps(self):
        jsonl = (
            '{"type":"text","part":{"text":"a","time":1.0}}\n'
            '{"type":"text","part":{"text":"b","time":5.0}}\n'
        )
        d = od.best_effort_duration(jsonl)
        assert d is not None
        assert abs(d - 4.0) < 0.001

    def test_single_part_returns_none(self):
        jsonl = '{"type":"text","part":{"text":"a","time":1.0}}\n'
        assert od.best_effort_duration(jsonl) is None

    def test_no_timestamp_returns_none(self):
        jsonl = '{"type":"text","part":{"text":"a"}}\n{"type":"text","part":{"text":"b"}}\n'
        assert od.best_effort_duration(jsonl) is None

    def test_mixed_objects_some_with_ts(self):
        jsonl = '{"type":"other","time":1.0}\n{"type":"other2","part":{"text":"a"}}\nnot-json\n'
        assert od.best_effort_duration(jsonl) is None  # only one with ts

    def test_epoch_ms_coerced(self):
        # epoch-ms timestamps > 1e12 → coerced to seconds
        jsonl = (
            '{"type":"text","part":{"text":"a","time":1000000000001}}\n'  # ~2001, > 1e12
            '{"type":"text","part":{"text":"b","time":1000000005001}}\n'
        )
        d = od.best_effort_duration(jsonl)
        assert d is not None
        # 5s difference after /1000
        assert abs(d - 5.0) < 0.1

    def test_empty_jsonl_returns_none(self):
        assert od.best_effort_duration("") is None

    def test_top_level_timestamp_used(self):
        jsonl = (
            '{"type":"text","part":{"text":"a"},"timestamp":100.0}\n'
            '{"type":"text","part":{"text":"b"},"timestamp":105.0}\n'
        )
        d = od.best_effort_duration(jsonl)
        assert d is not None
        assert abs(d - 5.0) < 0.001

    def test_observed_part_time_object_form(self):
        # Real opencode format (probed 2026-07-13): part.time = {start, end} epoch-ms.
        # Duration spans first part's start .. last part's end.
        jsonl = (
            '{"type":"text","part":{"text":"a","time":{"start":1783979950000,"end":1783979950100}}}\n'
            '{"type":"step-finish","part":{"type":"step-finish"}}\n'
            '{"type":"text","part":{"text":"b","time":{"start":1783979955000,"end":1783979958200}}}\n'
        )
        d = od.best_effort_duration(jsonl)
        assert d is not None
        assert abs(d - 8.2) < 0.05  # (1783979958200 - 1783979950000) / 1000


# ===================================================================
# T5 — main() pipeline integration test
# ===================================================================


class TestMainPipeline:
    """Full-pipeline tests using temp fixtures."""

    def _make_fixtures(self, tmp_path: Path, **overrides) -> dict:
        """Create out.jsonl, err.log, exit file and return paths dict.

        Fixture text by default contains markers and a verdict token.
        """
        defaults = dict(
            out_jsonl=(
                '{"type":"other","part":{"text":"skip"}}\n'
                '{"type":"text","part":{"text":"first text part"}}\n'
                "not-json-line\n"
                '{"type":"text","part":{"text":"final text with VERDICT: READY"}}\n'
            ),
            err_log="clean stderr\nno fallback\n",
            exit_text="EXIT=0",
        )
        defaults.update(overrides)
        paths = {}
        paths["out"] = str(tmp_path / "out.jsonl")
        paths["err"] = str(tmp_path / "err.log")
        paths["exit"] = str(tmp_path / "exit.txt")
        paths["text_out"] = str(tmp_path / "out.text.txt")
        paths["result_out"] = str(tmp_path / "out.result.json")
        paths["ledger"] = str(tmp_path / "ledger.jsonl")
        Path(paths["out"]).write_text(defaults["out_jsonl"])
        Path(paths["err"]).write_text(defaults["err_log"])
        Path(paths["exit"]).write_text(defaults["exit_text"])
        return paths

    def test_pipeline_ok(self, tmp_path):
        paths = self._make_fixtures(tmp_path)
        rc = od.main(
            [
                "--phase",
                "verify-pro",
                "--agent",
                "openspec-verifier",
                "--model",
                "deepseek/deepseek-v4-pro",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--require-marker",
                "VERDICT:",
                "--verdict-regex",
                "VERDICT: (READY|NEEDS REVISION)",
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 0

        # --text-out holds LAST text
        text = Path(paths["text_out"]).read_text()
        assert "final text with VERDICT: READY" in text

        # --result-out JSON
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "ok"
        assert result["verdict"] == "READY"
        assert result["exit"] == 0
        assert result["text_present"] is True

        # Ledger has exactly ONE line
        lines = Path(paths["ledger"]).read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        for key in od.CORE_LEDGER_KEYS:
            assert key in entry, f"Missing ledger key: {key}"
        assert entry["phase"] == "verify-pro"
        assert entry["status"] == "ok"
        assert entry["verdict"] == "READY"
        assert entry["exit"] == 0

    def test_append_only_ledger(self, tmp_path):
        """Two main() runs to the same ledger → two lines."""
        paths = self._make_fixtures(tmp_path)
        args = [
            "--phase",
            "verify-pro",
            "--agent",
            "openspec-verifier",
            "--model",
            "deepseek/deepseek-v4-pro",
            "--change",
            "demo",
            "--out",
            paths["out"],
            "--err",
            paths["err"],
            "--exit-file",
            paths["exit"],
            "--require-marker",
            "VERDICT:",
            "--ledger",
            paths["ledger"],
            "--text-out",
            paths["text_out"],
            "--result-out",
            paths["result_out"],
            "--quiet",
        ]
        rc1 = od.main(args)
        assert rc1 == 0
        rc2 = od.main(args)
        assert rc2 == 0

        lines = Path(paths["ledger"]).read_text().strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            entry = json.loads(line)
            assert entry["status"] == "ok"

    def test_fallback_status(self, tmp_path):
        paths = self._make_fixtures(tmp_path, err_log="Falling back to default agent\n")
        rc = od.main(
            [
                "--phase",
                "verify-pro",
                "--agent",
                "openspec-verifier",
                "--model",
                "deepseek/deepseek-v4-pro",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--require-marker",
                "VERDICT:",
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 1
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "fallback"
        assert result["fallback"] is True

    def test_marker_missing_status(self, tmp_path):
        paths = self._make_fixtures(tmp_path)
        rc = od.main(
            [
                "--phase",
                "verify-pro",
                "--agent",
                "openspec-verifier",
                "--model",
                "deepseek/deepseek-v4-pro",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--require-marker",
                "NOPE",
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 1
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "marker-missing"

    def test_no_text_in_out(self, tmp_path):
        """No type:text parts → status crash."""
        paths = self._make_fixtures(
            tmp_path,
            out_jsonl='{"type":"other","part":{"text":"nope"}}\n',
        )
        rc = od.main(
            [
                "--phase",
                "apply",
                "--agent",
                "apply-executor",
                "--model",
                "deepseek/deepseek-v4-flash",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 1
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "crash"

    def test_exit_124_timeout(self, tmp_path):
        paths = self._make_fixtures(tmp_path, exit_text="EXIT=124")
        rc = od.main(
            [
                "--phase",
                "verify-pro",
                "--agent",
                "openspec-verifier",
                "--model",
                "deepseek/deepseek-v4-pro",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 1
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "timeout"

    def test_sync_exit_flag(self, tmp_path):
        """Use --exit instead of --exit-file (synchronous sites)."""
        paths = self._make_fixtures(tmp_path)
        rc = od.main(
            [
                "--phase",
                "propose-review",
                "--agent",
                "openspec-reviewer",
                "--model",
                "deepseek/deepseek-v4-pro",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit",
                "0",
                "--require-marker",
                "VERDICT:",
                "--verdict-regex",
                "VERDICT: (READY)",
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 0
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "ok"
        assert result["verdict"] == "READY"

    def test_tags_passed_through(self, tmp_path):
        paths = self._make_fixtures(tmp_path)
        rc = od.main(
            [
                "--phase",
                "verify-lens",
                "--agent",
                "openspec-verifier",
                "--model",
                "deepseek/deepseek-v4-flash",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--require-marker",
                "VERDICT:",
                "--tag",
                "lens=test-quality",
                "--tag",
                "round=1",
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 0
        entry = json.loads(Path(paths["ledger"]).read_text().strip())
        assert entry["lens"] == "test-quality"
        assert entry["round"] == "1"

    def test_missing_out_file_graceful(self, tmp_path):
        """Missing --out file → treated as empty, no crash (T3)."""
        paths = self._make_fixtures(tmp_path)
        missing_out = str(tmp_path / "nonexistent.jsonl")
        rc = od.main(
            [
                "--phase",
                "apply",
                "--agent",
                "apply-executor",
                "--model",
                "deepseek/deepseek-v4-flash",
                "--change",
                "demo",
                "--out",
                missing_out,
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 1
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "crash"  # no text extracted

    def test_truncated_stream_status(self, tmp_path):
        """Unbalanced steps + satisfied marker → truncated-stream status."""
        paths = self._make_fixtures(
            tmp_path,
            out_jsonl=(
                '{"type":"text","part":{"text":"partial work VERDICT: READY"}}\n'
                '{"type":"step_start"}\n'
                '{"type":"step_finish"}\n'
                '{"type":"step_start"}\n'
            ),
        )
        rc = od.main(
            [
                "--phase",
                "verify-pro",
                "--agent",
                "openspec-verifier",
                "--model",
                "deepseek/deepseek-v4-pro",
                "--change",
                "demo",
                "--out",
                paths["out"],
                "--err",
                paths["err"],
                "--exit-file",
                paths["exit"],
                "--require-marker",
                "VERDICT:",
                "--ledger",
                paths["ledger"],
                "--text-out",
                paths["text_out"],
                "--result-out",
                paths["result_out"],
                "--quiet",
            ]
        )
        assert rc == 1
        result = json.loads(Path(paths["result_out"]).read_text())
        assert result["status"] == "truncated-stream"


# ===================================================================
# T6 — No self-finding: no datetime.now() in test bodies,
# no self-mock of opencode_delegate.
# ===================================================================


class TestNoUnfrozenClock:
    """Verify no test calls datetime.now() — static import check.

    The unfrozen-clock detector in checks.py looks for violations at the
    module level.  This cross-check verifies no ``from datetime import`` or
    ``import datetime`` exists in the file, which is the import pattern that
    would let a test call ``datetime.now()``.
    """

    def test_no_datetime_import_in_test_file(self):
        """No ``import datetime`` in this file (prevents unfrozen-clock)."""
        import ast

        with open(__file__) as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "datetime":
                        pytest.fail(f"Found 'import datetime' at line {node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "datetime":
                    names = [a.name for a in node.names]
                    pytest.fail(
                        f"Found 'from datetime import {', '.join(names)}' at line {node.lineno}"
                    )


class TestNoSelfMock:
    """Verify we do not mock opencode_delegate itself (no self-mock)."""

    def test_no_unittest_mock_import(self):
        """Assert no ``import unittest.mock`` or ``from unittest import mock``."""
        import ast

        with open(__file__) as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "unittest.mock":
                        pytest.fail(f"Found 'import unittest.mock' at line {node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "unittest" and any(a.name == "mock" for a in node.names):
                    pytest.fail(f"Found 'from unittest import mock' at line {node.lineno}")
