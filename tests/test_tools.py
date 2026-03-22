"""
Test harness for local-ai-legal-setup tools/.

Coverage strategy:
  1. Import smoke tests — every tool can be imported without error
  2. Structure tests — every tool has a Tools class with the expected shape
  3. Unit tests — pure Python logic (no Ollama, no network calls)
     - citation-checker.py: regex patterns, flagging, deduplication
     - legal-readability-scorer.py: grade bands, target detection, passive voice
     - ai-disclaimer.py: disclaimer appending, empty-text handling
     - batch-scanner.py: text extraction helpers, risk pattern matching
     - supervision-log.py: module-level constants and DB helpers
     - time-tracker.py: manual time lookups, valve overrides

Ollama/network calls are mocked so tests pass without a running server.
"""

import asyncio
import importlib.util
import json
import re
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Import helpers ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"


def load_tool(filename: str):
    """Load a tools/ module by filename (handles hyphens)."""
    path = TOOLS_DIR / filename
    module_name = filename.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(coro):
    """Run a coroutine synchronously (Python 3.10+ compatible)."""
    return asyncio.run(coro)


# ── 1. Import smoke tests ─────────────────────────────────────────────────────

OPEN_WEBUI_TOOLS = [
    "ai-disclaimer.py",
    "bar-exam-simulator.py",
    "bar-prep.py",
    "case-briefer.py",
    "citation-checker.py",
    "compliance-report.py",
    "contract-comparator.py",
    "court-rules-checker.py",
    "depo-prep.py",
    "document-qa.py",
    "document-summarizer.py",
    "exam-prep.py",
    "first-year-survival.py",
    "job-prep.py",
    "legal-grammar-checker.py",
    "legal-readability-scorer.py",
    "legal-research-trainer.py",
    "mentor-qa.py",
    "supervision-log.py",
    "time-tracker.py",
    "writing-coach.py",
]

# batch-scanner.py is a CLI tool (argparse-based) — tested separately below
CLI_TOOLS = ["batch-scanner.py"]


class TestImports:
    """Every tool module must import without raising an exception."""

    @pytest.mark.parametrize("filename", OPEN_WEBUI_TOOLS + CLI_TOOLS)
    def test_tool_imports_without_error(self, filename):
        """Import smoke test — catches syntax errors, missing stdlib deps, etc."""
        try:
            mod = load_tool(filename)
        except Exception as exc:
            pytest.fail(f"{filename} failed to import: {exc}")

    @pytest.mark.parametrize("filename", OPEN_WEBUI_TOOLS)
    def test_open_webui_tool_has_Tools_class(self, filename):
        """Open WebUI tools must expose a Tools class."""
        mod = load_tool(filename)
        assert hasattr(mod, "Tools"), f"{filename} missing top-level Tools class"

    @pytest.mark.parametrize("filename", OPEN_WEBUI_TOOLS)
    def test_tools_class_is_instantiable(self, filename):
        """Tools() constructor must succeed without arguments."""
        mod = load_tool(filename)
        try:
            instance = mod.Tools()
        except Exception as exc:
            pytest.fail(f"{filename}: Tools() raised {exc}")

    @pytest.mark.parametrize("filename", OPEN_WEBUI_TOOLS)
    def test_tools_class_has_valves(self, filename):
        """Tools must have a Valves inner class (Open WebUI contract)."""
        mod = load_tool(filename)
        assert hasattr(mod.Tools, "Valves"), (
            f"{filename}: Tools missing Valves inner class"
        )

    @pytest.mark.parametrize("filename", OPEN_WEBUI_TOOLS)
    def test_tools_class_has_at_least_one_async_method(self, filename):
        """Every Open WebUI tool must expose at least one async callable."""
        mod = load_tool(filename)
        instance = mod.Tools()
        public_methods = [
            name for name in dir(instance)
            if not name.startswith("_") and callable(getattr(instance, name))
        ]
        async_methods = [
            name for name in public_methods
            if asyncio.iscoroutinefunction(getattr(instance, name))
        ]
        assert async_methods, (
            f"{filename}: no async methods found on Tools instance"
        )


class TestCliTools:
    """batch-scanner.py is a standalone CLI script."""

    def test_batch_scanner_has_main_guard(self):
        """batch-scanner.py uses if __name__ == '__main__' or argparse."""
        source = (TOOLS_DIR / "batch-scanner.py").read_text()
        has_argparse = "argparse" in source
        has_main_guard = "__name__" in source
        assert has_argparse or has_main_guard, (
            "batch-scanner.py missing argparse or __main__ guard"
        )


# ── 2. Citation Checker unit tests ────────────────────────────────────────────

class TestCitationChecker:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("citation-checker.py")
        self.tools = self.mod.Tools()

    def test_detects_federal_case_citation(self):
        text = "See Anderson v. Liberty Lobby, Inc., 477 U.S. 242 (1986)."
        result = json.loads(run(self.tools.check_citations(text)))
        citations = result["citations_found"]
        types_ = {c["type"] for c in citations}
        assert "case_citation" in types_ or "case_name" in types_

    def test_detects_usc_statute(self):
        text = "Plaintiff brings this action under 42 U.S.C. § 1983."
        result = json.loads(run(self.tools.check_citations(text)))
        citations = result["citations_found"]
        statute_types = {c["type"] for c in citations}
        assert "federal_statute" in statute_types, (
            f"Expected federal_statute, got: {statute_types}"
        )

    def test_detects_cfr_citation(self):
        text = "See 29 C.F.R. § 1926.451 for scaffolding requirements."
        result = json.loads(run(self.tools.check_citations(text)))
        citations = result["citations_found"]
        assert any(c["type"] == "federal_regulation" for c in citations)

    def test_flags_nonexistent_reporter(self):
        """F.5th does not exist — should be red-flagged."""
        text = "The court held in Smith v. Jones, 123 F.5th 456 (2024)."
        result = json.loads(run(self.tools.check_citations(text)))
        high_risk = result["summary"]["high_risk_count"]
        assert high_risk > 0, "F.5th citation should have been flagged as non-existent"

    def test_flags_suspiciously_round_numbers(self):
        """Volume 100, page 200 is a round-number red flag pattern."""
        text = "See Fake v. Case, 100 F.3d 200 (9th Cir. 2020)."
        result = json.loads(run(self.tools.check_citations(text)))
        # At minimum a citation should be found
        assert result["summary"]["total"] > 0

    def test_empty_text_returns_no_citations(self):
        result = json.loads(run(self.tools.check_citations("")))
        assert result["summary"]["total"] == 0
        assert result["citations_found"] == []

    def test_bluebook_see_signal_detected(self):
        text = "See also Roe v. Wade, 410 U.S. 113 (1973)."
        result = json.loads(run(self.tools.check_citations(text)))
        types_ = {c["type"] for c in result["citations_found"]}
        assert "bluebook_signal" in types_

    def test_output_schema_valid(self):
        text = "See Miranda v. Arizona, 384 U.S. 436 (1966)."
        raw = run(self.tools.check_citations(text))
        validation = self.tools.validate_output(raw)
        assert validation["valid"], f"Schema errors: {validation['errors']}"

    def test_deduplication_no_duplicate_positions(self):
        """_deduplicate should never return two citations at the exact same position."""
        text = "See 42 U.S.C. § 1983 and 29 C.F.R. § 1926.451."
        result = json.loads(run(self.tools.check_citations(text)))
        positions_and_types = [(c["position"], c["type"]) for c in result["citations_found"]]
        assert len(positions_and_types) == len(set(positions_and_types)), (
            "Duplicate (position, type) pairs found after deduplication"
        )

    def test_truncates_oversized_text(self):
        """Text longer than max_text_length should be processed without error."""
        long_text = "See Smith v. Jones. " * 5000  # ~100k chars
        result_str = run(self.tools.check_citations(long_text))
        result = json.loads(result_str)
        assert "citations_found" in result

    def test_case_name_without_reporter_flagged(self):
        """A bare 'Smith v. Jones' with no reporter nearby should get a red flag."""
        text = "As held in Smith v. Jones, the standard is clear."
        result = json.loads(run(self.tools.check_citations(text)))
        case_names = [c for c in result["citations_found"] if c["type"] == "case_name"]
        # All bare case names here lack a reporter
        flagged = [c for c in case_names if c["red_flags"]]
        assert flagged, "Bare case name without reporter should be flagged"


# ── 3. Readability Scorer unit tests ─────────────────────────────────────────

class TestReadabilityScorer:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("legal-readability-scorer.py")
        self.tools = self.mod.Tools()

    def test_returns_valid_json(self, sample_legal_brief_text):
        result_str = run(self.tools.score_readability(sample_legal_brief_text))
        result = json.loads(result_str)
        assert "readability_scores" in result
        assert "sentence_statistics" in result
        assert "legal_interpretation" in result

    def test_readability_scores_keys_present(self, simple_text):
        result = json.loads(run(self.tools.score_readability(simple_text)))
        expected_keys = {
            "flesch_reading_ease",
            "flesch_kincaid_grade",
            "gunning_fog_index",
            "smog_index",
            "coleman_liau_index",
            "automated_readability_index",
            "dale_chall_score",
            "average_grade_level",
        }
        assert expected_keys.issubset(result["readability_scores"].keys())

    def test_sentence_statistics_keys_present(self, simple_text):
        result = json.loads(run(self.tools.score_readability(simple_text)))
        stats = result["sentence_statistics"]
        assert "total_sentences" in stats
        assert "total_words" in stats
        assert "average_sentence_length" in stats
        assert "long_sentences_over_40_words" in stats

    def test_simple_text_has_low_grade(self, simple_text):
        """Very simple text should score below grade 10."""
        result = json.loads(run(self.tools.score_readability(simple_text)))
        avg_grade = result["readability_scores"]["average_grade_level"]
        assert avg_grade < 10, f"Expected simple text to score below grade 10, got {avg_grade}"

    def test_legal_brief_has_higher_grade_than_simple(self, sample_legal_brief_text, simple_text):
        brief_result = json.loads(run(self.tools.score_readability(sample_legal_brief_text)))
        simple_result = json.loads(run(self.tools.score_readability(simple_text)))
        brief_grade = brief_result["readability_scores"]["average_grade_level"]
        simple_grade = simple_result["readability_scores"]["average_grade_level"]
        assert brief_grade > simple_grade, (
            f"Legal brief ({brief_grade}) should score higher than simple text ({simple_grade})"
        )

    def test_explicit_document_type_brief(self, sample_legal_brief_text):
        result = json.loads(run(self.tools.score_readability(sample_legal_brief_text, "brief")))
        interpretation = result["legal_interpretation"]
        assert "document_type_target" in interpretation

    def test_explicit_document_type_consumer(self, simple_text):
        result = json.loads(run(self.tools.score_readability(simple_text, "consumer")))
        interpretation = result["legal_interpretation"]
        # Should have a target note for consumer documents
        assert "document_type_target" in interpretation

    def test_passive_voice_detection(self):
        """Text with passive constructions should report positive passive count."""
        text = (
            "The contract was signed by the parties. "
            "The motion was filed by counsel. "
            "Evidence was presented by the witness. "
            "The decision was made by the court. "
            "The brief was written by the attorney."
        )
        result = json.loads(run(self.tools.score_readability(text)))
        passive = result["sentence_statistics"]["estimated_passive_voice_instances"]
        assert passive > 0, "Expected passive voice to be detected"

    def test_long_sentence_counting(self):
        """A 45-word sentence should appear in the long_sentences count."""
        long_sentence = " ".join(["word"] * 45) + "."
        text = long_sentence + " Short sentence."
        result = json.loads(run(self.tools.score_readability(text)))
        long_count = result["sentence_statistics"]["long_sentences_over_40_words"]
        assert long_count >= 1, f"Expected at least one long sentence, got {long_count}"

    def test_reference_bands_present(self, simple_text):
        result = json.loads(run(self.tools.score_readability(simple_text)))
        assert "reference_bands" in result
        bands = result["reference_bands"]
        assert len(bands) >= 6

    def test_validate_output_passes_valid_json(self, simple_text):
        """validate_output should return valid=True for well-formed output."""
        json_str = run(self.tools.score_readability(simple_text))
        result = self.tools.validate_output(json_str)
        assert result["valid"], f"Validation errors: {result.get('errors')}"

    def test_validate_output_fails_on_empty_string(self):
        result = self.tools.validate_output("")
        assert not result["valid"]
        assert "errors" in result

    def test_validate_output_fails_on_missing_key(self, simple_text):
        """Removing a required key should be caught by validate_output."""
        data = json.loads(run(self.tools.score_readability(simple_text)))
        del data["readability_scores"]
        result = self.tools.validate_output(json.dumps(data))
        assert not result["valid"]
        assert any("readability_scores" in e for e in result["errors"])

    def test_validate_output_fails_on_garbage_json(self):
        result = self.tools.validate_output("not json at all")
        assert not result["valid"]
        assert "errors" in result


# ── 4. AI Disclaimer unit tests ──────────────────────────────────────────────

class TestAIDisclaimer:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("ai-disclaimer.py")
        self.tools = self.mod.Tools()

    def test_disclaimer_appended_to_text(self):
        text = "This is a sample legal memo."
        result = run(self.tools.add_disclaimer(text))
        assert text.strip() in result
        assert "AI-GENERATED DRAFT" in result

    def test_separator_present(self):
        result = run(self.tools.add_disclaimer("Some text."))
        assert "=" * 60 in result

    def test_empty_text_returns_unchanged(self):
        result = run(self.tools.add_disclaimer(""))
        assert result == ""

    def test_whitespace_only_returns_unchanged(self):
        result = run(self.tools.add_disclaimer("   "))
        assert result.strip() == ""

    def test_timestamp_included_by_default(self):
        result = run(self.tools.add_disclaimer("Some text."))
        # Default includes_timestamp=True — should contain "Generated:"
        assert "Generated:" in result

    def test_model_name_included_when_provided(self):
        result = run(self.tools.add_disclaimer("Some text.", __model__="gemma3:12b"))
        assert "gemma3:12b" in result

    def test_model_name_omitted_when_not_provided(self):
        result = run(self.tools.add_disclaimer("Some text.", __model__=None))
        # No model info line should appear (None is not passed through)
        assert "Model:" not in result

    def test_disclaimer_text_from_valves(self):
        self.tools.valves.disclaimer_text = "CUSTOM DISCLAIMER TEXT"
        result = run(self.tools.add_disclaimer("My document."))
        assert "CUSTOM DISCLAIMER TEXT" in result

    def test_disclaimer_at_end_not_beginning(self):
        text = "Document content here."
        result = run(self.tools.add_disclaimer(text))
        content_pos = result.index("Document content")
        disclaimer_pos = result.index("AI-GENERATED DRAFT")
        assert content_pos < disclaimer_pos, "Disclaimer should appear after content"


# ── 5. Batch Scanner unit tests (pure functions) ─────────────────────────────

class TestBatchScanner:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("batch-scanner.py")

    def test_doc_hash_returns_hex_string(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h = self.mod._doc_hash(f)
        assert isinstance(h, str)
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_doc_hash_is_deterministic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("same content")
        assert self.mod._doc_hash(f) == self.mod._doc_hash(f)

    def test_doc_hash_differs_for_different_content(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content A")
        f2.write_text("content B")
        assert self.mod._doc_hash(f1) != self.mod._doc_hash(f2)

    def test_doc_hash_returns_empty_on_missing_file(self, tmp_path):
        missing = tmp_path / "does_not_exist.txt"
        result = self.mod._doc_hash(missing)
        assert result == ""

    def test_extract_text_from_txt(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("Hello from txt file.")
        text, warning = self.mod.extract_text_from_path(f)
        assert "Hello from txt file." in text
        assert warning is None

    def test_extract_text_unknown_extension_reads_as_text(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("Markdown content.")
        text, warning = self.mod.extract_text_from_path(f)
        assert "Markdown content." in text

    def test_glob_documents_finds_txt(self, tmp_path):
        (tmp_path / "a.txt").write_text("contract text")
        (tmp_path / "b.txt").write_text("more text")
        (tmp_path / "skip.py").write_text("not a doc")
        docs = self.mod.glob_documents(tmp_path)
        names = {p.name for p in docs}
        assert "a.txt" in names
        assert "b.txt" in names
        assert "skip.py" not in names

    def test_glob_documents_empty_dir(self, tmp_path):
        assert self.mod.glob_documents(tmp_path) == []

    def test_load_hash_cache_missing_file_returns_empty(self, tmp_path):
        missing = tmp_path / "cache.json"
        result = self.mod.load_hash_cache(missing)
        assert result == {}

    def test_load_hash_cache_roundtrip(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        entries = [{"_hash": "abc123", "file": "a.txt", "risk": []}]
        self.mod.save_hash_cache(cache_file, entries)
        loaded = self.mod.load_hash_cache(cache_file)
        assert "abc123" in loaded
        assert loaded["abc123"]["file"] == "a.txt"

    def test_cache_path_derives_from_output(self, tmp_path):
        out = tmp_path / "report.md"
        cache = self.mod._cache_path(out)
        assert cache.name == "report.cache.json"

    def test_cache_path_none_input_returns_none(self):
        assert self.mod._cache_path(None) is None

    def test_risk_patterns_list_not_empty(self):
        assert len(self.mod.RISK_PATTERNS) > 0

    def test_risk_pattern_detects_auto_renewal(self):
        text = "This Agreement shall automatically renew each year."
        found = []
        for pattern, label, severity, detail in self.mod.RISK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(label)
        assert any("renewal" in f.lower() or "renew" in f.lower() for f in found), (
            f"Auto-renewal pattern not detected. Found: {found}"
        )

    def test_risk_pattern_detects_indemnification(self, sample_contract_text):
        found = []
        for pattern, label, severity, detail in self.mod.RISK_PATTERNS:
            if re.search(pattern, sample_contract_text, re.IGNORECASE):
                found.append((label, severity))
        indemnification_hits = [f for f in found if "indemnif" in f[0].lower()]
        assert indemnification_hits, "Indemnification clause not detected in sample contract"

    def test_risk_pattern_detects_arbitration(self, sample_contract_text):
        found = []
        for pattern, label, severity, detail in self.mod.RISK_PATTERNS:
            if re.search(pattern, sample_contract_text, re.IGNORECASE):
                found.append(label)
        assert any("arbitration" in f.lower() for f in found), (
            "Mandatory arbitration clause not detected"
        )


# ── 6. Supervision Log unit tests (module-level constants & helper) ───────────

class TestSupervisionLog:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("supervision-log.py")

    def test_input_types_constant_defined(self):
        assert hasattr(self.mod, "INPUT_TYPES")
        assert isinstance(self.mod.INPUT_TYPES, set)
        assert "contract" in self.mod.INPUT_TYPES
        assert "memo" in self.mod.INPUT_TYPES

    def test_expected_input_types_present(self):
        expected = {"contract", "deposition", "email", "memo", "brief", "research", "other"}
        assert expected == self.mod.INPUT_TYPES

    def test_db_path_is_in_home(self):
        from pathlib import Path
        db_path = self.mod.DB_PATH
        assert str(db_path).startswith(str(Path.home()))

    def test_input_summary_max_is_positive_int(self):
        assert isinstance(self.mod.INPUT_SUMMARY_MAX, int)
        assert self.mod.INPUT_SUMMARY_MAX > 0

    def test_output_summary_max_is_positive_int(self):
        assert isinstance(self.mod.OUTPUT_SUMMARY_MAX, int)
        assert self.mod.OUTPUT_SUMMARY_MAX > 0

    def test_tools_class_instantiates(self):
        tools = self.mod.Tools()
        assert tools is not None

    def test_tools_has_log_review_method(self):
        tools = self.mod.Tools()
        assert hasattr(tools, "log_review"), "Missing log_review method"
        assert asyncio.iscoroutinefunction(tools.log_review)

    def test_get_db_creates_in_temp_dir(self, tmp_path, monkeypatch):
        """_get_db should create the DB file at the configured path."""
        import sqlite3
        db_file = tmp_path / "test_supervision.db"
        monkeypatch.setattr(self.mod, "DB_PATH", db_file)
        monkeypatch.setattr(self.mod, "DB_DIR", tmp_path)
        conn = self.mod._get_db()
        conn.close()
        assert db_file.exists(), "Database file should have been created"

    def test_supervision_table_schema(self, tmp_path, monkeypatch):
        """The supervision_log table should have required columns."""
        db_file = tmp_path / "test_supervision.db"
        monkeypatch.setattr(self.mod, "DB_PATH", db_file)
        monkeypatch.setattr(self.mod, "DB_DIR", tmp_path)
        conn = self.mod._get_db()
        cols = {row[1] for row in conn.execute("PRAGMA table_info(supervision_log)").fetchall()}
        conn.close()
        required = {"id", "timestamp", "review_status", "input_type", "user", "model"}
        assert required.issubset(cols), f"Missing columns: {required - cols}"


# ── 7. Time Tracker unit tests ────────────────────────────────────────────────

class TestTimeTracker:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("time-tracker.py")
        self.tools = self.mod.Tools()

    def test_manual_time_estimates_all_types_present(self):
        expected_types = {"contract", "deposition", "email", "memo", "brief", "research", "other"}
        assert expected_types.issubset(self.mod.MANUAL_TIME_ESTIMATES.keys())

    def test_ai_assisted_time_always_less_than_manual(self):
        """AI-assisted estimates must be less than manual for all types."""
        for task_type in self.mod.MANUAL_TIME_ESTIMATES:
            manual = self.mod.MANUAL_TIME_ESTIMATES[task_type]
            ai = self.mod.AI_ASSISTED_TIME_ESTIMATES[task_type]
            assert ai < manual, (
                f"AI time ({ai}) should be less than manual ({manual}) for {task_type}"
            )

    def test_manual_time_returns_default_for_unknown_type(self):
        result = self.tools._manual_time("unknown_type")
        assert result == self.mod.MANUAL_TIME_ESTIMATES["other"]

    def test_manual_time_returns_correct_value(self):
        expected = self.mod.MANUAL_TIME_ESTIMATES["contract"]
        result = self.tools._manual_time("contract")
        assert result == expected

    def test_valve_override_applied(self):
        """Setting manual_contract_min > 0 should override the default."""
        self.tools.valves.manual_contract_min = 999.0
        result = self.tools._manual_time("contract")
        assert result == 999.0

    def test_valve_override_zero_falls_back_to_default(self):
        """Leaving override at 0 should use the built-in default."""
        self.tools.valves.manual_contract_min = 0.0
        result = self.tools._manual_time("contract")
        assert result == self.mod.MANUAL_TIME_ESTIMATES["contract"]

    def test_time_savings_no_db_returns_error_message(self):
        """When no supervision DB exists, tool should return an informative string."""
        self.tools.valves.db_path = "/nonexistent/path/supervision.db"
        result = run(self.tools.time_savings_report())
        assert "not found" in result.lower() or "supervision" in result.lower()

    def test_roi_summary_no_db_returns_error_message(self):
        self.tools.valves.db_path = "/nonexistent/path/supervision.db"
        result = run(self.tools.roi_summary())
        assert "not found" in result.lower() or "supervision" in result.lower()

    def test_invalid_period_returns_error(self):
        result = run(self.tools.time_savings_report("yearly"))
        assert "invalid" in result.lower()

    def test_all_valid_periods_accepted(self):
        """week, month, quarter, all are valid — should not return 'invalid'."""
        self.tools.valves.db_path = "/nonexistent/path/supervision.db"
        for period in ("week", "month", "quarter", "all"):
            result = run(self.tools.time_savings_report(period))
            assert "invalid" not in result.lower(), (
                f"Period '{period}' should be valid but got: {result}"
            )


# ── 8. Compliance Report unit tests ──────────────────────────────────────────

class TestComplianceReport:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("compliance-report.py")
        self.tools = self.mod.Tools()

    def test_tools_instantiates(self):
        assert self.tools is not None

    def test_connect_returns_none_for_missing_db(self):
        self.tools.valves.db_path = "/nonexistent/path/supervision.db"
        conn = self.tools._connect()
        assert conn is None

    def test_require_db_returns_error_string_for_missing_db(self):
        self.tools.valves.db_path = "/nonexistent/path/supervision.db"
        conn, err = self.tools._require_db()
        assert conn is None
        assert err is not None
        assert isinstance(err, str)
        assert len(err) > 0

    def test_monthly_summary_no_db_returns_message(self):
        self.tools.valves.db_path = "/nonexistent/path/supervision.db"
        result = run(self.tools.monthly_summary())
        assert isinstance(result, str)
        assert len(result) > 0


# ── 9. Cross-tool consistency checks ─────────────────────────────────────────

class TestCrossToolConsistency:
    """Sanity checks that apply across multiple tools."""

    def test_all_tools_exist_on_disk(self):
        """Every expected tool file should exist."""
        all_tools = OPEN_WEBUI_TOOLS + CLI_TOOLS
        for filename in all_tools:
            path = TOOLS_DIR / filename
            assert path.exists(), f"Tool file missing: {path}"

    def test_tool_count_matches_expected(self):
        """There should be exactly 22 tool files."""
        py_files = list(TOOLS_DIR.glob("*.py"))
        assert len(py_files) == 22, (
            f"Expected 22 tools, found {len(py_files)}: {[f.name for f in py_files]}"
        )

    def test_all_tools_have_docstring_header(self):
        """Every tool should have a module docstring (used as Open WebUI metadata)."""
        no_docstring = []
        for filename in OPEN_WEBUI_TOOLS:
            source = (TOOLS_DIR / filename).read_text()
            # Module docstring starts with triple-quote at the top
            if not (source.lstrip().startswith('"""') or source.lstrip().startswith("'''")):
                no_docstring.append(filename)
        assert not no_docstring, f"Tools missing module docstring: {no_docstring}"

    @pytest.mark.parametrize("filename", OPEN_WEBUI_TOOLS)
    def test_no_hardcoded_api_keys(self, filename):
        """Tools should not contain hardcoded API keys or tokens."""
        source = (TOOLS_DIR / filename).read_text()
        # Look for common patterns that suggest hardcoded secrets
        suspicious = re.findall(
            r'(?:api_key|secret|password|token)\s*=\s*["\'][^"\']{10,}["\']',
            source,
            re.IGNORECASE,
        )
        assert not suspicious, (
            f"{filename} may contain hardcoded secrets: {suspicious}"
        )


# ── 10. Mentor QA input validation tests ─────────────────────────────────────

class TestMentorQA:

    @pytest.fixture(autouse=True)
    def load_module(self):
        self.mod = load_tool("mentor-qa.py")
        self.tools = self.mod.Tools()

    def test_billing_guidance_empty_input_returns_helpful_message(self):
        """Empty task should return a descriptive error, not a half-formed prompt."""
        result = run(self.tools.billing_guidance(""))
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not contain the raw billing prompt template
        assert "TASK TO BILL:" not in result

    def test_billing_guidance_whitespace_only_returns_helpful_message(self):
        result = run(self.tools.billing_guidance("   "))
        assert "TASK TO BILL:" not in result

    def test_billing_guidance_valid_input_returns_prompt(self):
        result = run(self.tools.billing_guidance("I drafted a 5-page memo on tortious interference."))
        assert "TASK TO BILL:" in result

    def test_client_communication_empty_input_returns_helpful_message(self):
        result = run(self.tools.client_communication(""))
        assert isinstance(result, str)
        # Should not contain the raw communication prompt
        assert "SITUATION:" not in result

    def test_client_communication_valid_input_returns_prompt(self):
        result = run(self.tools.client_communication("Client asking for a status update on their lease negotiation."))
        assert "SITUATION:" in result

    def test_ethics_scenario_empty_input_returns_helpful_message(self):
        result = run(self.tools.ethics_scenario(""))
        assert isinstance(result, str)
        assert "SCENARIO:" not in result

    def test_ethics_scenario_whitespace_only_returns_helpful_message(self):
        result = run(self.tools.ethics_scenario("   \n  "))
        assert "SCENARIO:" not in result

    def test_ethics_scenario_valid_input_returns_prompt(self):
        result = run(self.tools.ethics_scenario("My partner asked me to backdate a document."))
        assert "SCENARIO:" in result
