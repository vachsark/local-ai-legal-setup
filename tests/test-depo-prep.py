#!/usr/bin/env python3
"""
Test harness for tools/depo-prep.py

Tests all three features against tests/sample-deposition.txt:
  1. analyze_transcript  — parse, admissions, contradictions, evasions, objections
  2. generate_questions  — topic-specific question generation
  3. prep_outline        — full outline from uploaded materials

Run from the project root:
  python3 tests/test-depo-prep.py
"""

import asyncio
import importlib.util
import json
import os
import sys

# depo-prep.py has a hyphen in the filename — use importlib to load it directly
_spec = importlib.util.spec_from_file_location(
    "depo_prep",
    os.path.join(os.path.dirname(__file__), "..", "tools", "depo-prep.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Tools = _mod.Tools


SAMPLE_TRANSCRIPT = os.path.join(os.path.dirname(__file__), "sample-deposition.txt")

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"
WARN = "\033[93m WARN\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_transcript_file() -> dict:
    """Build a mock Open WebUI file object from the sample transcript."""
    with open(SAMPLE_TRANSCRIPT, "r") as f:
        content = f.read()
    return {
        "filename": "sample-deposition.txt",
        "content": content,
    }


async def mock_emitter(event: dict):
    """Collect status events for inspection."""
    if event.get("type") == "status":
        desc = event["data"].get("description", "")
        done = event["data"].get("done", False)
        marker = "[done]" if done else "[ .. ]"
        print(f"      {marker} {desc}")


# ──────────────────────────────────────────────────────────────────────────────
# Test 1: analyze_transcript
# ──────────────────────────────────────────────────────────────────────────────

async def test_analyze_transcript(tools: Tools) -> bool:
    print(f"\n{BOLD}Test 1: analyze_transcript{RESET}")
    file_obj = load_transcript_file()
    result = await tools.analyze_transcript(
        __files__=[file_obj],
        __event_emitter__=mock_emitter,
    )

    try:
        data = json.loads(result)
    except json.JSONDecodeError as e:
        print(f"  {FAIL} — invalid JSON returned: {e}")
        print(f"  Raw output (first 200): {result[:200]}")
        return False

    stats = data.get("stats", {})
    errors = []

    # Basic structure checks
    if data.get("analysis_type") != "deposition_transcript":
        errors.append("analysis_type not set correctly")

    if stats.get("total_exchanges", 0) < 20:
        errors.append(f"Expected >=20 exchanges, got {stats.get('total_exchanges')}")

    if stats.get("total_objections", 0) < 5:
        errors.append(f"Expected >=5 objections, got {stats.get('total_objections')}")

    if stats.get("admissions_flagged", 0) < 3:
        errors.append(f"Expected >=3 admissions, got {stats.get('admissions_flagged')}")

    if stats.get("evasion_instances", 0) < 3:
        errors.append(f"Expected >=3 evasions, got {stats.get('evasion_instances')}")

    if stats.get("potential_contradictions", 0) < 1:
        errors.append(f"Expected >=1 contradiction, got {stats.get('potential_contradictions')}")

    # Check witness name extracted
    witness = data.get("witness", "")
    if "kowalski" not in witness.lower():
        errors.append(f"Witness name not extracted correctly: got '{witness}'")

    # Check instructions present for LLM
    if not data.get("analysis_instructions"):
        errors.append("analysis_instructions missing from payload")

    if errors:
        for e in errors:
            print(f"  {FAIL} — {e}")
        print(f"\n  Stats: {json.dumps(stats, indent=4)}")
        return False

    print(f"  {PASS} — {stats['total_exchanges']} exchanges, "
          f"{stats['total_objections']} objections, "
          f"{stats['admissions_flagged']} admissions, "
          f"{stats['evasion_instances']} evasions, "
          f"{stats['potential_contradictions']} contradictions")
    print(f"  {PASS} — Witness: {witness}")

    # Print a sample admission and evasion for manual review
    if data.get("admissions"):
        a = data["admissions"][0]
        ex_num = a.get("exchange", a.get("index", "?"))
        print(f"\n  Sample admission (exchange {ex_num}):")
        print(f"    Q: {a['question'][:80]}")
        print(f"    A: {a['answer'][:80]}")

    if data.get("evasion_instances"):
        e = data["evasion_instances"][0]
        print(f"\n  Sample evasion (exchange {e['exchange']}, pattern={e['pattern']}):")
        print(f"    Q: {e['question'][:80]}")
        print(f"    A: {e['answer'][:80]}")

    if data.get("contradictions"):
        c = data["contradictions"][0]
        print(f"\n  Sample contradiction: {c['description'][:100]}")

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Test 2: generate_questions
# ──────────────────────────────────────────────────────────────────────────────

async def test_generate_questions(tools: Tools) -> bool:
    print(f"\n{BOLD}Test 2: generate_questions{RESET}")

    # Read a snippet of the transcript for context
    with open(SAMPLE_TRANSCRIPT) as f:
        context_snippet = f.read()[3000:6000]  # middle section

    result = await tools.generate_questions(
        topic="Meridian's failure to issue service level credits",
        witness_role="VP of Operations",
        case_type="breach of contract",
        context=context_snippet,
        __event_emitter__=mock_emitter,
    )

    try:
        data = json.loads(result)
    except json.JSONDecodeError as e:
        print(f"  {FAIL} — invalid JSON: {e}")
        return False

    errors = []

    if data.get("tool") != "question_generator":
        errors.append("tool field not set")

    if data.get("topic") != "Meridian's failure to issue service level credits":
        errors.append("topic not echoed correctly")

    if not data.get("generation_instructions"):
        errors.append("generation_instructions missing")

    if not data.get("prior_testimony_provided"):
        errors.append("prior_testimony_provided should be True when context is given")

    if not data.get("prior_testimony_sample"):
        errors.append("prior_testimony_sample should be populated")

    if errors:
        for e in errors:
            print(f"  {FAIL} — {e}")
        return False

    print(f"  {PASS} — payload built for topic: '{data['topic']}'")
    print(f"  {PASS} — {len(data['prior_testimony_sample'])} exchanges in context sample")
    print(f"  {PASS} — instructions include one-fact-per-question rule: "
          + ("yes" if "One fact per question" in data["generation_instructions"] else "NO"))

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Test 3: prep_outline
# ──────────────────────────────────────────────────────────────────────────────

async def test_prep_outline(tools: Tools) -> bool:
    print(f"\n{BOLD}Test 3: prep_outline{RESET}")
    file_obj = load_transcript_file()

    result = await tools.prep_outline(
        topics="contract formation, performance failures, notice obligations, damages",
        __files__=[file_obj],
        __event_emitter__=mock_emitter,
    )

    try:
        data = json.loads(result)
    except json.JSONDecodeError as e:
        print(f"  {FAIL} — invalid JSON: {e}")
        return False

    errors = []

    if data.get("tool") != "prep_outline":
        errors.append("tool field not set")

    requested = data.get("requested_topics", [])
    if len(requested) < 3:
        errors.append(f"Expected 4 parsed topics, got {len(requested)}")

    stats = data.get("transcript_stats", {})
    if stats.get("exchanges_parsed", 0) < 20:
        errors.append(f"Expected >=20 exchanges in outline, got {stats.get('exchanges_parsed')}")

    if not data.get("outline_instructions"):
        errors.append("outline_instructions missing")

    if not data.get("covered_topic_areas"):
        errors.append("covered_topic_areas not populated")

    if errors:
        for e in errors:
            print(f"  {FAIL} — {e}")
        return False

    print(f"  {PASS} — requested topics: {requested}")
    print(f"  {PASS} — transcript stats: {json.dumps(stats)}")
    print(f"  {PASS} — {len(data.get('covered_topic_areas', []))} topic areas identified")

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Test 4: edge cases
# ──────────────────────────────────────────────────────────────────────────────

async def test_edge_cases(tools: Tools) -> bool:
    print(f"\n{BOLD}Test 4: edge cases{RESET}")
    all_pass = True

    # No file uploaded
    result = await tools.analyze_transcript(__files__=None, __event_emitter__=mock_emitter)
    if "No document" in result or "No transcript" in result or "paperclip" in result:
        print(f"  {PASS} — no-file gracefully handled")
    else:
        print(f"  {FAIL} — no-file should return helpful message, got: {result[:100]}")
        all_pass = False

    # generate_questions without context
    result = await tools.generate_questions(
        topic="document retention",
        witness_role="records custodian",
        case_type="products liability",
        context="",
        __event_emitter__=mock_emitter,
    )
    try:
        data = json.loads(result)
        if data.get("prior_testimony_provided") is False:
            print(f"  {PASS} — no-context case flagged correctly")
        else:
            print(f"  {WARN} — prior_testimony_provided not False when no context given")
    except Exception as e:
        print(f"  {FAIL} — exception on no-context: {e}")
        all_pass = False

    # prep_outline with no file and no topics
    result = await tools.prep_outline(
        topics="",
        __files__=None,
        __event_emitter__=mock_emitter,
    )
    try:
        data = json.loads(result)
        if data.get("source_file") == "No file uploaded":
            print(f"  {PASS} — no-file outline handled gracefully")
        else:
            print(f"  {WARN} — source_file not 'No file uploaded': {data.get('source_file')}")
    except Exception as e:
        print(f"  {FAIL} — exception on empty outline: {e}")
        all_pass = False

    return all_pass


FEDERAL_TRANSCRIPT = os.path.join(os.path.dirname(__file__), "sample-deposition-federal.txt")


# ──────────────────────────────────────────────────────────────────────────────
# Test 5: Federal format (numbered lines, THE WITNESS, BY MR., multi-volume)
# ──────────────────────────────────────────────────────────────────────────────

async def test_federal_format(tools: Tools) -> bool:
    print(f"\n{BOLD}Test 5: federal transcript format{RESET}")

    if not os.path.exists(FEDERAL_TRANSCRIPT):
        print(f"  {WARN} Federal transcript not found at {FEDERAL_TRANSCRIPT} — skipping")
        return True

    with open(FEDERAL_TRANSCRIPT, "r") as f:
        content = f.read()

    file_obj = {"filename": "sample-deposition-federal.txt", "content": content}
    result = await tools.analyze_transcript(
        __files__=[file_obj],
        __event_emitter__=mock_emitter,
    )

    try:
        data = json.loads(result)
    except json.JSONDecodeError as e:
        print(f"  {FAIL} — invalid JSON: {e}")
        return False

    stats = data.get("stats", {})
    errors = []

    # Should parse exchanges from the federal numbered format
    if stats.get("total_exchanges", 0) < 15:
        errors.append(f"Expected >=15 exchanges from federal format, got {stats.get('total_exchanges')}")

    # Should extract witness name (Priya Anand-Mehta)
    witness = data.get("witness", "")
    if "anand" not in witness.lower() and "mehta" not in witness.lower():
        errors.append(f"Witness name not extracted from federal header: got '{witness}'")

    # Should have objections
    if stats.get("total_objections", 0) < 5:
        errors.append(f"Expected >=5 objections, got {stats.get('total_objections')}")

    # Should have timeline events (the transcript mentions many specific dates)
    if stats.get("timeline_events", 0) < 3:
        errors.append(f"Expected >=3 timeline events, got {stats.get('timeline_events')}")

    # Should have exhibit index (Exhibit 1, 3, 4, 5, 6, 12, 13 referenced)
    if stats.get("exhibits_referenced", 0) < 3:
        errors.append(f"Expected >=3 exhibits, got {stats.get('exhibits_referenced')}")

    # Should have procedural markers (recess, off-record, videotape, exhibit markings)
    if stats.get("procedural_markers", 0) < 2:
        errors.append(f"Expected >=2 procedural markers, got {stats.get('procedural_markers')}")

    # Volume tracking — transcript has VOLUME I and VOLUME II
    # At least some exchanges from Vol.II should be present
    qa_sample = data.get("qa_sample", [])
    vol2_exchanges = [e for e in qa_sample if "Vol.II" in e.get("page_line", "")]
    if not vol2_exchanges:
        errors.append("No Volume II exchanges found — multi-volume handling may be broken")

    if errors:
        for e in errors:
            print(f"  {FAIL} — {e}")
        print(f"\n  Stats: {json.dumps(stats, indent=4)}")
        if qa_sample:
            print(f"\n  First 3 exchanges:")
            for ex in qa_sample[:3]:
                print(f"    [{ex['index']}] {ex['page_line']} examiner={ex.get('examiner','')}")
                print(f"      Q: {ex['question'][:80]}")
                print(f"      A: {ex['answer'][:80]}")
        return False

    print(f"  {PASS} — {stats['total_exchanges']} exchanges, "
          f"{stats['total_objections']} objections, "
          f"{stats['admissions_flagged']} admissions, "
          f"{stats['evasion_instances']} evasions")
    print(f"  {PASS} — Witness: {witness}")
    print(f"  {PASS} — Timeline events: {stats['timeline_events']}, "
          f"Exhibits: {stats['exhibits_referenced']}, "
          f"Procedural markers: {stats['procedural_markers']}")
    print(f"  {PASS} — Volume II exchanges found: {len(vol2_exchanges)}")

    # Print timeline sample
    timeline = data.get("timeline", [])
    if timeline:
        print(f"\n  Timeline sample (first 5 events):")
        for ev in timeline[:5]:
            print(f"    {ev['date_reference']} (exchange {ev['exchange']})")

    # Print exhibit index
    exhibits = data.get("exhibit_index", [])
    if exhibits:
        print(f"\n  Exhibits referenced: {[e['exhibit_id'] for e in exhibits]}")

    # Print procedural markers
    proc = data.get("procedural_markers", [])
    if proc:
        print(f"\n  Procedural markers:")
        for p in proc[:5]:
            print(f"    [{p['category']}] {p['text'][:80]}")

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Test 6: New output fields on original sample
# ──────────────────────────────────────────────────────────────────────────────

async def test_new_output_fields(tools: Tools) -> bool:
    print(f"\n{BOLD}Test 6: new output fields (timeline, exhibits, key admissions){RESET}")

    file_obj = {
        "filename": "sample-deposition.txt",
        "content": open(SAMPLE_TRANSCRIPT).read(),
    }
    result = await tools.analyze_transcript(
        __files__=[file_obj],
        __event_emitter__=mock_emitter,
    )

    try:
        data = json.loads(result)
    except json.JSONDecodeError as e:
        print(f"  {FAIL} — invalid JSON: {e}")
        return False

    errors = []

    # timeline should exist
    if "timeline" not in data:
        errors.append("'timeline' field missing from payload")
    elif len(data["timeline"]) == 0:
        errors.append("timeline is empty — transcript has many dates (2021, 2022, 2023)")

    # exhibit_index should exist (transcript mentions Exhibits 1, 3, 7)
    if "exhibit_index" not in data:
        errors.append("'exhibit_index' field missing from payload")
    elif len(data["exhibit_index"]) == 0:
        errors.append("exhibit_index is empty — transcript references Plaintiff's Exhibit 3, 7")

    # key_admission_index should exist
    if "key_admission_index" not in data:
        errors.append("'key_admission_index' field missing from payload")
    elif len(data["key_admission_index"]) == 0:
        errors.append("key_admission_index is empty")

    # procedural_markers should exist
    if "procedural_markers" not in data:
        errors.append("'procedural_markers' field missing from payload")

    # stats should include new counts
    stats = data.get("stats", {})
    for field in ("timeline_events", "exhibits_referenced", "procedural_markers"):
        if field not in stats:
            errors.append(f"stats.{field} missing")

    if errors:
        for e in errors:
            print(f"  {FAIL} — {e}")
        return False

    print(f"  {PASS} — timeline: {len(data['timeline'])} events")
    print(f"  {PASS} — exhibit_index: {[e['exhibit_id'] for e in data['exhibit_index']]}")
    print(f"  {PASS} — key_admission_index: {len(data['key_admission_index'])} entries")
    print(f"  {PASS} — procedural_markers: {len(data['procedural_markers'])} events")

    # Show top admission
    if data["key_admission_index"]:
        top = data["key_admission_index"][0]
        print(f"\n  Top key admission (exchange {top['exchange']}):")
        print(f"    Q: {top['question'][:80]}")
        print(f"    A: {top['answer'][:80]}")
        print(f"    Note: {top.get('trial_prep_note','')}")

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

async def main():
    print(f"\n{'='*60}")
    print(f"  Depo Prep Tool — Test Suite")
    print(f"  Transcript: {SAMPLE_TRANSCRIPT}")
    print(f"{'='*60}")

    if not os.path.exists(SAMPLE_TRANSCRIPT):
        print(f"\n{FAIL} Sample transcript not found at {SAMPLE_TRANSCRIPT}")
        sys.exit(1)

    tools = Tools()
    results = []

    results.append(await test_analyze_transcript(tools))
    results.append(await test_generate_questions(tools))
    results.append(await test_prep_outline(tools))
    results.append(await test_edge_cases(tools))
    results.append(await test_federal_format(tools))
    results.append(await test_new_output_fields(tools))

    total = len(results)
    passed = sum(results)

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
