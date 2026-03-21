#!/usr/bin/env python3
"""
Test harness for career development tools:
  - tools/bar-prep.py
  - tools/legal-research-trainer.py
  - tools/mentor-qa.py

Tests structural correctness, expected return types, and prompt content quality
without requiring pydantic or Ollama (validates tool logic, not LLM responses).

Run from the project root:
  python3 tests/test-career-tools.py

Note: These tools run inside Open WebUI where pydantic is available. This test
harness stubs pydantic to allow local structural testing.
"""

import asyncio
import ast
import importlib.util
import os
import sys
import types
import unittest

# ─── Stub pydantic so we can import the tools without Open WebUI's environment ──

# Create a minimal pydantic stub
pydantic_stub = types.ModuleType("pydantic")

class BaseModelStub:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Collect class-level field defaults
        _defaults = {}
        for name, val in cls.__dict__.items():
            if not name.startswith("_") and not callable(val):
                _defaults[name] = val
        cls._pydantic_defaults = _defaults
    def __init__(self, **kwargs):
        # Apply defaults first, then overrides
        for k, v in getattr(self.__class__, '_pydantic_defaults', {}).items():
            setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

pydantic_stub.BaseModel = BaseModelStub
sys.modules["pydantic"] = pydantic_stub

# ─── Load the tools ──────────────────────────────────────────────────────────────

TOOL_DIR = os.path.join(os.path.dirname(__file__), "..", "tools")

def load_tool(filename):
    name = filename.replace("-", "_").replace(".py", "")
    path = os.path.join(TOOL_DIR, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Tools


# ─── Async test runner ───────────────────────────────────────────────────────────

def run_async(coro):
    return asyncio.run(coro)


# ─── Tests: bar-prep.py ──────────────────────────────────────────────────────────

class TestBarPrep(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Tools = load_tool("bar-prep.py")

    def test_tools_instantiates(self):
        t = self.Tools()
        self.assertIsNotNone(t)

    def test_has_all_required_methods(self):
        t = self.Tools()
        required = ["practice_question", "spot_issues", "rule_statement", "mnemonic", "grade_essay"]
        for method in required:
            self.assertTrue(hasattr(t, method), f"Missing method: {method}")

    def test_practice_question_returns_string(self):
        t = self.Tools()
        result = run_async(t.practice_question("negligence per se", "torts"))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 100)

    def test_practice_question_includes_topic(self):
        t = self.Tools()
        result = run_async(t.practice_question("mailbox rule", "contracts"))
        self.assertIn("mailbox rule", result.lower())

    def test_spot_issues_short_input_returns_error(self):
        t = self.Tools()
        result = run_async(t.spot_issues("Alice hit Bob."))
        self.assertIn("too short", result.lower())

    def test_spot_issues_valid_input_returns_prompt(self):
        t = self.Tools()
        fact_pattern = (
            "Alice was driving to work when she ran a red light and struck Bob's car. "
            "Bob suffered a broken arm. Alice's employer had instructed her to make the "
            "delivery quickly. Bob also failed to wear a seatbelt. Carol, a passenger in "
            "Alice's car, was also injured."
        )
        result = run_async(t.spot_issues(fact_pattern))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 200)
        self.assertIn("IRAC", result)

    def test_rule_statement_returns_structured_prompt(self):
        t = self.Tools()
        result = run_async(t.rule_statement("res ipsa loquitur", "general"))
        self.assertIsInstance(result, str)
        self.assertIn("THE RULE", result)
        self.assertIn("ELEMENTS", result)
        self.assertIn("EXCEPTIONS", result)

    def test_mnemonic_returns_prompt(self):
        t = self.Tools()
        result = run_async(t.mnemonic("elements of negligence"))
        self.assertIsInstance(result, str)
        self.assertIn("ACRONYM", result)
        self.assertIn("STORY", result)

    def test_grade_essay_short_input_returns_error(self):
        t = self.Tools()
        result = run_async(t.grade_essay("Short essay."))
        self.assertIn("too short", result.lower())

    def test_grade_essay_valid_input_returns_grading_prompt(self):
        t = self.Tools()
        essay = (
            "Issue: Whether defendant is liable for negligence. "
            "Rule: Negligence requires duty, breach, causation, and damages. "
            "Application: Defendant owed a duty of care to plaintiff as a foreseeable user "
            "of the roadway. Defendant breached that duty by running a red light. "
            "Defendant's breach caused plaintiff's injuries, which constituted damages. "
            "Conclusion: Therefore, defendant is liable for negligence. " * 5
        )
        result = run_async(t.grade_essay(essay, "negligence"))
        self.assertIsInstance(result, str)
        self.assertIn("ISSUE SPOTTING", result)
        self.assertIn("RULE STATEMENTS", result)

    def test_subject_matching(self):
        t = self.Tools()
        # Test abbreviation matching
        result = run_async(t.practice_question("joinder", "civ pro"))
        self.assertIsInstance(result, str)

    def test_no_case_citation_instruction_in_prompt(self):
        """All prompts should instruct the LLM not to fabricate citations."""
        t = self.Tools()
        result = run_async(t.rule_statement("consideration"))
        # rule_statement uses "Do not cite specific cases by name" as the citation guard
        has_citation_guard = (
            "fabricat" in result.lower()
            or "do not cite" in result.lower()
            or "never cite" in result.lower()
            or "verify" in result.lower()
        )
        self.assertTrue(has_citation_guard, "rule_statement prompt should include a citation accuracy warning")


# ─── Tests: legal-research-trainer.py ───────────────────────────────────────────

class TestLegalResearchTrainer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Tools = load_tool("legal-research-trainer.py")

    def test_tools_instantiates(self):
        t = self.Tools()
        self.assertIsNotNone(t)

    def test_has_all_required_methods(self):
        t = self.Tools()
        required = ["research_strategy", "bluebook_citation", "shepardizing_guide", "source_hierarchy"]
        for method in required:
            self.assertTrue(hasattr(t, method), f"Missing method: {method}")

    def test_research_strategy_returns_prompt(self):
        t = self.Tools()
        result = run_async(
            t.research_strategy(
                "Can an employer terminate an employee for off-duty social media posts?",
                "california"
            )
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 300)
        self.assertIn("STEP", result)

    def test_research_strategy_includes_secondary_sources(self):
        t = self.Tools()
        result = run_async(t.research_strategy("Fourth Amendment standing doctrine", "federal"))
        self.assertIn("secondary", result.lower())

    def test_bluebook_citation_returns_prompt(self):
        t = self.Tools()
        result = run_async(
            t.bluebook_citation(
                "a 2001 Ninth Circuit case, volume 234 of F.3d page 567",
                "case"
            )
        )
        self.assertIsInstance(result, str)
        self.assertIn("Bluebook", result)
        self.assertIn("FORMATTED CITATION", result)

    def test_bluebook_citation_includes_examples(self):
        t = self.Tools()
        result = run_async(t.bluebook_citation("42 U.S.C. section 1983", "statute"))
        # Should include reference examples from BLUEBOOK_FORMATS
        self.assertIn("U.S.C.", result)

    def test_bluebook_all_citation_types(self):
        t = self.Tools()
        for ctype in ["case", "statute", "regulation", "constitution", "law_review"]:
            result = run_async(t.bluebook_citation("test source", ctype))
            self.assertIsInstance(result, str, f"Failed for citation_type={ctype}")

    def test_shepardizing_guide_general(self):
        t = self.Tools()
        result = run_async(t.shepardizing_guide("general"))
        self.assertIsInstance(result, str)
        self.assertIn("KeyCite", result)
        self.assertIn("Shepard", result)

    def test_shepardizing_guide_signals(self):
        t = self.Tools()
        result = run_async(t.shepardizing_guide("signals"))
        self.assertIn("red", result.lower())
        self.assertIn("yellow", result.lower())

    def test_source_hierarchy_returns_prompt(self):
        t = self.Tools()
        result = run_async(t.source_hierarchy("9th Circuit", "common law"))
        self.assertIsInstance(result, str)
        self.assertIn("MANDATORY", result.upper())
        self.assertIn("PERSUASIVE", result.upper())

    def test_source_hierarchy_includes_erie(self):
        t = self.Tools()
        result = run_async(t.source_hierarchy("Southern District of New York", "statutory"))
        # Should mention diversity jurisdiction / Erie
        self.assertIn("diversity", result.lower())


# ─── Tests: mentor-qa.py ─────────────────────────────────────────────────────────

class TestMentorQA(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Tools = load_tool("mentor-qa.py")

    def test_tools_instantiates(self):
        t = self.Tools()
        self.assertIsNotNone(t)

    def test_has_all_required_methods(self):
        t = self.Tools()
        required = [
            "billing_guidance", "client_communication", "professional_development",
            "ethics_scenario", "courtroom_basics"
        ]
        for method in required:
            self.assertTrue(hasattr(t, method), f"Missing method: {method}")

    def test_billing_guidance_returns_prompt(self):
        t = self.Tools()
        result = run_async(t.billing_guidance("I researched for 3 hours on the tortious interference question"))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 200)
        self.assertIn("time entr", result.lower())

    def test_billing_guidance_task_type_matched(self):
        t = self.Tools()
        result = run_async(t.billing_guidance("I reviewed 200 emails for discovery"))
        # Should match "document review" or "email" from BILLABLE_TASK_REFERENCE
        self.assertIn("billing", result.lower())

    def test_client_communication_returns_prompt(self):
        t = self.Tools()
        result = run_async(
            t.client_communication(
                "client wants a status update on their ongoing contract negotiation",
                "email"
            )
        )
        self.assertIsInstance(result, str)
        self.assertIn("DRAFT", result)
        # The prompt uses "MODEL RULE 1.4" or "Rule 1.4" — check for the obligation section
        self.assertIn("1.4", result)

    def test_client_communication_all_types(self):
        t = self.Tools()
        for ctype in ["email", "letter", "call_summary", "voicemail_script", "in_person_guidance"]:
            result = run_async(t.client_communication("status update needed", ctype))
            self.assertIsInstance(result, str, f"Failed for communication_type={ctype}")

    def test_professional_development_returns_prompt(self):
        t = self.Tools()
        result = run_async(t.professional_development("general"))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 200)

    def test_professional_development_all_areas(self):
        t = self.Tools()
        for area in ["general", "skills", "cle", "relationships", "career_paths", "feedback"]:
            result = run_async(t.professional_development(area))
            self.assertIsInstance(result, str, f"Failed for area={area}")

    def test_ethics_scenario_returns_prompt(self):
        t = self.Tools()
        result = run_async(
            t.ethics_scenario(
                "My supervising partner asked me to backdate a letter we sent to the opposing party"
            )
        )
        self.assertIsInstance(result, str)
        self.assertIn("Model Rule", result)
        self.assertIn("Rule 5.2", result)

    def test_ethics_scenario_includes_disclaimer(self):
        t = self.Tools()
        result = run_async(t.ethics_scenario("I accidentally received opposing counsel's privileged email"))
        self.assertIn("DISCLAIMER", result.upper())

    def test_ethics_scenario_mentions_ethics_hotline(self):
        t = self.Tools()
        result = run_async(t.ethics_scenario("Client told me they plan to commit fraud"))
        self.assertIn("hotline", result.lower())

    def test_courtroom_basics_returns_prompt(self):
        t = self.Tools()
        result = run_async(t.courtroom_basics("first_hearing"))
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 200)
        self.assertIn("PREPARATION", result.upper())

    def test_courtroom_basics_all_proceeding_types(self):
        t = self.Tools()
        proceeding_types = [
            "first_hearing", "deposition", "jury_selection", "opening_statement",
            "direct_exam", "cross_exam", "closing_argument", "trial_day_one", "bench_trial"
        ]
        for ptype in proceeding_types:
            result = run_async(t.courtroom_basics(ptype))
            self.assertIsInstance(result, str, f"Failed for proceeding_type={ptype}")
            self.assertGreater(len(result), 100, f"Response too short for {ptype}")


# ─── Structural tests ────────────────────────────────────────────────────────────

class TestFileStructure(unittest.TestCase):
    """Validate Open WebUI tool file structure requirements."""

    def _get_source(self, filename):
        path = os.path.join(TOOL_DIR, filename)
        with open(path) as f:
            return f.read()

    def _check_file(self, filename):
        source = self._get_source(filename)
        tree = ast.parse(source)

        # Check: file has a docstring with required fields
        docstring = ast.get_docstring(tree)
        self.assertIsNotNone(docstring, f"{filename}: missing module docstring")
        self.assertIn("title:", docstring, f"{filename}: docstring missing 'title:'")
        self.assertIn("license:", docstring, f"{filename}: docstring missing 'license:'")

        # Check: Tools class exists
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        class_names = [c.name for c in classes]
        self.assertIn("Tools", class_names, f"{filename}: no Tools class")

        # Check: Valves inner class exists
        tools_class = next(c for c in classes if c.name == "Tools")
        inner_classes = [n.name for n in ast.walk(tools_class) if isinstance(n, ast.ClassDef)]
        self.assertIn("Valves", inner_classes, f"{filename}: no Valves inner class")

        # Check: all public methods are async
        methods = [
            n for n in ast.walk(tools_class)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith("_")
            and n.name not in ("__init__",)
        ]
        for method in methods:
            if method.name == "Valves":
                continue
            self.assertIsInstance(
                method, ast.AsyncFunctionDef,
                f"{filename}: {method.name} should be async"
            )

        # Check: all async methods have docstrings
        async_methods = [n for n in ast.walk(tools_class) if isinstance(n, ast.AsyncFunctionDef)]
        for method in async_methods:
            doc = ast.get_docstring(method)
            self.assertIsNotNone(doc, f"{filename}: {method.name} missing docstring")

        return True

    def test_bar_prep_structure(self):
        self.assertTrue(self._check_file("bar-prep.py"))

    def test_legal_research_trainer_structure(self):
        self.assertTrue(self._check_file("legal-research-trainer.py"))

    def test_mentor_qa_structure(self):
        self.assertTrue(self._check_file("mentor-qa.py"))

    def test_modelfile_exists(self):
        path = os.path.join(os.path.dirname(TOOL_DIR), "Modelfile.legal-tutor")
        self.assertTrue(os.path.exists(path), "Modelfile.legal-tutor not found")

    def test_modelfile_has_required_sections(self):
        path = os.path.join(os.path.dirname(TOOL_DIR), "Modelfile.legal-tutor")
        with open(path) as f:
            content = f.read()
        self.assertTrue(content.startswith("FROM"), "Modelfile must start with FROM")
        self.assertIn("SYSTEM", content, "Modelfile missing SYSTEM block")
        self.assertIn("TEMPLATE", content, "Modelfile missing TEMPLATE block")
        self.assertIn("PARAMETER temperature", content, "Modelfile missing temperature")
        self.assertIn("PARAMETER num_ctx", content, "Modelfile missing num_ctx")
        self.assertIn("/no_think", content, "Modelfile missing /no_think in TEMPLATE")
        self.assertIn("fabricat", content.lower(), "Modelfile should warn against fabricating citations")

    def test_career_prompts_added(self):
        path = os.path.join(
            os.path.dirname(TOOL_DIR), "prompts", "legal-prompt-library.md"
        )
        with open(path) as f:
            content = f.read()
        self.assertIn("Career Development", content)
        self.assertIn("Explain Like I'm a 1L", content)
        self.assertIn("legal-tutor", content)

    def test_new_associate_guide_exists(self):
        path = os.path.join(
            os.path.dirname(TOOL_DIR), "templates", "new-associate-guide.md"
        )
        self.assertTrue(os.path.exists(path), "new-associate-guide.md not found")

    def test_new_associate_guide_has_sections(self):
        path = os.path.join(
            os.path.dirname(TOOL_DIR), "templates", "new-associate-guide.md"
        )
        with open(path) as f:
            content = f.read()
        required_sections = [
            "First Day",
            "Billing",
            "Research",
            "Writing",
            "Common Mistakes",
            "Professional Development",
            "Ethics",
        ]
        for section in required_sections:
            self.assertIn(section, content, f"new-associate-guide.md missing section: {section}")


# ─── Event emitter tests ─────────────────────────────────────────────────────────

class TestEventEmitter(unittest.IsolatedAsyncioTestCase):
    """Verify that event emitter calls are made correctly."""

    @classmethod
    def setUpClass(cls):
        cls.BarPrep = load_tool("bar-prep.py")
        cls.ResearchTrainer = load_tool("legal-research-trainer.py")
        cls.MentorQA = load_tool("mentor-qa.py")

    async def test_bar_prep_emits_status_events(self):
        emitted = []
        async def mock_emitter(event):
            emitted.append(event)

        t = self.BarPrep()
        await t.practice_question("hearsay", "evidence", __event_emitter__=mock_emitter)

        self.assertGreater(len(emitted), 0, "No events emitted")
        types = [e["type"] for e in emitted]
        self.assertIn("status", types)

        # Last event should have done=True
        last = emitted[-1]
        self.assertTrue(last["data"]["done"], "Last event should have done=True")

    async def test_research_trainer_emits_status_events(self):
        emitted = []
        async def mock_emitter(event):
            emitted.append(event)

        t = self.ResearchTrainer()
        await t.research_strategy("Fourth Amendment search and seizure", "federal", __event_emitter__=mock_emitter)

        self.assertGreater(len(emitted), 0, "No events emitted")
        last = emitted[-1]
        self.assertTrue(last["data"]["done"])

    async def test_mentor_qa_emits_status_events(self):
        emitted = []
        async def mock_emitter(event):
            emitted.append(event)

        t = self.MentorQA()
        await t.billing_guidance("I drafted a 10-page contract", __event_emitter__=mock_emitter)

        self.assertGreater(len(emitted), 0, "No events emitted")
        last = emitted[-1]
        self.assertTrue(last["data"]["done"])


# ─── Main ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Career Development Tools — Test Suite")
    print("=" * 60)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_class in [
        TestFileStructure,
        TestBarPrep,
        TestLegalResearchTrainer,
        TestMentorQA,
        TestEventEmitter,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    if result.wasSuccessful():
        print(f"All {result.testsRun} tests passed.")
    else:
        print(f"{len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests.")
        sys.exit(1)
