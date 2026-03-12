#!/usr/bin/env python3
"""
Evaluate grammar checker models against test samples with known errors.

Compares multiple models (e.g., legal-reviewer vs legal-grammar-ft) on:
  - True positive rate (found expected errors)
  - False positive rate (flagged non-issues)
  - Legal term preservation (never "corrects" terms of art)
  - Output format compliance
  - Response time
"""

import json
import subprocess
import time
import re
import argparse
from pathlib import Path
from datetime import datetime

# Expected findings per test sample (from grammar-test-samples.md)
EXPECTED_FINDINGS = {
    1: {
        "errors": [
            "contraction",        # "don't", "we'd", "didn't"
            "missing_oxford_comma",  # "transcripts, the expert reports and"
            "informal_language",  # "ASAP", "FYI"
            "passive_voice",      # "was reviewed by Sarah"
            "buried_action_item", # settlement response buried at end
        ],
        "legal_terms_present": ["estoppel", "deposition", "interrogatory"],
        "should_be_clean": False,
    },
    2: {
        "errors": [
            "subject_verb_agreement",  # "damages...was", "efforts were"
            "which_that_confusion",    # "which was" should be "that was"
            "tense_inconsistency",     # "will demonstrate" vs past tense
            "sentence_length",         # 50+ word sentences
            "passive_voice",           # "was collected", "was rejected"
            "parallel_structure",      # "negotiations, mediation, and had also proposed"
            "hedging",                 # "arguable", "perhaps"
        ],
        "legal_terms_present": ["material breach", "covenant of good faith", "consequential damages", "mitigation"],
        "should_be_clean": False,
    },
    3: {
        "errors": [
            "and_or_usage",            # "and/or"
            "vague_timeframe",         # "promptly", "reasonable time"
            "dangling_modifier",       # "Having been notified..."
            "defined_term_inconsistency",  # "vendor" vs "Vendor", "client" vs "Client"
            "missing_without_limitation",  # "including" without "without limitation"
        ],
        "legal_terms_present": ["indemnify", "security breach"],
        "should_be_clean": False,
    },
    4: {
        "errors": [
            "modal_verb_error",        # "will be liable" (should be different framing)
            "to_the_extent_misuse",    # "To the extent that" used as "because"
            "nominalization",          # "made the determination"
            "passive_voice",           # "was effectuated", "was filed by"
            "subject_verb_agreement",  # "who exercises" (should be "exercise")
            "inconsistent_party_ref",  # "Rodriguez" vs "Ms. Rodriguez" vs "the employee"
        ],
        "legal_terms_present": ["wrongful termination", "retaliation", "workers' compensation"],
        "should_be_clean": False,
    },
    5: {
        "errors": [],  # Clean sample — should find no critical issues
        "legal_terms_present": ["summary judgment", "material fact", "Fed. R. Civ. P. 56(a)"],
        "should_be_clean": True,
    },
}

REQUIRED_SECTIONS = [
    "CRITICAL ISSUES",
    "GRAMMAR FIXES",
    "STYLE IMPROVEMENTS",
    "CONSISTENCY NOTES",
    "CITATIONS TO VERIFY",
]

LEGAL_TERMS_TO_PRESERVE = [
    "consideration", "estoppel", "laches", "prima facie", "res judicata",
    "sui generis", "inter alia", "pro rata", "arguendo", "ab initio",
    "de novo", "quantum meruit", "indemnify", "covenant", "fiduciary",
    "material breach", "consequential damages", "mitigation",
    "summary judgment", "wrongful termination",
]


def extract_samples(test_file: Path) -> dict[int, str]:
    """Extract test samples from the markdown file."""
    samples = {}
    current_num = 0
    current_text = []
    in_sample_block = False

    for line in test_file.read_text().splitlines():
        if m := re.match(r"^## Sample (\d+):", line):
            if current_num > 0 and current_text:
                samples[current_num] = "\n".join(current_text).strip()
            current_num = int(m.group(1))
            current_text = []
            in_sample_block = False
            continue

        if line.startswith("```") and current_num > 0:
            if "EXPECTED:" in line or not in_sample_block:
                in_sample_block = not in_sample_block
                continue
            in_sample_block = not in_sample_block
            continue

        if current_num > 0 and not in_sample_block and not line.startswith("```"):
            if not line.startswith("EXPECTED:") and not line.startswith("## ") and not line.startswith("---"):
                current_text.append(line)

    if current_num > 0 and current_text:
        samples[current_num] = "\n".join(current_text).strip()

    return samples


def run_model(model: str, text: str) -> tuple[str, float]:
    """Run a model and return (output, elapsed_seconds)."""
    start = time.time()
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=text,
            capture_output=True,
            text=True,
            timeout=120,
        )
        elapsed = time.time() - start
        return result.stdout.strip(), elapsed
    except subprocess.TimeoutExpired:
        return "TIMEOUT", time.time() - start


def score_output(output: str, sample_num: int) -> dict:
    """Score a model's output against expected findings."""
    expected = EXPECTED_FINDINGS.get(sample_num, {})
    output_lower = output.lower()

    # Format compliance
    sections_found = sum(1 for s in REQUIRED_SECTIONS if s.lower() in output_lower)
    format_score = sections_found / len(REQUIRED_SECTIONS)

    # True positives: check if expected errors were found
    expected_errors = expected.get("errors", [])
    found_errors = 0
    missed_errors = []

    error_keywords = {
        "contraction": ["contraction", "don't", "didn't", "we'd", "can't", "won't"],
        "missing_oxford_comma": ["oxford comma", "serial comma", "comma before \"and\"", "reports and"],
        "informal_language": ["informal", "asap", "fyi", "colloquial"],
        "passive_voice": ["passive voice", "passive construction", "was reviewed", "was collected"],
        "buried_action_item": ["action item", "buried", "unclear what action"],
        "subject_verb_agreement": ["subject-verb", "agreement", "damages...was", "data...show", "efforts were"],
        "which_that_confusion": ["which\" vs", "that\" vs", "restrictive", "non-restrictive"],
        "tense_inconsistency": ["tense", "inconsisten"],
        "sentence_length": ["sentence length", "long sentence", "words long", "break up"],
        "parallel_structure": ["parallel", "structure"],
        "hedging": ["hedging", "arguably", "perhaps", "it seems"],
        "and_or_usage": ["and/or", "ambiguous"],
        "vague_timeframe": ["promptly", "reasonable time", "vague", "specific timeframe"],
        "dangling_modifier": ["dangling", "modifier", "having been notified"],
        "defined_term_inconsistency": ["defined term", "inconsisten", "capitaliz", "vendor\" vs", "client\" vs"],
        "missing_without_limitation": ["without limitation", "including but not limited", "ejusdem generis"],
        "modal_verb_error": ["shall", "will", "modal"],
        "to_the_extent_misuse": ["to the extent", "misuse"],
        "nominalization": ["nominalization", "made the determination", "determine"],
        "inconsistent_party_ref": ["inconsisten", "rodriguez", "party reference"],
        "missing_apostrophe": ["apostrophe", "attorneys fees", "attorney's"],
        "missing_comma_after_date": ["comma", "date"],
        "spelling_error": ["spelling", "accomodate", "accommodate"],
        "its_vs_its": ["it's", "its", "possessive"],
        "possessive_error": ["possessive", "plaintiff's", "plaintiffs"],
        "comma_splice": ["comma splice", "run-on"],
        "missing_comma": ["comma"],
        "cap_conflict_with_indemnity": ["indemnif", "limitation", "conflict", "cap"],
        "capitalization_inconsistency": ["capitaliz", "inconsisten"],
        "party_reference_inconsistency": ["party", "inconsisten", "receiving party", "disclosing party"],
    }

    for error in expected_errors:
        keywords = error_keywords.get(error, [error.replace("_", " ")])
        if any(kw in output_lower for kw in keywords):
            found_errors += 1
        else:
            missed_errors.append(error)

    tp_rate = found_errors / len(expected_errors) if expected_errors else 1.0

    # False positive check for clean samples
    false_positive = False
    if expected.get("should_be_clean", False):
        # Check if model flagged significant issues on clean text
        critical_section = re.search(
            r"CRITICAL ISSUES(.*?)(?:GRAMMAR|STYLE|$)",
            output, re.DOTALL | re.IGNORECASE
        )
        if critical_section:
            content = critical_section.group(1).strip()
            false_positive = "none found" not in content.lower() and len(content) > 50

    # Legal term preservation: check model didn't "correct" any terms of art
    legal_terms_in_text = expected.get("legal_terms_present", [])
    terms_incorrectly_modified = []
    for term in legal_terms_in_text:
        # Check if the model suggested replacing or correcting the term
        correction_patterns = [
            f'"{term}" → ',
            f'"{term}" ->',
            f"replace \"{term}\"",
            f"change \"{term}\"",
            f'"{term}" should be',
        ]
        if any(p.lower() in output_lower for p in correction_patterns):
            terms_incorrectly_modified.append(term)

    return {
        "format_score": format_score,
        "sections_found": sections_found,
        "true_positive_rate": tp_rate,
        "found_errors": found_errors,
        "total_expected": len(expected_errors),
        "missed_errors": missed_errors,
        "false_positive_on_clean": false_positive,
        "legal_terms_preserved": len(terms_incorrectly_modified) == 0,
        "terms_incorrectly_modified": terms_incorrectly_modified,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate grammar checker models")
    parser.add_argument("--models", required=True, help="Comma-separated model names")
    parser.add_argument("--test-samples", required=True, help="Path to test samples markdown")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    test_file = Path(args.test_samples)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Extract samples
    samples = extract_samples(test_file)
    print(f"Loaded {len(samples)} test samples")

    results = {
        "timestamp": datetime.now().isoformat(),
        "models": {},
    }

    for model in models:
        # Check if model exists
        check = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model not in check.stdout:
            print(f"\nSKIP {model} — not found in ollama")
            continue

        print(f"\n{'='*50}")
        print(f"Testing: {model}")
        print(f"{'='*50}")

        model_results = {
            "samples": {},
            "aggregate": {},
        }

        total_tp = 0
        total_expected = 0
        total_format = 0
        total_time = 0
        legal_preservation_perfect = True

        for num, text in sorted(samples.items()):
            print(f"  Sample {num}...", end=" ", flush=True)
            output, elapsed = run_model(model, text)
            print(f"{elapsed:.1f}s")

            scores = score_output(output, num)

            model_results["samples"][str(num)] = {
                "scores": scores,
                "elapsed_seconds": round(elapsed, 1),
                "output_length": len(output),
            }

            total_tp += scores["found_errors"]
            total_expected += scores["total_expected"]
            total_format += scores["format_score"]
            total_time += elapsed
            if not scores["legal_terms_preserved"]:
                legal_preservation_perfect = False

        n = len(samples)
        model_results["aggregate"] = {
            "avg_true_positive_rate": round(total_tp / total_expected, 3) if total_expected > 0 else 1.0,
            "avg_format_compliance": round(total_format / n, 3),
            "total_time_seconds": round(total_time, 1),
            "avg_time_seconds": round(total_time / n, 1),
            "legal_terms_preserved": legal_preservation_perfect,
        }

        results["models"][model] = model_results

        print(f"\n  Results for {model}:")
        print(f"    True positive rate: {model_results['aggregate']['avg_true_positive_rate']:.1%}")
        print(f"    Format compliance:  {model_results['aggregate']['avg_format_compliance']:.1%}")
        print(f"    Legal preservation: {'PASS' if legal_preservation_perfect else 'FAIL'}")
        print(f"    Avg time/sample:    {model_results['aggregate']['avg_time_seconds']:.1f}s")

    # Save results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")

    # Print comparison table if multiple models
    if len(results["models"]) > 1:
        print(f"\n{'='*60}")
        print("MODEL COMPARISON")
        print(f"{'='*60}")
        print(f"{'Model':<25} {'TP Rate':>8} {'Format':>8} {'Legal':>7} {'Avg Time':>9}")
        print("-" * 60)
        for model, data in results["models"].items():
            agg = data["aggregate"]
            print(
                f"{model:<25} "
                f"{agg['avg_true_positive_rate']:>7.1%} "
                f"{agg['avg_format_compliance']:>7.1%} "
                f"{'PASS' if agg['legal_terms_preserved'] else 'FAIL':>7} "
                f"{agg['avg_time_seconds']:>7.1f}s"
            )


if __name__ == "__main__":
    main()
