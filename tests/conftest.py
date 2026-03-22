"""
Shared pytest fixtures for local-ai-legal-setup tool tests.

All tools are Open WebUI plugins that run inside an environment where pydantic
is pre-installed. Since the system Python lacks pydantic/textstat, these tests
either use the project venv (.venv/) or stub out the dependencies.

Loading strategy: tools have hyphens in filenames, so we use importlib.
"""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── Path constants ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"

# List of all 22 tool filenames
ALL_TOOLS = [
    "ai-disclaimer.py",
    "bar-exam-simulator.py",
    "bar-prep.py",
    "batch-scanner.py",
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


# ── importlib loader (handles hyphenated filenames) ───────────────────────────

def load_tool_module(filename: str):
    """
    Load a tool module from tools/ by filename.
    Returns the module object. Raises ImportError on failure.
    """
    path = TOOLS_DIR / filename
    module_name = filename.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_event_emitter():
    """A no-op async event emitter that accepts any status payload."""
    async def emitter(event):
        pass
    return emitter


@pytest.fixture
def sample_contract_text():
    return """
    SERVICE AGREEMENT

    This Agreement is entered into between Acme Corp ("Client") and TechVendor Inc ("Vendor")
    on January 1, 2024.

    1. TERM: This Agreement shall commence on January 1, 2024 and continue for twelve (12) months.
       The Agreement shall automatically renew unless either party provides thirty (30) days written notice.

    2. PAYMENT: Client shall pay Vendor $10,000 per month within net-30 days of invoice.
       Late payments accrue interest at 1.5% per month.

    3. INDEMNIFICATION: Client shall indemnify, defend, and hold harmless Vendor from any
       claims arising out of Client's use of the services.

    4. LIMITATION OF LIABILITY: In no event shall either party be liable for indirect,
       incidental, or consequential damages. Total liability shall not exceed the fees
       paid in the prior three months.

    5. TERMINATION: Either party may terminate this Agreement for any reason with thirty
       (30) days written notice. Vendor may terminate immediately for non-payment.

    6. GOVERNING LAW: This Agreement shall be governed by the laws of California.
       Any disputes shall be resolved through binding arbitration in San Francisco, CA.
    """


@pytest.fixture
def sample_legal_brief_text():
    return """
    IN THE UNITED STATES COURT OF APPEALS FOR THE NINTH CIRCUIT

    SMITH v. JONES, 42 F.3d 101 (9th Cir. 1995).

    The district court erred in granting summary judgment. See Anderson v. Liberty Lobby,
    Inc., 477 U.S. 242 (1986). The plaintiff presented sufficient evidence to create a
    genuine issue of material fact under 42 U.S.C. § 1983.

    Furthermore, the court failed to apply the correct standard. See generally Celotex Corp.
    v. Catrett, 477 U.S. 317 (1986). The respondent's reliance on cases decided under
    29 C.F.R. § 1926.451 is misplaced given the distinct factual record here.
    """


@pytest.fixture
def simple_text():
    return "The cat sat on the mat. It was a very small cat. The mat was red."


@pytest.fixture
def null_event_emitter():
    """Returns None — for tools that accept optional emitters."""
    return None
