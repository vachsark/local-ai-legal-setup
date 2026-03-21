#!/usr/bin/env python3
"""
title: Batch Contract Scanner
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Scan a folder of contracts and produce a consolidated risk report.
             Supports risk scanning, privilege review, and key terms extraction.

CLI usage:
  python3 tools/batch-scanner.py contracts/ --output risk-report.md
  python3 tools/batch-scanner.py contracts/ --focus "indemnification,termination"
  python3 tools/batch-scanner.py discovery/ --mode privilege
  python3 tools/batch-scanner.py contracts/ --mode terms --format csv
"""

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional


# ── Content-hash disk cache ────────────────────────────────────────────────────
# Each document gets a SHA-256 hash of its raw bytes. Results are cached in a
# JSON file alongside the output so re-runs only process changed/new documents.
# This is more reliable than file-list based --resume: if you edit a contract
# the hash changes, forcing reprocessing even if the filename is unchanged.

def _doc_hash(path: Path) -> str:
    """SHA-256 of raw file bytes, hex-encoded (first 16 chars for brevity)."""
    try:
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        return h[:16]
    except Exception:
        return ""


def _cache_path(output_path: Optional[Path]) -> Optional[Path]:
    """Derive cache file path from output path (.cache.json suffix)."""
    if not output_path:
        return None
    return output_path.with_suffix(".cache.json")


def _dir_cache_path(directory: Path) -> Path:
    """Canonical per-directory cache — always written on every scan.

    Stored as {directory}/.legal-scan-cache.json.  Query mode reads from
    here so it can find pre-analyzed results without an --output path.
    """
    return directory / ".legal-scan-cache.json"


def load_hash_cache(cache_file: Optional[Path]) -> dict[str, dict]:
    """Load {doc_hash: result_dict} from the cache file."""
    if not cache_file or not cache_file.exists():
        return {}
    try:
        entries = json.loads(cache_file.read_text())
        return {e["_hash"]: e for e in entries if "_hash" in e}
    except Exception:
        return {}


def save_hash_cache(cache_file: Optional[Path], results: list[dict]) -> None:
    """Persist results (those that have a _hash field) to the cache file."""
    if not cache_file:
        return
    try:
        cache_file.write_text(json.dumps(results, indent=2))
    except Exception:
        pass


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text_from_path(path: Path) -> tuple[str, Optional[str]]:
    """Return (text, warning). Warning is set if extraction was degraded."""
    ext = path.suffix.lower()

    if ext == ".pdf":
        try:
            result = subprocess.run(
                ["pdftotext", str(path), "-"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout, None
            return "", f"pdftotext failed (exit {result.returncode}): {result.stderr[:100]}"
        except FileNotFoundError:
            return "", (
                "pdftotext not found — install poppler-utils "
                "(Arch: sudo pacman -S poppler | apt: sudo apt install poppler-utils | brew install poppler)"
            )
        except subprocess.TimeoutExpired:
            return "", "pdftotext timed out"

    elif ext == ".docx":
        try:
            from docx import Document  # type: ignore
            doc = Document(str(path))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text, None
        except ImportError:
            return "", "python-docx not installed (pip install python-docx) — skipping DOCX"
        except Exception as e:
            return "", f"docx read error: {e}"

    else:  # .txt and everything else
        try:
            return path.read_text(errors="replace"), None
        except Exception as e:
            return "", f"read error: {e}"


def glob_documents(directory: Path) -> list[Path]:
    """Find all .txt, .pdf, .docx files under directory."""
    patterns = ["**/*.txt", "**/*.pdf", "**/*.docx"]
    docs = []
    seen = set()
    for pattern in patterns:
        for p in sorted(directory.glob(pattern)):
            if p.is_file() and str(p) not in seen:
                docs.append(p)
                seen.add(str(p))
    return sorted(docs)


# ── Risk signal extraction (shared with document-summarizer.py) ───────────────

RISK_PATTERNS = [
    # (regex, label, severity, detail_hint)
    (r"\bindemnif(?:y|ication|ied)\b(?![^.]{0,60}(?:cap|limit|capped|exceed|maximum|\$[\d,]+))",
     "Indemnification without apparent cap", "HIGH",
     "Indemnification clause present but no cap/limit detected nearby"),
    (r"\bindemnif(?:y|ication|ied)\b",
     "Indemnification clause", "MEDIUM",
     "Indemnification present — verify if a cap applies"),
    (r"\bauto(?:matic(?:ally)?)?[\s-]renew",
     "Auto-renewal provision", "HIGH",
     "Contract auto-renews — check notice period to cancel"),
    (r"\bsolely?\s+(?:at\s+)?(?:its|(?:the\s+)?(?:company|vendor|licensor)[\'\s]*s)\s+(?:sole\s+)?(?:and\s+absolute\s+)?discretion\b"
     r"|\bsole\s+(?:and\s+absolute\s+)?discretion\b",
     "Unilateral/sole discretion clause", "HIGH",
     "One party may act without the other's consent"),
    (r"\bterminate\b.{0,60}\bwithout cause\b|\bat will\b.{0,40}\bterminate\b"
     r"|\bterminate.{0,60}for\s+(?:any|no)\s+reason\b",
     "Unilateral termination (without cause)", "HIGH",
     "Either party can terminate without cause — check for asymmetry"),
    (r"\bbinding arbitration\b|\bmandatory arbitration\b",
     "Mandatory arbitration", "MEDIUM",
     "Disputes must go to arbitration — waives right to jury trial in court"),
    (r"\bwaiver of (?:jury|class action|class)\b|\bjury trial waiver\b|\bwaives.{0,20}jury\b",
     "Jury / class action waiver", "HIGH",
     "Explicit waiver of jury trial or class action rights"),
    (r"\bnon-compete\b|\bnoncompete\b|\bnon compete\b",
     "Non-compete clause", "HIGH",
     "Restricts future business activity — verify scope and duration"),
    (r"\bnon-solicit(?:ation)?\b|\bnonsolicit(?:ation)?\b",
     "Non-solicitation clause", "MEDIUM",
     "Restricts hiring or poaching of employees/clients"),
    (r"\bunlimited liability\b|\bno limitation\b.{0,30}\bliability\b"
     r"|\bliability is not limited\b",
     "Unlimited liability exposure", "HIGH",
     "No cap on damages — significant financial risk"),
    (r"\bassignment\b.{0,60}(?:without consent|without.{0,20}approval)",
     "Assignment without consent", "HIGH",
     "Contract can be assigned to third parties without approval"),
    (r"\bassignment\b",
     "Assignment provision", "LOW",
     "Assignment clause present — check consent requirements"),
    (r"\bmost[- ]favored[- ]nation\b|\bMFN\b",
     "Most-favored-nation (MFN) clause", "MEDIUM",
     "Price or terms parity obligation — may restrict flexibility"),
    (r"\bin perpetuity\b|\bperpetual\b",
     "Perpetual obligation or grant", "HIGH",
     "Obligation or license has no end date"),
    (r"\birrevocable\b",
     "Irrevocable right or waiver", "MEDIUM",
     "Cannot be reversed — verify what is being made irrevocable"),
    (r"\bforce majeure\b",
     "Force majeure clause", "LOW",
     "Excuses performance for unforeseeable events — check breadth"),
    (r"\bconfidential(?:ity)?\b",
     "Confidentiality obligation", "LOW",
     "Confidentiality obligations present — check duration and scope"),
    (r"\bgoverning law\b|\bchoice of law\b",
     "Choice of law / governing law", "LOW",
     "Which jurisdiction's law controls — may require local counsel"),
    (r"\bliquidated damages\b",
     "Liquidated damages clause", "MEDIUM",
     "Pre-set damages amount — may be one-sided"),
    (r"\brepresent(?:ation)?s?\s+and\s+warrant(?:ies|y)\b",
     "Representations and warranties", "LOW",
     "Reps & warranties present — check survival and remedy provisions"),
    (r"\bsurvive(?:s)?\s+termination\b|\bsurvival\b",
     "Survival clause", "LOW",
     "Some obligations survive contract end — check which ones"),
    (r"(?:5|six|seven|eight|nine|ten|\d+)\s+year(?:s)?\s+(?:confidentiality|survival)"
     r"|confidentiality.{0,40}(?:5|six|seven|eight|nine|ten|\d+)\s+year",
     "Long confidentiality survival period (5+ years)", "MEDIUM",
     "Confidentiality obligations extend years beyond contract end"),
    (r"\bexclusive\b",
     "Exclusivity provision", "MEDIUM",
     "Exclusive relationship — may lock out other vendors/clients"),
    (r"\bcure period\b|\bnotice and cure\b|\bopportunity to cure\b",
     "Cure period in termination", "LOW",
     "Breaching party has time to fix before termination — check length"),
    (r"\bfee(?:s)?\s+increase\b|\bprice\s+increas(?:e|ing)\b|\bescalat(?:e|ion)\b",
     "Fee escalation provision", "MEDIUM",
     "Fees can increase — check cap and notice period"),
    # Ken Adams / MSCD patterns (from research Agent 6)
    (r"\bbest efforts?\b",
     "Best efforts standard", "MEDIUM",
     "Ken Adams (MSCD): 'best efforts' is ambiguous — courts split on whether it differs from 'reasonable efforts'"),
    (r"\bcommercially reasonable efforts?\b",
     "Commercially reasonable efforts standard", "LOW",
     "Common standard — but courts interpret it differently; consider defining in contract"),
    (r"\bincluding(?:\s+without\s+limitation)?\b",
     "Non-exhaustive 'including' (ejusdem generis risk)", "LOW",
     "Adams: 'including' without 'but not limited to' may invite ejusdem generis narrowing; use 'including but not limited to' or tabulate"),
    (r"\bshall\b.{0,80}\bwill\b|\bwill\b.{0,80}\bshall\b",
     "Mixed 'shall'/'will' usage", "LOW",
     "Adams (MSCD): mixing shall/will in same document creates ambiguity about obligation vs. futurity; pick one and be consistent"),
    (r"\bSection\s+\d+(?:\.\d+)*\b.{0,30}(?:above|below|hereof|herein)\b",
     "Cross-reference (potential rot risk)", "LOW",
     "Adams: cross-references become stale when sections are renumbered — verify all referenced sections exist"),
    # O'Connor v. Oakhurst Dairy — serial/Oxford comma ambiguity
    (r"(?:[A-Z][a-z]+(?:ing|ation|ment)),\s+(?:[A-Z][a-z]+(?:ing|ation|ment)),\s+(?:and|or)\s+[A-Z][a-z]+",
     "Potential serial comma ambiguity (O'Connor risk)", "MEDIUM",
     "O'Connor v. Oakhurst Dairy ($5M): missing Oxford comma in a list caused $5M wage claim; verify lists are unambiguous"),
    # Boilerplate gaps from research
    (r"\bchange\s+of\s+control\b|\bchange-of-control\b",
     "Change of control provision", "MEDIUM",
     "Triggers on acquisition — check if it accelerates obligations or permits termination"),
    (r"\bintellectual\s+property\b|\bwork\s+for\s+hire\b|\bwork-for-hire\b",
     "IP ownership / work-for-hire", "MEDIUM",
     "Verify IP ownership is clearly assigned; work-for-hire must meet statutory requirements"),
    (r"\blimitation\s+of\s+liability\b|\bliability\s+cap\b|\bliability\s+limited\b",
     "Liability cap / limitation of liability clause", "LOW",
     "Liability ceiling present — check amount, exclusions (fraud, willful misconduct), and mutual vs. one-sided"),
    (r"\bindirect\b.{0,40}\bdamages?\b|\bconsequential\b.{0,40}\bdamages?\b|\bspecial\s+damages?\b",
     "Consequential/indirect damages exclusion or waiver", "HIGH",
     "Waiving consequential damages can eliminate most real-world losses — verify scope and exceptions"),
]

PRIVILEGE_PATTERNS = [
    (r"\battorney[\s-]client\b", "Attorney-client privilege marker"),
    (r"\bwork product\b|\battorney work product\b", "Work product doctrine marker"),
    (r"\bprivileged\b.{0,20}(?:and\s+)?confidential\b"
     r"|\bconfidential\b.{0,20}\bprivileged\b",
     "Privileged & confidential header"),
    (r"\blegal advice\b|\bprovide(?:d)? counsel\b|\bprovide(?:d)? legal\b",
     "Legal advice reference"),
    (r"\bcounsel\b.{0,40}(?:advice|opinion|letter|memo|memorandum)\b",
     "Counsel advice/opinion reference"),
    (r"\bdo not disclose\b|\bnot for distribution\b|\bprotected from disclosure\b",
     "Non-disclosure instruction"),
    (r"(?:to|from):\s*.{0,30}(?:esq|j\.d\.|attorney|counsel|law firm)",
     "Communication with attorney"),
    # Additional markers per research findings (Agent 7: Email/Letter Legal Writing)
    (r"\bprepared\s+(?:at\s+the\s+)?(?:request|direction)\s+of\s+(?:counsel|attorney|legal)\b"
     r"|\bat\s+(?:the\s+)?(?:direction|request)\s+of\s+(?:our\s+)?(?:legal|counsel|attorney)\b",
     "Prepared at direction of counsel"),
    (r"\blitigation\s+hold\b|\blegal\s+hold\b|\bpreservation\s+notice\b",
     "Litigation hold / preservation notice"),
    (r"\bin[- ]house\s+counsel\b|\bgeneral\s+counsel\b|\bdeputy\s+general\s+counsel\b",
     "In-house/general counsel reference"),
    (r"\bsubject\s+to\s+(?:attorney[- ]client\s+)?privilege\b"
     r"|\bprotected\s+by\s+(?:attorney[- ]client\s+)?privilege\b",
     "Explicit privilege assertion"),
    (r"\bwithout\s+prejudice\b",
     "Without prejudice marker (settlement/negotiation protection)"),
]

TERMS_PATTERNS = [
    # Financial
    (r"(?:USD\s*)?\$\s*[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B|K))?|"
     r"(?:USD|US\$)\s*[\d,]+(?:\.\d{2})?", "financial"),
    (r"\b(\d+(?:\.\d+)?)\s*%", "percentage"),
    # Dates
    (r"(?:January|February|March|April|May|June|July|August|September|"
     r"October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}", "date"),
    (r"\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b", "date"),
    # Parties (org names)
    (r"([A-Z][A-Za-z0-9 &\',\.-]{1,60}"
     r"(?:Inc|LLC|LLP|Corp|Ltd|Co|Company|Corporation|"
     r"Association|Associates|Group|Partners|Foundation|Authority|Solutions|Services|Analytics)"
     r"\.?)", "party"),
]


def extract_risk_signals(text: str, focus_terms: Optional[list[str]] = None) -> list[dict]:
    """Return list of risk findings. If focus_terms set, bias towards those patterns."""
    text_lower = text.lower()
    found = []
    seen_labels = set()

    for pattern, label, severity, hint in RISK_PATTERNS:
        # If focus terms given, skip signals not matching any focus term
        if focus_terms:
            match_focus = any(f.lower() in label.lower() or f.lower() in hint.lower()
                              for f in focus_terms)
            if not match_focus:
                # Still include HIGH severity even if not focused
                if severity != "HIGH":
                    continue

        if label in seen_labels:
            continue

        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 120)
            excerpt = text[start:end].strip().replace("\n", " ")
            found.append({
                "label": label,
                "severity": severity,
                "hint": hint,
                "excerpt": excerpt,
            })
            seen_labels.add(label)

    return found


def score_risk(signals: list[dict]) -> str:
    """Convert signal list to HIGH / MEDIUM / LOW."""
    if not signals:
        return "LOW"
    severities = [s["severity"] for s in signals]
    if "HIGH" in severities:
        return "HIGH"
    if "MEDIUM" in severities:
        return "MEDIUM"
    return "LOW"


def extract_privilege_signals(text: str) -> tuple[str, list[dict]]:
    """Return (classification, signals) where classification is LIKELY/POSSIBLY/NOT PRIVILEGED."""
    text_lower = text.lower()
    found = []

    for pattern, label in PRIVILEGE_PATTERNS:
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 100)
            excerpt = text[start:end].strip().replace("\n", " ")
            found.append({"label": label, "excerpt": excerpt})

    if len(found) >= 2:
        classification = "LIKELY PRIVILEGED"
    elif len(found) == 1:
        classification = "POSSIBLY PRIVILEGED"
    else:
        classification = "NOT PRIVILEGED"

    return classification, found


def extract_parties(text: str) -> list[dict]:
    """Quick party extraction — same logic as document-summarizer.py."""
    parties = []
    seen = set()
    skip_labels = {
        "agreement", "effective date", "term", "renewal term", "initial term",
        "services", "platform", "client data", "confidential information",
        "work product", "party", "parties",
    }
    for m in re.finditer(
        r'([A-Z][A-Za-z0-9 &\',\.-]{1,60}'
        r'(?:Inc|LLC|LLP|Corp|Ltd|Co|Company|Corporation|'
        r'Association|Associates|Group|Partners|Foundation|Authority|Solutions|Services|Analytics)'
        r'\.?)'
        r'[,\s]*\((?:the\s+)?["\u201c\u2018]([A-Z][A-Za-z ]{1,30})["\u201d\u2019]\)',
        text,
    ):
        full_name = m.group(1).strip().rstrip(", ")
        label = m.group(2).strip()
        key = label.lower()
        if key in skip_labels:
            continue
        if key not in seen and len(full_name) > 3:
            parties.append({"name": full_name, "role": label})
            seen.add(key)
    return parties[:6]


def extract_key_terms(text: str) -> dict:
    """Extract financial amounts, dates, parties for terms mode."""
    results: dict[str, list] = {"financial": [], "percentage": [], "date": [], "party": []}
    seen: dict[str, set] = {k: set() for k in results}

    # Financial
    for m in re.finditer(
        r"(?:USD\s*)?\$\s*[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B|K))?|"
        r"(?:USD|US\$)\s*[\d,]+(?:\.\d{2})?", text
    ):
        val = m.group(0).strip()
        if val not in seen["financial"]:
            start = max(0, m.start() - 70)
            end = min(len(text), m.end() + 70)
            ctx = text[start:end].strip().replace("\n", " ")
            results["financial"].append({"value": val, "context": ctx})
            seen["financial"].add(val)

    # Percentages
    for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*%\b", text):
        val = m.group(0).strip()
        if val not in seen["percentage"]:
            start = max(0, m.start() - 70)
            end = min(len(text), m.end() + 70)
            ctx = text[start:end].strip().replace("\n", " ")
            results["percentage"].append({"value": val, "context": ctx})
            seen["percentage"].add(val)

    # Dates
    for m in re.finditer(
        r"(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|"
        r"\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b",
        text,
    ):
        val = m.group(0).strip()
        if val not in seen["date"]:
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            ctx = text[start:end].strip().replace("\n", " ")
            results["date"].append({"value": val, "context": ctx})
            seen["date"].add(val)

    # Parties
    results["party"] = extract_parties(text)

    return results


# ── Cross-document query mode ─────────────────────────────────────────────────
#
# "Find every contract with uncapped indemnification" across an entire library.
# Searches cached results (signals + excerpts) for the query terms.  If the
# directory has no cache yet, runs a quick risk scan first to build it.


def _query_terms_from_string(query: str) -> list[str]:
    """Split a free-text query into individual search tokens (≥3 chars)."""
    # Keep multi-word phrases as single tokens after splitting on commas/semicolons
    parts = re.split(r"[,;]+", query)
    tokens = []
    for part in parts:
        part = part.strip()
        if part:
            tokens.append(part.lower())
    # If no comma/semicolon split occurred, also split on spaces for keyword matching
    if len(tokens) == 1:
        words = [w.lower() for w in query.split() if len(w) >= 3]
        if words:
            tokens.extend(words)
    return list(dict.fromkeys(tokens))  # deduplicate, preserve order


def _score_result_against_query(result: dict, query_tokens: list[str]) -> tuple[int, list[str]]:
    """Return (score, matched_excerpts) for how well a cached result matches the query.

    Scoring:
      +3  for each token found in a signal label
      +2  for each token found in a signal hint
      +1  for each token found in a signal excerpt
    Returns the top matching excerpts (deduplicated, up to 5).
    """
    score = 0
    matched_excerpts: list[str] = []
    seen_excerpts: set[str] = set()

    signals = result.get("signals", [])
    for sig in signals:
        label = sig.get("label", "").lower()
        hint = sig.get("hint", "").lower()
        excerpt = sig.get("excerpt", "")
        excerpt_lower = excerpt.lower()

        label_hit = any(tok in label for tok in query_tokens)
        hint_hit = any(tok in hint for tok in query_tokens)
        excerpt_hit = any(tok in excerpt_lower for tok in query_tokens)

        if label_hit:
            score += 3
        if hint_hit:
            score += 2
        if (label_hit or hint_hit or excerpt_hit) and excerpt:
            key = excerpt[:80]
            if key not in seen_excerpts:
                matched_excerpts.append(excerpt)
                seen_excerpts.add(key)
        elif excerpt_hit and excerpt:
            score += 1
            key = excerpt[:80]
            if key not in seen_excerpts:
                matched_excerpts.append(excerpt)
                seen_excerpts.add(key)

    return score, matched_excerpts[:5]


def query_documents(
    directory: Path,
    query: str,
    output_path: Optional[Path] = None,
) -> str:
    """Cross-document query: find every cached contract matching the query.

    Steps:
      1. Load the canonical directory cache.
      2. If no cache exists, run a full risk scan first to build it.
      3. Score every cached result against the query tokens.
      4. Return a ranked report of matching documents with evidence excerpts.
    """
    dir_cache = _dir_cache_path(directory)
    query_tokens = _query_terms_from_string(query)

    # ── Step 1: Load or build cache ─────────────────────────────────────────
    if not dir_cache.exists():
        print(
            f"  No cache found for {directory}. Running quick risk scan to build it...",
            file=sys.stderr,
        )
        # Run a full risk scan — this writes to the dir cache as a side effect
        process_batch(
            directory=directory,
            mode="risk",
            focus_terms=None,
            output_path=output_path,
            fmt="markdown",
            resume=False,
        )
        if not dir_cache.exists():
            return (
                f"# Query: {query}\n\n"
                "No documents found or cache could not be built. "
                f"Ensure {directory} contains .txt, .pdf, or .docx files."
            )

    cached_results = list(load_hash_cache(dir_cache).values())
    if not cached_results:
        return f"# Query: {query}\n\nCache is empty. Re-run a scan first."

    # ── Step 2: Score every document against the query ──────────────────────
    scored: list[tuple[int, list[str], dict]] = []
    for result in cached_results:
        if result.get("skipped"):
            continue
        score, excerpts = _score_result_against_query(result, query_tokens)
        if score > 0:
            scored.append((score, excerpts, result))

    # Sort highest score first
    scored.sort(key=lambda x: x[0], reverse=True)

    # ── Step 3: Format report ────────────────────────────────────────────────
    today = date.today().isoformat()
    total_scanned = len(cached_results)
    total_matches = len(scored)

    lines = [
        "# Cross-Document Query Report",
        f"Query: **{query}**",
        f"Generated: {today}",
        f"Documents searched: {total_scanned}",
        f"Documents matching: {total_matches}",
        "",
    ]

    if not scored:
        lines += [
            f"No documents matched the query: **{query}**",
            "",
            "Suggestions:",
            "- Check spelling or try broader terms",
            "- Run `--mode risk` scan first if documents haven't been analyzed yet",
            "- Try `--batch-focus` with specific risk terms for more targeted scanning",
        ]
        return "\n".join(lines)

    lines += [
        "## Matching Documents",
        "",
        "| Document | Risk Level | Match Score | Top Issue |",
        "|----------|-----------|-------------|-----------|",
    ]
    for score, excerpts, result in scored:
        doc = result["doc"]
        risk = result.get("risk_level", "—")
        icon = RISK_EMOJI.get(risk, "")
        sigs = result.get("signals", [])
        # Find the top signal that matched
        top_sig = ""
        for sig in sigs:
            label = sig.get("label", "").lower()
            hint = sig.get("hint", "").lower()
            if any(tok in label or tok in hint for tok in query_tokens):
                top_sig = sig.get("label", "")
                break
        if not top_sig and sigs:
            top_sig = sigs[0].get("label", "")
        lines.append(f"| {doc} | {icon} {risk} | {score} | {top_sig} |")

    lines += ["", "## Evidence by Document", ""]

    for score, excerpts, result in scored:
        doc = result["doc"]
        risk = result.get("risk_level", "—")
        icon = RISK_EMOJI.get(risk, "")
        parties = result.get("parties", [])
        party_str = " ↔ ".join(
            f"{p['name']} ({p['role']})" for p in parties
        ) if parties else "Not identified"

        lines += [
            f"### {doc}",
            f"**Risk Level**: {icon} {risk}  |  **Match Score**: {score}",
            f"**Parties**: {party_str}",
            "",
            f"**Matching signals for** *{query}*:",
        ]

        # List all signals that matched the query
        sigs = result.get("signals", [])
        matched_sigs = [
            s for s in sigs
            if any(tok in s.get("label", "").lower() or tok in s.get("hint", "").lower()
                   for tok in query_tokens)
        ]
        if not matched_sigs:
            matched_sigs = sigs  # fall back to all signals if excerpt-only match
        for sig in matched_sigs[:5]:
            sev_icon = RISK_EMOJI.get(sig.get("severity", ""), "")
            lines.append(f"- {sev_icon} **{sig['label']}** — {sig.get('hint', '')}")
            exc = sig.get("excerpt", "")
            if exc:
                lines.append(f"  > *\"{exc[:250].replace(chr(10), ' ')}\"*")

        lines.append("")

    return "\n".join(lines)


# ── Report formatters ──────────────────────────────────────────────────────────

RISK_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
PRIV_EMOJI = {"LIKELY PRIVILEGED": "⚠️ ", "POSSIBLY PRIVILEGED": "ℹ️ ", "NOT PRIVILEGED": "✅"}


def format_risk_report(results: list[dict], focus_terms: Optional[list[str]]) -> str:
    today = date.today().isoformat()
    total = len(results)
    high_count = sum(1 for r in results if r.get("risk_level") == "HIGH")
    medium_count = sum(1 for r in results if r.get("risk_level") == "MEDIUM")
    low_count = sum(1 for r in results if r.get("risk_level") == "LOW")
    skipped = sum(1 for r in results if r.get("skipped"))

    lines = [
        "# Contract Risk Report",
        f"Generated: {today}",
        f"Documents scanned: {total - skipped}",
    ]
    if skipped:
        lines.append(f"Documents skipped (unreadable): {skipped}")
    if focus_terms:
        lines.append(f"Focus terms: {', '.join(focus_terms)}")
    lines += [
        f"High-risk findings: {high_count}",
        f"Medium-risk findings: {medium_count}",
        f"Low-risk findings: {low_count}",
        "",
    ]

    # Summary table
    lines += [
        "## Summary Table",
        "",
        "| Document | Risk Level | Key Issues |",
        "|----------|-----------|------------|",
    ]
    for r in results:
        doc_name = r["doc"]
        if r.get("skipped"):
            lines.append(f"| {doc_name} | SKIPPED | {r.get('error', 'unknown error')} |")
            continue
        risk = r["risk_level"]
        icon = RISK_EMOJI.get(risk, "")
        signals = r.get("signals", [])
        # Show top 2 HIGH signals, else first 2
        high_signals = [s for s in signals if s["severity"] == "HIGH"]
        top = (high_signals[:2] if high_signals else signals[:2])
        key_issues = "; ".join(s["label"] for s in top) if top else "No significant risks"
        lines.append(f"| {doc_name} | {icon} {risk} | {key_issues} |")

    lines.append("")

    # Detailed findings
    lines.append("## Detailed Findings")
    lines.append("")

    for r in results:
        if r.get("skipped"):
            lines += [
                f"### {r['doc']}",
                f"**Status**: SKIPPED — {r.get('error', 'unknown error')}",
                "",
            ]
            continue

        risk = r["risk_level"]
        icon = RISK_EMOJI.get(risk, "")
        parties = r.get("parties", [])
        party_str = " ↔ ".join(
            f"{p['name']} ({p['role']})" for p in parties
        ) if parties else "Not identified"

        lines += [
            f"### {r['doc']}",
            f"**Risk Level**: {icon} {risk}",
            f"**Parties**: {party_str}",
        ]

        if r.get("warning"):
            lines.append(f"**Warning**: {r['warning']}")

        signals = r.get("signals", [])
        if not signals:
            lines.append("**Key Issues**: None detected")
        else:
            lines.append("**Key Issues**:")
            # Group by severity
            for sev in ("HIGH", "MEDIUM", "LOW"):
                sev_signals = [s for s in signals if s["severity"] == sev]
                if not sev_signals:
                    continue
                sev_icon = RISK_EMOJI.get(sev, "")
                for s in sev_signals:
                    lines.append(f"- {sev_icon} **{s['label']}** — {s['hint']}")
                    if s.get("excerpt"):
                        excerpt = s["excerpt"][:200].replace("\n", " ")
                        lines.append(f"  > *\"{excerpt}\"*")

        lines.append("")

    return "\n".join(lines)


def format_privilege_report(results: list[dict]) -> str:
    today = date.today().isoformat()
    total = len(results)
    skipped = sum(1 for r in results if r.get("skipped"))
    likely = sum(1 for r in results if r.get("classification") == "LIKELY PRIVILEGED")
    possibly = sum(1 for r in results if r.get("classification") == "POSSIBLY PRIVILEGED")

    lines = [
        "# Privilege Review Report",
        f"Generated: {today}",
        f"Documents reviewed: {total - skipped}",
        f"Likely privileged: {likely}",
        f"Possibly privileged: {possibly}",
        "",
        "> **Disclaimer**: This is a first-pass automated filter only.",
        "> It is NOT a legal determination of privilege. All flagged documents",
        "> require review by qualified legal counsel before production.",
        "",
        "## Summary Table",
        "",
        "| Document | Classification | Signals Found |",
        "|----------|---------------|---------------|",
    ]

    for r in results:
        doc_name = r["doc"]
        if r.get("skipped"):
            lines.append(f"| {doc_name} | SKIPPED | {r.get('error', 'unknown')} |")
            continue
        cls = r.get("classification", "NOT PRIVILEGED")
        icon = PRIV_EMOJI.get(cls, "")
        count = len(r.get("signals", []))
        lines.append(f"| {doc_name} | {icon} {cls} | {count} signal(s) |")

    lines += ["", "## Detailed Findings", ""]

    for r in results:
        if r.get("skipped"):
            lines += [f"### {r['doc']}", f"**Status**: SKIPPED — {r.get('error', 'unknown')}", ""]
            continue

        cls = r.get("classification", "NOT PRIVILEGED")
        icon = PRIV_EMOJI.get(cls, "")
        lines += [f"### {r['doc']}", f"**Classification**: {icon} {cls}"]

        signals = r.get("signals", [])
        if not signals:
            lines.append("No privilege markers detected.")
        else:
            lines.append("**Markers found**:")
            for s in signals:
                lines.append(f"- **{s['label']}**")
                if s.get("excerpt"):
                    excerpt = s["excerpt"][:200].replace("\n", " ")
                    lines.append(f"  > *\"{excerpt}\"*")

        lines.append("")

    return "\n".join(lines)


def format_terms_report_md(results: list[dict]) -> str:
    today = date.today().isoformat()
    lines = [
        "# Key Terms Extraction Report",
        f"Generated: {today}",
        f"Documents processed: {len([r for r in results if not r.get('skipped')])}",
        "",
    ]

    for r in results:
        if r.get("skipped"):
            lines += [f"### {r['doc']}", f"SKIPPED: {r.get('error', 'unknown')}", ""]
            continue

        terms = r.get("terms", {})
        lines += [f"### {r['doc']}", ""]

        parties = terms.get("party", [])
        if parties:
            lines.append("**Parties**: " + " | ".join(
                f"{p['name']} ({p['role']})" for p in parties
            ))
            lines.append("")

        financials = terms.get("financial", [])
        if financials:
            lines.append("**Financial Terms**:")
            lines.append("")
            lines.append("| Amount | Context |")
            lines.append("|--------|---------|")
            for f in financials[:15]:
                ctx = f["context"][:100].replace("|", "\\|").replace("\n", " ")
                lines.append(f"| {f['value']} | {ctx} |")
            lines.append("")

        percentages = terms.get("percentage", [])
        if percentages:
            lines.append("**Percentages**:")
            for p in percentages[:10]:
                ctx = p["context"][:100].replace("\n", " ")
                lines.append(f"- {p['value']} — {ctx}")
            lines.append("")

        dates = terms.get("date", [])
        if dates:
            lines.append("**Dates**:")
            for d in dates[:10]:
                ctx = d["context"][:80].replace("\n", " ")
                lines.append(f"- {d['value']} — {ctx}")
            lines.append("")

    return "\n".join(lines)


def format_terms_report_csv(results: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["document", "term_type", "value", "context"])
    for r in results:
        if r.get("skipped"):
            continue
        doc = r["doc"]
        terms = r.get("terms", {})
        for term_type in ("financial", "percentage", "date"):
            for item in terms.get(term_type, []):
                writer.writerow([
                    doc, term_type, item["value"],
                    item["context"][:200].replace("\n", " "),
                ])
        for party in terms.get("party", []):
            writer.writerow([doc, "party", party["name"], party.get("role", "")])
    return buf.getvalue()


# ── Main processing ────────────────────────────────────────────────────────────

def print_progress(n: int, total: int, name: str) -> None:
    bar_len = 30
    filled = int(bar_len * n / total) if total else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    sys.stderr.write(f"\r  [{bar}] {n}/{total}  {name:<40}")
    sys.stderr.flush()
    if n == total:
        sys.stderr.write("\n")
        sys.stderr.flush()


def process_batch(
    directory: Path,
    mode: str,
    focus_terms: Optional[list[str]],
    output_path: Optional[Path],
    fmt: str,
    resume: bool,
) -> str:
    docs = glob_documents(directory)
    if not docs:
        print(f"No documents found in {directory}", file=sys.stderr)
        sys.exit(1)

    total = len(docs)
    print(f"  Found {total} document(s) in {directory}", file=sys.stderr)

    # Content-hash cache: keyed by SHA-256 of file bytes (first 16 hex chars).
    # Falls back to name-based --resume for backwards compatibility.
    cache_file = _cache_path(output_path)
    hash_cache: dict[str, dict] = {}  # hash → result
    name_cache: dict[str, dict] = {}  # doc_name → result (legacy resume)

    if resume:
        if not output_path:
            print(
                "  Warning: --resume requires --output <file> to locate the cache. "
                "Resume skipped — starting fresh.",
                file=sys.stderr,
            )
        else:
            # Load content-hash cache (new format)
            hash_cache = load_hash_cache(cache_file)
            if hash_cache:
                print(f"  Cache: {len(hash_cache)} hashed result(s) loaded", file=sys.stderr)
            else:
                # Fall back to legacy state file (name-based)
                state_path_legacy = output_path.with_suffix(".state.json")
                if state_path_legacy.exists():
                    try:
                        name_cache = {
                            r["doc"]: r
                            for r in json.loads(state_path_legacy.read_text())
                        }
                        print(
                            f"  Resuming (legacy name cache) — "
                            f"{len(name_cache)} already done",
                            file=sys.stderr,
                        )
                    except Exception as e:
                        print(f"  Warning: could not load resume state: {e}", file=sys.stderr)

    results = []
    cache_entries: list[dict] = []  # accumulate for cache write

    for i, doc_path in enumerate(docs, 1):
        doc_name = doc_path.name
        print_progress(i, total, doc_name)

        # Check content-hash cache first
        doc_hash = _doc_hash(doc_path)
        if doc_hash and doc_hash in hash_cache:
            cached = hash_cache[doc_hash]
            results.append(cached)
            cache_entries.append(cached)
            continue

        # Fall back to legacy name-based resume
        if doc_name in name_cache:
            entry = name_cache[doc_name]
            # Promote to hash cache by tagging it
            entry["_hash"] = doc_hash
            results.append(entry)
            cache_entries.append(entry)
            continue

        text, warning = extract_text_from_path(doc_path)

        if not text.strip():
            result: dict = {
                "doc": doc_name,
                "skipped": True,
                "error": warning or "empty document",
            }
        else:
            if mode == "risk":
                signals = extract_risk_signals(text, focus_terms)
                risk_level = score_risk(signals)
                parties = extract_parties(text)
                result = {
                    "doc": doc_name,
                    "risk_level": risk_level,
                    "signals": signals,
                    "parties": parties,
                }
                if warning:
                    result["warning"] = warning

            elif mode == "privilege":
                classification, signals = extract_privilege_signals(text)
                result = {
                    "doc": doc_name,
                    "classification": classification,
                    "signals": signals,
                }
                if warning:
                    result["warning"] = warning

            elif mode == "terms":
                terms = extract_key_terms(text)
                result = {
                    "doc": doc_name,
                    "terms": terms,
                }
                if warning:
                    result["warning"] = warning
            else:
                result = {"doc": doc_name, "skipped": True, "error": f"unknown mode: {mode}"}

        # Tag with content hash for cache
        if doc_hash:
            result["_hash"] = doc_hash

        results.append(result)
        cache_entries.append(result)

        # Write incremental hash cache (replaces legacy state file)
        if cache_file:
            save_hash_cache(cache_file, cache_entries)
        # Always mirror to the canonical directory-level cache for query mode
        save_hash_cache(_dir_cache_path(directory), cache_entries)

    # Generate report
    if mode == "risk":
        report = format_risk_report(results, focus_terms)
    elif mode == "privilege":
        report = format_privilege_report(results)
    elif mode == "terms":
        if fmt == "csv":
            report = format_terms_report_csv(results)
        else:
            report = format_terms_report_md(results)
    else:
        report = f"Unknown mode: {mode}"

    # Clean up legacy state file if it exists (replaced by hash cache)
    legacy_state = output_path.with_suffix(".state.json") if output_path else None
    if legacy_state and legacy_state.exists():
        try:
            legacy_state.unlink()
        except Exception:
            pass
    # Note: hash cache file (.cache.json) is intentionally kept for future runs.

    return report


# ── Open WebUI Tool wrapper ────────────────────────────────────────────────────

try:
    from pydantic import BaseModel as _BaseModel  # type: ignore
    _PYDANTIC = True
except ImportError:
    _PYDANTIC = False
    _BaseModel = object  # fallback so class body doesn't error


class _ValvesMixin:
    """Pydantic Valves if available, plain object otherwise."""
    scan_directory: str = "/tmp/contracts"
    mode: str = "risk"
    focus_terms: str = ""
    output_format: str = "markdown"

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


if _PYDANTIC:
    class _Valves(_BaseModel):  # type: ignore[valid-type]
        scan_directory: str = "/tmp/contracts"
        mode: str = "risk"  # risk | privilege | terms
        focus_terms: str = ""  # comma-separated
        output_format: str = "markdown"  # markdown | csv
else:
    _Valves = _ValvesMixin  # type: ignore[misc]


class Tools:
    """Open WebUI tool wrapper for batch-scanner."""

    Valves = _Valves

    def __init__(self):
        self.valves = _Valves()

    async def scan_contracts(
        self,
        directory: str = "",
        mode: str = "risk",
        focus_terms: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Scan a directory of contracts and return a risk/privilege/terms report.

        :param directory: Path to folder containing contracts (.txt, .pdf, .docx)
        :param mode: 'risk' (default), 'privilege', or 'terms'
        :param focus_terms: Comma-separated list of terms to focus on (e.g. 'indemnification,termination')
        :return: Markdown report
        """
        target = Path(directory or self.valves.scan_directory)
        if not target.exists():
            return f"Directory not found: {target}"

        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"Scanning {target} ({mode} mode)...", "done": False},
            })

        focus = [t.strip() for t in focus_terms.split(",") if t.strip()] if focus_terms else None

        try:
            report = process_batch(
                directory=target,
                mode=mode,
                focus_terms=focus,
                output_path=None,
                fmt="markdown",
                resume=False,
            )
        except SystemExit:
            report = f"No documents found in {target}"
        except Exception as e:
            report = f"Scan error: {e}"

        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "Scan complete", "done": True},
            })

        return report


# ── CLI entrypoint ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="batch-scanner",
        description="Scan a folder of contracts and produce a consolidated risk report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/batch-scanner.py contracts/ --output risk-report.md
  python3 tools/batch-scanner.py contracts/ --focus "indemnification,termination,auto-renewal"
  python3 tools/batch-scanner.py discovery/ --mode privilege
  python3 tools/batch-scanner.py contracts/ --mode terms --format csv
  python3 tools/batch-scanner.py contracts/ --mode terms --output terms.md
  python3 tools/batch-scanner.py contracts/ --mode query --focus "uncapped indemnification"
        """,
    )
    parser.add_argument("directory", help="Directory containing contracts to scan")
    parser.add_argument(
        "--mode", "-M",
        choices=["risk", "privilege", "terms", "query"],
        default="risk",
        help=(
            "Scan mode: risk (default), privilege, terms, or query.\n"
            "  query — search cached results across all documents for --focus terms.\n"
            "          Builds the cache automatically if it doesn't exist yet."
        ),
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: print to stdout)",
    )
    parser.add_argument(
        "--focus", "-f",
        help="Comma-separated focus terms, e.g. 'indemnification,auto-renewal'",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format for --mode terms (default: markdown)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Skip documents whose content hash matches the cache from a previous run. "
            "Only re-processes changed or new files (requires --output). "
            "More reliable than file-name resuming: editing a contract forces reprocessing."
        ),
    )

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    if not directory.is_dir():
        print(f"Error: not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else None
    focus_terms = (
        [t.strip() for t in args.focus.split(",") if t.strip()]
        if args.focus else None
    )

    print(f"\n  Batch Scanner — mode: {args.mode}", file=sys.stderr)
    if focus_terms:
        print(f"  Focus terms: {', '.join(focus_terms)}", file=sys.stderr)
    print("", file=sys.stderr)

    if args.mode == "query":
        if not focus_terms:
            print(
                "Error: --mode query requires --focus <query terms>\n"
                "  Example: --mode query --focus \"uncapped indemnification\"",
                file=sys.stderr,
            )
            sys.exit(1)
        query_str = ", ".join(focus_terms)
        report = query_documents(
            directory=directory,
            query=query_str,
            output_path=output_path,
        )
    else:
        report = process_batch(
            directory=directory,
            mode=args.mode,
            focus_terms=focus_terms,
            output_path=output_path,
            fmt=args.format,
            resume=args.resume,
        )

    if output_path:
        output_path.write_text(report)
        print(f"\n  Report written to: {output_path}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
