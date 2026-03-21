"""
title: Court Filing Rules Checker
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Checks a legal document against court filing rules for a specific jurisdiction.
  Catches formatting issues before filing: word/page limits, required sections,
  certificate of compliance, citation formatting, and common rejection reasons.
  Covers all federal circuit courts, SCOTUS, and major state courts.
  Works as an Open WebUI tool or standalone via CLI / legal-check -m rules.

Standalone CLI:
  python3 tools/court-rules-checker.py --jurisdiction 9th-circuit brief.txt
  python3 tools/court-rules-checker.py --list-jurisdictions
  python3 tools/court-rules-checker.py --jurisdiction cal-superior --json motion.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from pydantic import BaseModel
except ImportError:
    # Pydantic not required for standalone CLI use — Open WebUI provides it
    class BaseModel:  # type: ignore[no-redef]
        """Minimal BaseModel stub for environments without pydantic."""
        pass


# ── Resolve rules database ────────────────────────────────────────────────────

def _find_rules_db() -> Path:
    """Locate court-rules.json relative to this file or in CWD."""
    candidates = [
        Path(__file__).parent.parent / "rules" / "court-rules.json",
        Path.cwd() / "rules" / "court-rules.json",
        Path(__file__).parent / "court-rules.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "court-rules.json not found. Expected at rules/court-rules.json "
        "relative to the project root."
    )


def _load_rules() -> dict:
    db_path = _find_rules_db()
    with open(db_path, encoding="utf-8") as fh:
        data = json.load(fh)
    # Strip metadata key
    return {k: v for k, v in data.items() if not k.startswith("_")}


# ── Section detection helpers ─────────────────────────────────────────────────

# Maps canonical section names to the regex patterns that detect them in text.
# Multiple patterns per section — any match is sufficient.
SECTION_PATTERNS: dict[str, list[str]] = {
    "Table of Contents": [
        r"table\s+of\s+contents",
        r"TABLE\s+OF\s+CONTENTS",
    ],
    "Table of Authorities": [
        r"table\s+of\s+authorities",
        r"TABLE\s+OF\s+AUTHORITIES",
    ],
    "Certificate of Compliance": [
        r"certificate\s+of\s+(compliance|word\s+count|service\s+and\s+compliance)",
        r"CERTIFICATE\s+OF\s+(COMPLIANCE|WORD\s+COUNT)",
        r"certif(?:y|ies|ication)\s+(?:that\s+)?(?:this\s+)?(?:brief|document|filing)\s+(?:complies|contains)",
        r"I\s+certify\s+that\s+this\s+(?:brief|document)",
        r"pursuant\s+to\s+(?:FRAP|Fed\.\s*R\.\s*App\.\s*P\.)\s*32",
        r"word\s+count\s+(?:for\s+)?(?:this\s+)?(?:brief|document)\s+(?:is|does\s+not\s+exceed)",
    ],
    "Certificate of Service": [
        r"certificate\s+of\s+service",
        r"CERTIFICATE\s+OF\s+SERVICE",
        r"I\s+(?:hereby\s+)?certify\s+that\s+(?:on|today|I)\s+(?:have\s+)?served",
        r"proof\s+of\s+service",
    ],
    "Cover Page": [
        r"(?:IN\s+THE\s+)?(?:UNITED\s+STATES\s+COURT\s+OF\s+APPEALS|SUPREME\s+COURT)",
        r"No\.\s+\d{2}-\d+",
        r"Case\s+No\.\s+\d",
        r"Docket\s+No\.",
    ],
    "Jurisdictional Statement": [
        r"jurisdictional\s+statement",
        r"JURISDICTIONAL\s+STATEMENT",
        r"statement\s+of\s+jurisdiction",
        r"STATEMENT\s+OF\s+JURISDICTION",
        r"jurisdiction\s+(?:is\s+)?(?:vested|conferred|based)",
        r"this\s+court\s+has\s+jurisdiction",
    ],
    "Statement of Issues": [
        r"(?:statement\s+of\s+)?issues?\s+(?:presented|on\s+appeal|raised)",
        r"STATEMENT\s+OF\s+ISSUES?",
        r"ISSUES?\s+(?:PRESENTED|ON\s+APPEAL|RAISED)",
        r"questions?\s+presented",
        r"QUESTIONS?\s+PRESENTED",
    ],
    "Questions Presented": [
        r"questions?\s+presented",
        r"QUESTIONS?\s+PRESENTED",
    ],
    "Statement of the Case": [
        r"statement\s+of\s+(?:the\s+)?case(?:\s+and\s+facts?)?",
        r"STATEMENT\s+OF\s+(?:THE\s+)?CASE(?:\s+AND\s+FACTS?)?",
    ],
    "Statement of Facts": [
        r"statement\s+of\s+(?:the\s+)?facts?",
        r"STATEMENT\s+OF\s+(?:THE\s+)?FACTS?",
        r"factual\s+background",
        r"FACTUAL\s+BACKGROUND",
    ],
    "Summary of Argument": [
        r"summary\s+of\s+(?:the\s+)?argument",
        r"SUMMARY\s+OF\s+(?:THE\s+)?ARGUMENT",
    ],
    "Argument": [
        r"^ARGUMENT\s*$",
        r"\bARGUMENT\b",
        r"^argument\s*$",
    ],
    "Conclusion": [
        r"^CONCLUSION\s*$",
        r"\bCONCLUSION\b",
        r"^conclusion\s*$",
        r"for\s+(?:the\s+)?(?:foregoing|above)\s+reasons",
        r"WHEREFORE",
        r"respectfully\s+(?:requests?|submits?|prays?)",
    ],
    "Caption": [
        r"IN\s+THE\s+(?:SUPERIOR|CIRCUIT|DISTRICT|SUPREME)\s+COURT",
        r"(?:Plaintiff|Defendant|Petitioner|Respondent|Appellant|Appellee)\s*[,.]",
        r"Case\s+No\.",
        r"Docket\s+No\.",
        r"v\.\s*$",
    ],
    "Introduction": [
        r"^INTRODUCTION\s*$",
        r"\bINTRODUCTION\b",
        r"^introduction\s*$",
    ],
    "Background": [
        r"^BACKGROUND\s*$",
        r"\bBACKGROUND\b",
        r"^background\s*$",
        r"^FACTUAL\s+BACKGROUND\s*$",
    ],
    "Opinions Below": [
        r"opinions?\s+below",
        r"OPINIONS?\s+BELOW",
        r"decision\s+below",
    ],
    "Jurisdiction": [
        r"^JURISDICTION\s*$",
        r"\bJURISDICTION\b",
    ],
    "Constitutional and Statutory Provisions": [
        r"constitutional\s+and\s+statutory\s+provisions?",
        r"CONSTITUTIONAL\s+AND\s+STATUTORY\s+PROVISIONS?",
        r"statutes?\s+involved",
        r"relevant\s+(?:statutes?|provisions?)",
    ],
    "Statement": [
        r"^STATEMENT\s*$",
        r"STATEMENT\s+OF\s+THE\s+CASE",
    ],
    "Glossary of Abbreviations": [
        r"glossary\s+of\s+(?:abbreviations?|acronyms?)",
        r"GLOSSARY\s+OF\s+(?:ABBREVIATIONS?|ACRONYMS?)",
        r"list\s+of\s+abbreviations?",
    ],
    "Statement of Related Cases": [
        r"statement\s+of\s+related\s+cases?",
        r"STATEMENT\s+OF\s+RELATED\s+CASES?",
        r"related\s+cases?",
    ],
    "Preliminary Statement": [
        r"preliminary\s+statement",
        r"PRELIMINARY\s+STATEMENT",
    ],
    "Issues Presented": [
        r"issues?\s+presented",
        r"ISSUES?\s+PRESENTED",
    ],
    "Certificate of Compliance (section heading)": [
        r"certificate\s+of\s+compliance",
        r"CERTIFICATE\s+OF\s+COMPLIANCE",
    ],
}

# Canonical aliases: some required_sections keys map to broader detection
_SECTION_ALIASES: dict[str, str] = {
    "Certificate of Compliance": "Certificate of Compliance",
    "Certificate of Service": "Certificate of Service",
    "Cover Page": "Cover Page",
    "Table of Contents": "Table of Contents",
    "Table of Authorities": "Table of Authorities",
    "Statement of the Case": "Statement of the Case",
    "Statement of the Case and Facts": "Statement of the Case",
    "Statement of Issues": "Statement of Issues",
    "Jurisdictional Statement": "Jurisdictional Statement",
    "Statement of Jurisdiction": "Jurisdictional Statement",
}


def _section_present(section_name: str, text: str) -> bool:
    """Return True if the section is detectable in the text."""
    # Resolve alias
    canonical = _SECTION_ALIASES.get(section_name, section_name)
    patterns = SECTION_PATTERNS.get(canonical) or SECTION_PATTERNS.get(section_name)
    if not patterns:
        # No pattern registered — skip this check
        return True
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
            return True
    return False


# ── Citation issue detection ──────────────────────────────────────────────────

# Patterns for "v." that look like case citations but may lack italics.
# Requires a reporter citation nearby (number followed by reporter abbrev or "U.S." etc.)
# to avoid false positives from cover pages and party listings.
CASE_CITATION_PATTERN = re.compile(
    r"([A-Z][A-Za-z\s\.,&']{3,60}?)\s+v\.\s+([A-Z][A-Za-z\s\.,&']{3,60}?)"
    r"(?=,\s+\d+\s+[A-Z]|\s+\d+\s+(?:U\.S\.|F\.|S\.Ct\.|N\.Y\.|Cal\.|Tex\.|F\.2d|F\.3d|F\.4th|B\.R\.))",
    re.MULTILINE,
)

# Signals used without proper formatting (e.g., "see" uncapitalized, missing comma)
SIGNAL_ISSUES = [
    (re.compile(r"\bsee\s+[A-Z]"), "Lowercase 'see' — Bluebook signals are capitalized at start of citation sentence"),
    (re.compile(r"\bSee\s+[a-z]"), None),  # OK: see lowercase after signal is fine in some contexts
    (re.compile(r"\bCf\s+"), "'Cf' missing period — should be 'Cf.'"),
    (re.compile(r"\bBut\s+See\b"), "'But See' — should be 'But see' (only first word capitalized)"),
    (re.compile(r"\bSee\s+Also\b"), "'See Also' — should be 'See also'"),
    (re.compile(r"\bId\s+at\b"), "'Id at' — should be 'Id. at'"),
    (re.compile(r"\bId\.\s+[A-Z](?!d\b)"), None),  # OK
    (re.compile(r"\bsupra\s+note\s+\d"), None),  # OK
    (re.compile(r"\bInfra\b"), "'Infra' should be lowercase unless at start of sentence"),
    (re.compile(r"\bSupra\b(?!\s+note)"), "'Supra' should be lowercase unless at start of sentence (and 'supra note X' is the standard form)"),
]

# Missing pinpoint citation after a case citation.
# Flags "123 F.3d 456" not followed by ", [pinpoint page]" or " (year)".
# Does NOT flag citations that are followed by a year parenthetical —
# those are Table of Authorities entries, not in-text citations needing pinpoints.
MISSING_PINPOINT = re.compile(
    r"\d+\s+(?:U\.S\.|F\.\d?|F\.2d|F\.3d|F\.4th|S\.Ct\.|L\.Ed\.(?:2d)?)\s+(\d+)"
    r"(?!\s*,\s*\d)"      # not followed by comma + pinpoint
    r"(?!\s*\(\d{4}\))",  # not followed by year — those are TOA entries
    re.IGNORECASE,
)


def _check_citations(text: str, lines: list[str]) -> list[dict]:
    """Return a list of citation issues found in the text."""
    issues = []

    # 1. Case name italics check (best-effort in plain text)
    #    Flag all "X v. Y" patterns as needing italics check
    for m in CASE_CITATION_PATTERN.finditer(text):
        # Find line number
        start = m.start()
        line_no = text[:start].count("\n") + 1
        case_name = m.group(0).strip()
        if len(case_name) < 100:  # sanity length filter
            issues.append({
                "type": "italics",
                "line": line_no,
                "text": case_name,
                "message": f"Case name should be italicized: \"{case_name}\"",
                "severity": "warning",
            })

    # 2. Signal formatting issues
    for pat, msg in SIGNAL_ISSUES:
        if msg is None:
            continue
        for m in pat.finditer(text):
            line_no = text[:m.start()].count("\n") + 1
            issues.append({
                "type": "signal",
                "line": line_no,
                "text": m.group(0).strip(),
                "message": msg,
                "severity": "warning",
            })

    # 3. Missing pinpoint citations (flag reporter+page patterns without pinpoint)
    for m in MISSING_PINPOINT.finditer(text):
        line_no = text[:m.start()].count("\n") + 1
        issues.append({
            "type": "pinpoint",
            "line": line_no,
            "text": m.group(0).strip(),
            "message": f"Possible missing pinpoint citation after: \"{m.group(0).strip()}\"",
            "severity": "info",
        })

    # Deduplicate by line+type (keep first occurrence per line per type)
    seen: set[tuple] = set()
    deduped = []
    for issue in issues:
        key = (issue["line"], issue["type"], issue["text"][:40])
        if key not in seen:
            seen.add(key)
            deduped.append(issue)

    return deduped


# ── Word / page counting ──────────────────────────────────────────────────────

# Maps human-readable exclusion names (from court-rules.json) to section patterns
# used to locate and strip them from the text before counting.
_EXCLUSION_SECTION_MARKERS: dict[str, list[str]] = {
    "cover page": [
        r"(?:IN\s+THE\s+)?(?:UNITED\s+STATES|SUPREME\s+COURT)",
        r"No\.\s+\d{2}[-–]\d+",
        r"BRIEF\s+(?:OF|FOR)\s+",
    ],
    "disclosure statement": [
        r"CORPORATE\s+DISCLOSURE",
        r"DISCLOSURE\s+STATEMENT",
        r"RULE\s+26\.1",
    ],
    "table of contents": [r"TABLE\s+OF\s+CONTENTS"],
    "table of authorities": [r"TABLE\s+OF\s+AUTHORITIES"],
    "jurisdictional statement": [
        r"JURISDICTIONAL\s+STATEMENT",
        r"STATEMENT\s+OF\s+JURISDICTION",
    ],
    "glossary of abbreviations": [
        r"GLOSSARY\s+OF\s+ABBREVIATIONS?",
        r"LIST\s+OF\s+ABBREVIATIONS?",
    ],
    "statement of issues": [
        r"(?:STATEMENT\s+OF\s+)?ISSUES?\s+(?:PRESENTED|ON\s+APPEAL)",
        r"QUESTIONS?\s+PRESENTED",
    ],
    "questions presented": [r"QUESTIONS?\s+PRESENTED"],
    "opinions below": [r"OPINIONS?\s+BELOW", r"DECISION\s+BELOW"],
    "jurisdiction": [r"^JURISDICTION\s*$"],
    "constitutional and statutory provisions": [
        r"CONSTITUTIONAL\s+AND\s+STATUTORY\s+PROVISIONS?",
    ],
    "signature block": [r"Respectfully\s+submitted", r"s/\s*[A-Z]"],
    "certificate of compliance": [
        r"CERTIFICATE\s+OF\s+COMPLIANCE",
        r"certif(?:y|ies)\s+that\s+this\s+brief",
        r"word\s+count\s+(?:for\s+)?this\s+(?:brief|document)",
    ],
    "certificate of service": [
        r"CERTIFICATE\s+OF\s+SERVICE",
        r"I\s+(?:hereby\s+)?certify\s+that\s+(?:on|today|I)\s+(?:have\s+)?served",
    ],
}


def _strip_excluded_sections(text: str, exclusions: list[str]) -> tuple[str, list[str]]:
    """
    Attempt to strip exempt sections from text before word counting.

    Uses heuristic section-boundary detection: finds the start marker of an
    excluded section, then removes text from that marker to the next ALL-CAPS
    section heading (which likely begins a counted section).

    Returns (stripped_text, list_of_stripped_section_names).
    This is best-effort — plain-text extraction is imprecise.
    """
    stripped_names: list[str] = []
    remaining = text

    for excl in exclusions:
        markers = _EXCLUSION_SECTION_MARKERS.get(excl.lower(), [])
        if not markers:
            continue
        for marker_pat in markers:
            m_start = re.search(marker_pat, remaining, re.IGNORECASE | re.MULTILINE)
            if not m_start:
                continue
            # Find start of the line containing the marker
            line_start = remaining.rfind("\n", 0, m_start.start()) + 1
            # Find end: next ALL-CAPS heading at least 20 chars after start
            next_section = re.search(
                r"\n[A-Z][A-Z\s\-]{4,}\n",
                remaining[m_start.end() + 20:],
            )
            if next_section:
                end = m_start.end() + 20 + next_section.start()
            else:
                # No following heading — strip to end (last section)
                end = len(remaining)

            stripped_names.append(excl)
            remaining = remaining[:line_start] + remaining[end:]
            break  # only strip once per exclusion

    return remaining, stripped_names


def _count_words(text: str) -> int:
    """Count words in plain text."""
    return len(text.split())


def _count_words_excluding(
    text: str, exclusions: list[str]
) -> tuple[int, int, list[str]]:
    """
    Count words in text, optionally stripping exempt sections first.

    Returns (total_words, counted_words, list_of_stripped_sections).
    total_words is the raw count; counted_words excludes exempt sections.
    """
    total = _count_words(text)
    if not exclusions:
        return total, total, []
    stripped_text, stripped_names = _strip_excluded_sections(text, exclusions)
    counted = _count_words(stripped_text)
    return total, counted, stripped_names


def _estimate_pages(text: str, words_per_page: int = 250) -> int:
    """Rough page estimate based on word count (double-spaced, ~250 words/page)."""
    return max(1, round(_count_words(text) / words_per_page))


# ── Core checker ──────────────────────────────────────────────────────────────

def check_document(
    text: str,
    jurisdiction_key: str,
    filename: str = "document",
    rules_override: Optional[dict] = None,
) -> dict:
    """
    Run all checks against the rules for the given jurisdiction.

    Returns a structured result dict with:
      - jurisdiction info
      - word_count / page_estimate
      - checks: list of {name, status, detail} dicts
      - citation_issues: list of citation-level issues
      - summary: overall pass/fail + counts
    """
    all_rules = rules_override or _load_rules()

    # Normalize jurisdiction key
    jkey = jurisdiction_key.lower().strip()
    if jkey not in all_rules:
        # Fuzzy match
        candidates = [k for k in all_rules if jkey in k or k in jkey]
        if len(candidates) == 1:
            jkey = candidates[0]
        else:
            available = sorted(all_rules.keys())
            raise ValueError(
                f"Unknown jurisdiction '{jurisdiction_key}'. "
                f"Available: {', '.join(available)}"
            )

    rules = all_rules[jkey]
    lines = text.splitlines()
    exclusions: list[str] = rules.get("word_count_exclusions") or []
    total_word_count, counted_word_count, stripped_sections = _count_words_excluding(
        text, exclusions
    )
    # Use total for display; counted for limit comparison
    word_count = total_word_count
    page_estimate = _estimate_pages(text)

    checks: list[dict] = []

    # ── 1. Word limit ─────────────────────────────────────────────────────────
    if rules.get("word_limit"):
        limit = rules["word_limit"]
        # Compare against counted words (excludes exempt sections)
        effective = counted_word_count
        pct = round(effective / limit * 100)
        exclusion_note = ""
        if exclusions:
            if stripped_sections:
                exclusion_note = (
                    f" (Excluded from count: {', '.join(stripped_sections[:4])}"
                    + (f", +{len(stripped_sections) - 4} more" if len(stripped_sections) > 4 else "")
                    + f". Total document: {total_word_count:,} words.)"
                )
            else:
                exclusion_note = (
                    f" (Could not auto-detect exempt sections — counted all {total_word_count:,} words. "
                    f"FRAP 32(f) excludes: {', '.join(exclusions[:4])}{'...' if len(exclusions) > 4 else ''}.)"
                )
        if effective > limit:
            status = "fail"
            detail = (
                f"{effective:,} counted words — exceeds {limit:,} limit by "
                f"{effective - limit:,} words ({pct}%){exclusion_note}"
            )
        elif effective > limit * 0.95:
            status = "warn"
            detail = (
                f"{effective:,} / {limit:,} counted words ({pct}% of limit) "
                f"— within 5% of limit{exclusion_note}"
            )
        else:
            status = "pass"
            detail = f"{effective:,} / {limit:,} counted words ({pct}% of limit){exclusion_note}"
        checks.append({"name": "Word count", "status": status, "detail": detail})

    # ── 2. Page limit (estimated) ─────────────────────────────────────────────
    if rules.get("page_limit"):
        limit = rules["page_limit"]
        if page_estimate > limit:
            status = "fail"
            detail = f"~{page_estimate} pages estimated — exceeds {limit}-page limit (estimate only; verify in formatted document)"
        elif page_estimate > limit - 2:
            status = "warn"
            detail = f"~{page_estimate} pages estimated — close to {limit}-page limit (estimate only)"
        else:
            status = "pass"
            detail = f"~{page_estimate} pages estimated / {limit}-page limit (estimate; verify in formatted document)"
        checks.append({"name": "Page count (estimated)", "status": status, "detail": detail})

    # ── 3. Certificate of compliance ──────────────────────────────────────────
    if rules.get("certificate_required"):
        found = _section_present("Certificate of Compliance", text)
        checks.append({
            "name": "Certificate of compliance",
            "status": "pass" if found else "fail",
            "detail": "Present" if found else (
                "NOT FOUND — required by " + rules.get("source", "court rules") +
                ". Add a certificate stating word count and font compliance."
            ),
        })

    # ── 4. Cover page / caption ───────────────────────────────────────────────
    if rules.get("cover_page_required"):
        found = _section_present("Cover Page", text)
        checks.append({
            "name": "Cover page / caption",
            "status": "pass" if found else "warn",
            "detail": "Present" if found else
                "Not detected — may be missing or not recognizable from text extraction",
        })

    # ── 5. Table of contents ──────────────────────────────────────────────────
    if rules.get("table_of_contents_required"):
        found = _section_present("Table of Contents", text)
        checks.append({
            "name": "Table of contents",
            "status": "pass" if found else "fail",
            "detail": "Present" if found else "NOT FOUND — required",
        })

    # ── 6. Table of authorities ───────────────────────────────────────────────
    if rules.get("table_of_authorities_required"):
        found = _section_present("Table of Authorities", text)
        checks.append({
            "name": "Table of authorities",
            "status": "pass" if found else "fail",
            "detail": "Present" if found else "NOT FOUND — required",
        })

    # ── 7. Required sections ──────────────────────────────────────────────────
    required_sections = rules.get("required_sections", [])
    section_results = []
    for section in required_sections:
        # Skip structural checks already handled above
        if section in ("Table of Contents", "Table of Authorities", "Cover Page", "Certificate of Compliance", "Certificate of Service"):
            continue
        found = _section_present(section, text)
        section_results.append((section, found))

    missing_sections = [s for s, found in section_results if not found]
    present_sections = [s for s, found in section_results if found]

    if missing_sections:
        checks.append({
            "name": "Required sections",
            "status": "warn",
            "detail": f"Present: {', '.join(present_sections) or 'none detected'}. "
                      f"Missing or not detected: {', '.join(missing_sections)}",
        })
    else:
        checks.append({
            "name": "Required sections",
            "status": "pass",
            "detail": f"All detected: {', '.join(present_sections) or '(no specific sections required)'}",
        })

    # ── 8. Double-spacing indicator ───────────────────────────────────────────
    # Heuristic: check average blank lines between paragraphs in text file
    blank_line_ratio = text.count("\n\n") / max(text.count("\n"), 1)
    if blank_line_ratio < 0.1 and len(lines) > 20:
        spacing_status = "warn"
        spacing_detail = (
            "Text appears single-spaced or compact. Verify double-spacing in formatted document. "
            f"({rules.get('line_spacing', 'double-spaced')} required)"
        )
    else:
        spacing_status = "info"
        spacing_detail = f"Cannot verify from text file — {rules.get('line_spacing', 'double-spaced')} required; check formatted document"
    checks.append({"name": "Line spacing", "status": spacing_status, "detail": spacing_detail})

    # ── 9. Font check ─────────────────────────────────────────────────────────
    checks.append({
        "name": "Font / type size",
        "status": "info",
        "detail": f"Cannot verify from text file. Required: {rules.get('font', 'see court rules')}",
    })

    # ── 10. Margins check ─────────────────────────────────────────────────────
    checks.append({
        "name": "Margins",
        "status": "info",
        "detail": f"Cannot verify from text file. Required: {rules.get('margins', 'see court rules')}",
    })

    # ── 11. Certificate of service (if required) ──────────────────────────────
    # Certificate of service is required by most courts even if not in required_sections
    cert_service_found = _section_present("Certificate of Service", text)
    if "Certificate of Service" in required_sections:
        checks.append({
            "name": "Certificate of service",
            "status": "pass" if cert_service_found else "fail",
            "detail": "Present" if cert_service_found else "NOT FOUND — required",
        })
    else:
        checks.append({
            "name": "Certificate of service",
            "status": "pass" if cert_service_found else "info",
            "detail": "Present" if cert_service_found else
                "Not detected — may be required depending on filing method; verify with court rules",
        })

    # ── 12. Citation checks ───────────────────────────────────────────────────
    citation_issues = _check_citations(text, lines)
    italics_issues = [i for i in citation_issues if i["type"] == "italics"]
    signal_issues = [i for i in citation_issues if i["type"] == "signal"]
    pinpoint_issues = [i for i in citation_issues if i["type"] == "pinpoint"]

    if italics_issues or signal_issues:
        checks.append({
            "name": "Citation formatting",
            "status": "warn",
            "detail": (
                f"{len(italics_issues)} case name(s) flagged for italics check; "
                f"{len(signal_issues)} signal issue(s). See citation issues below."
            ),
        })
    else:
        checks.append({
            "name": "Citation formatting",
            "status": "pass",
            "detail": f"No obvious issues detected. {len(pinpoint_issues)} possible missing pinpoint(s) (info only).",
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    status_counts = {"pass": 0, "fail": 0, "warn": 0, "info": 0}
    for check in checks:
        status_counts[check["status"]] = status_counts.get(check["status"], 0) + 1

    if status_counts["fail"] > 0:
        overall = "FAIL"
        verdict = f"{status_counts['fail']} issue(s) must be fixed before filing"
    elif status_counts["warn"] > 0:
        overall = "REVIEW"
        verdict = f"{status_counts['warn']} item(s) need review"
    else:
        overall = "PASS"
        verdict = "No blocking issues found (verify font/spacing/margins in formatted document)"

    return {
        "filename": filename,
        "jurisdiction_key": jkey,
        "jurisdiction_name": rules["name"],
        "source": rules.get("source", ""),
        "notes": rules.get("notes", ""),
        "word_count": word_count,
        "word_count_for_limit": counted_word_count,
        "word_count_exclusions_applied": stripped_sections,
        "page_estimate": page_estimate,
        "checks": checks,
        "citation_issues": citation_issues[:50],  # cap for readability
        "summary": {
            "overall": overall,
            "verdict": verdict,
            **status_counts,
        },
    }


# ── Markdown formatter ────────────────────────────────────────────────────────

def _status_icon(status: str) -> str:
    return {"pass": "✓", "fail": "✗", "warn": "⚠", "info": "?"}.get(status, "?")


def format_report(result: dict) -> str:
    lines = []
    lines.append(f"## Filing Compliance Check — {result['jurisdiction_name']}")
    lines.append("")
    lines.append(f"**Document:** {result['filename']}")
    lines.append(f"**Jurisdiction:** {result['jurisdiction_name']} ({result['source']})")
    lines.append(f"**Word count:** {result['word_count']:,} | **Estimated pages:** ~{result['page_estimate']}")
    lines.append("")

    # Checks table
    for check in result["checks"]:
        icon = _status_icon(check["status"])
        lines.append(f"{icon} **{check['name']}:** {check['detail']}")

    # Citation issues
    citation_issues = result.get("citation_issues", [])
    italics = [i for i in citation_issues if i["type"] == "italics"]
    signals = [i for i in citation_issues if i["type"] == "signal"]
    pinpoints = [i for i in citation_issues if i["type"] == "pinpoint"]

    if italics or signals or pinpoints:
        lines.append("")
        lines.append("### Citation Issues")
        if italics:
            lines.append("")
            lines.append("**Case name italics** (verify formatting in final document):")
            for issue in italics[:10]:
                lines.append(f"  - Line {issue['line']}: {issue['text'][:80]}")
            if len(italics) > 10:
                lines.append(f"  - ...and {len(italics) - 10} more")
        if signals:
            lines.append("")
            lines.append("**Signal formatting:**")
            for issue in signals[:10]:
                lines.append(f"  - Line {issue['line']}: {issue['message']}")
        if pinpoints:
            lines.append("")
            lines.append("**Possible missing pinpoints** (info only — verify manually):")
            for issue in pinpoints[:5]:
                lines.append(f"  - Line {issue['line']}: `{issue['text'][:60]}`")

    # Summary
    lines.append("")
    summary = result["summary"]
    overall_icon = {"PASS": "✓", "FAIL": "✗", "REVIEW": "⚠"}.get(summary["overall"], "?")
    lines.append(f"---")
    lines.append(f"**Overall: {overall_icon} {summary['overall']}** — {summary['verdict']}")

    if result.get("notes"):
        lines.append("")
        lines.append(f"_Note: {result['notes']}_")

    lines.append("")
    lines.append(
        "_Results based on text extraction. Font size, margins, and line spacing "
        "cannot be verified from plain text — always check the formatted PDF before filing._"
    )

    return "\n".join(lines)


# ── Open WebUI Tool wrapper ───────────────────────────────────────────────────

class Tools:
    class Valves(BaseModel):
        rules_db_path: str = ""  # Optional override; auto-detected if empty
        max_text_length: int = 100000

    def __init__(self):
        self.valves = self.Valves()

    async def check_court_filing(
        self,
        text: str,
        jurisdiction: str,
        filename: Optional[str] = "document",
        __event_emitter__=None,
    ) -> str:
        """
        Check a legal document for compliance with court filing rules.

        Checks word/page limits, required sections (Table of Contents, Table of
        Authorities, Certificate of Compliance, etc.), and citation formatting.
        Returns a Markdown compliance report.

        :param text: The full text of the legal document to check.
        :param jurisdiction: Court jurisdiction key (e.g., '9th-circuit', 'cal-superior',
               'sdny', 'scotus', 'tx-appeals'). Use list_jurisdictions() to see all options.
        :param filename: Optional filename for display in the report.
        :return: Markdown compliance report.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Checking document against {jurisdiction} rules...",
                        "done": False,
                    },
                }
            )

        if not text or not text.strip():
            return "Error: No document text provided."

        if len(text) > self.valves.max_text_length:
            text = text[: self.valves.max_text_length]

        try:
            rules_override = None
            if self.valves.rules_db_path:
                p = Path(self.valves.rules_db_path)
                if p.exists():
                    with open(p) as fh:
                        raw = json.load(fh)
                    rules_override = {k: v for k, v in raw.items() if not k.startswith("_")}

            result = check_document(text, jurisdiction, filename or "document", rules_override)
            report = format_report(result)
        except ValueError as exc:
            report = f"Error: {exc}"
        except Exception as exc:  # noqa: BLE001
            report = f"Error running compliance check: {exc}"

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Compliance check complete.",
                        "done": True,
                    },
                }
            )

        return report

    async def list_jurisdictions(self, __event_emitter__=None) -> str:
        """
        List all supported court jurisdictions and their keys.

        :return: Markdown table of jurisdiction keys and names.
        """
        try:
            all_rules = _load_rules()
        except FileNotFoundError as exc:
            return f"Error: {exc}"

        lines = ["## Supported Jurisdictions", "", "| Key | Court | Word Limit | Page Limit | Source |", "| --- | ----- | ---------- | ---------- | ------ |"]
        for key, rules in sorted(all_rules.items()):
            wl = f"{rules['word_limit']:,}" if rules.get("word_limit") else "—"
            pl = str(rules["page_limit"]) if rules.get("page_limit") else "—"
            lines.append(f"| `{key}` | {rules['name']} | {wl} | {pl} | {rules.get('source', '')} |")
        return "\n".join(lines)

    async def get_jurisdiction_rules(
        self,
        jurisdiction: str,
        __event_emitter__=None,
    ) -> str:
        """
        Get the detailed filing rules for a specific jurisdiction.

        :param jurisdiction: Court jurisdiction key (e.g., '9th-circuit').
        :return: Formatted rules summary.
        """
        try:
            all_rules = _load_rules()
            jkey = jurisdiction.lower().strip()
            if jkey not in all_rules:
                candidates = [k for k in all_rules if jkey in k or k in jkey]
                if len(candidates) == 1:
                    jkey = candidates[0]
                else:
                    return f"Unknown jurisdiction '{jurisdiction}'. Use list_jurisdictions() to see options."
            rules = all_rules[jkey]
        except FileNotFoundError as exc:
            return f"Error: {exc}"

        lines = [
            f"## Filing Rules — {rules['name']}",
            "",
            f"**Source:** {rules.get('source', 'N/A')}",
            f"**Word limit:** {rules['word_limit']:,}" if rules.get('word_limit') else "**Word limit:** None",
            f"**Page limit:** {rules['page_limit']}" if rules.get('page_limit') else "**Page limit:** None",
            f"**Font:** {rules.get('font', 'N/A')}",
            f"**Margins:** {rules.get('margins', 'N/A')}",
            f"**Line spacing:** {rules.get('line_spacing', 'N/A')}",
            f"**Footnotes:** {rules.get('footnote_rules', 'N/A')}",
            f"**Certificate required:** {'Yes' if rules.get('certificate_required') else 'No'}",
            f"**Cover page required:** {'Yes' if rules.get('cover_page_required') else 'No'}",
            f"**Table of Contents required:** {'Yes' if rules.get('table_of_contents_required') else 'No'}",
            f"**Table of Authorities required:** {'Yes' if rules.get('table_of_authorities_required') else 'No'}",
        ]
        if rules.get("required_sections"):
            lines.append("")
            lines.append("**Required sections:**")
            for s in rules["required_sections"]:
                lines.append(f"  - {s}")
        if rules.get("notes"):
            lines.append("")
            lines.append(f"_Note: {rules['notes']}_")

        return "\n".join(lines)

    def validate_output(self, report: str) -> dict:
        """
        Validate that a compliance report conforms to the expected schema.

        Checks that the report has a recognized header, an Overall verdict,
        and at least one check result. Returns {"valid": bool, "errors": list[str]}.

        Useful for pipeline integration — catches silent failures where the
        tool returns a partial or malformed report due to truncation or errors.

        :param report: Markdown string returned by check_court_filing().
        :return: {"valid": bool, "errors": list[str]}
        """
        errors: list[str] = []

        if not report or not report.strip():
            errors.append("Report is empty")
            return {"valid": False, "errors": errors}

        if report.startswith("Error:") or report.startswith("Error running"):
            errors.append(f"Report contains an error: {report[:200]}")
            return {"valid": False, "errors": errors}

        # Must start with the expected header
        if not report.startswith("## Filing Compliance Check"):
            errors.append(
                "Missing expected header '## Filing Compliance Check — <jurisdiction>'. "
                "Report may be from a different tool or malformed."
            )

        # Must have an Overall verdict
        verdict_markers = ["**Overall:", "**Overall: ✓", "**Overall: ✗", "**Overall: ⚠"]
        if not any(m in report for m in verdict_markers):
            errors.append(
                "Missing Overall verdict line ('**Overall: PASS/FAIL/REVIEW**'). "
                "Report may be truncated."
            )

        # Must have at least one check result (✓, ✗, or ⚠)
        import re as _re
        check_lines = _re.findall(r'^[✓✗⚠?] \*\*', report, _re.MULTILINE)
        if not check_lines:
            errors.append(
                "No check result lines found. Expected lines starting with ✓, ✗, or ⚠. "
                "Report may be empty or truncated."
            )

        # Word count should be present
        if "**Word count:**" not in report:
            errors.append(
                "Missing '**Word count:**' line. Report may be truncated before check results."
            )

        return {"valid": len(errors) == 0, "errors": errors}


# ── CLI entry point ───────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(
        prog="court-rules-checker",
        description="Check a legal document against court filing rules.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/court-rules-checker.py --jurisdiction 9th-circuit brief.txt
  python3 tools/court-rules-checker.py --jurisdiction cal-superior motion.txt
  python3 tools/court-rules-checker.py --jurisdiction sdny --json memo.txt
  python3 tools/court-rules-checker.py --list-jurisdictions
  cat brief.txt | python3 tools/court-rules-checker.py --jurisdiction scotus

Via legal-check:
  legal-check -m rules --jurisdiction 9th-circuit brief.txt
        """,
    )
    parser.add_argument("file", nargs="?", help="Document to check (or stdin if omitted)")
    parser.add_argument("--jurisdiction", "-j", help="Jurisdiction key (e.g., 9th-circuit, cal-superior)")
    parser.add_argument("--list-jurisdictions", "-l", action="store_true", help="List all supported jurisdictions")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown")
    parser.add_argument("--rules-db", help="Path to court-rules.json (auto-detected by default)")
    args = parser.parse_args()

    # List mode
    if args.list_jurisdictions:
        try:
            all_rules = _load_rules()
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"{'Key':<22} {'Court':<50} {'Word Limit':>12} {'Page Limit':>12}")
        print("-" * 100)
        for key, rules in sorted(all_rules.items()):
            wl = f"{rules['word_limit']:,}" if rules.get("word_limit") else "—"
            pl = str(rules["page_limit"]) if rules.get("page_limit") else "—"
            print(f"{key:<22} {rules['name']:<50} {wl:>12} {pl:>12}")
        sys.exit(0)

    if not args.jurisdiction:
        parser.error("--jurisdiction is required (use --list-jurisdictions to see options)")

    # Read input
    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        # Handle PDF
        if p.suffix.lower() == ".pdf":
            import subprocess
            try:
                result_proc = subprocess.run(
                    ["pdftotext", str(p), "-"],
                    capture_output=True, text=True, check=True
                )
                text = result_proc.stdout
            except FileNotFoundError:
                print("Error: pdftotext not found. Install poppler-utils.", file=sys.stderr)
                sys.exit(1)
            except subprocess.CalledProcessError as exc:
                print(f"Error extracting PDF: {exc}", file=sys.stderr)
                sys.exit(1)
        else:
            text = p.read_text(encoding="utf-8", errors="replace")
        filename = p.name
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
        filename = "stdin"
    else:
        parser.error("No input provided. Specify a file or pipe text via stdin.")

    # Load optional rules override
    rules_override = None
    if args.rules_db:
        rp = Path(args.rules_db)
        if not rp.exists():
            print(f"Error: Rules DB not found: {args.rules_db}", file=sys.stderr)
            sys.exit(1)
        with open(rp) as fh:
            raw = json.load(fh)
        rules_override = {k: v for k, v in raw.items() if not k.startswith("_")}

    try:
        result = check_document(text, args.jurisdiction, filename, rules_override)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result))

    # Exit with non-zero if FAIL
    if result["summary"]["overall"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    _cli()
