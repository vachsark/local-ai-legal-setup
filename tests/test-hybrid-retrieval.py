#!/usr/bin/env python3
"""
Benchmark: BM25-only vs Hybrid (BM25 + semantic) retrieval on sample-contract.txt.

Runs three conceptual queries that BM25 is known to struggle with and prints
a side-by-side comparison showing which sections each method surfaces.

Standalone — no pydantic required. Reimplements the retrieval logic inline.

Usage:
    python3 tests/test-hybrid-retrieval.py
    python3 tests/test-hybrid-retrieval.py --verbose   # show full chunk text
"""

import argparse
import json
import math
import re
import sys
import os
import urllib.request
from typing import Optional

CONTRACT = os.path.join(os.path.dirname(__file__), "sample-contract.txt")

TEST_QUERIES = [
    {
        "query": "What happens if the vendor goes bankrupt?",
        "expected_sections": ["Force Majeure", "Limitation of Liability", "General"],
        "note": "Should find Section 9.4 (Force Majeure). BM25 gets zero hits — 'bankrupt' not in doc.",
    },
    {
        "query": "Are we protected if something goes wrong?",
        "expected_sections": ["Indemnification", "Limitation of Liability"],
        "note": "Conceptual — should surface Section 6 (Indemnification) + Section 7 (Liability cap).",
    },
    {
        "query": "What are the risks in this contract?",
        "expected_sections": ["Limitation of Liability", "Indemnification", "Confidentiality"],
        "note": "Broad query — BM25 anchors on 'risk'; semantic should widen to all protective clauses.",
    },
]

# ── Legal term normalization ─────────────────────────────────────────────────

_LEGAL_SYNONYMS = {
    "indemnif": ["indemnify", "indemnification", "indemnified", "indemnifies", "indemnitor", "indemnitee"],
    "terminat": ["terminate", "termination", "terminates", "terminated"],
    "arbitrat": ["arbitrate", "arbitration", "arbitrator", "arbitrated"],
    "confiden": ["confidential", "confidentiality", "confidentially"],
    "warrant":  ["warranty", "warranties", "warrants", "warranted"],
    "represent":["representation", "representations", "represent", "represents"],
    "liabil":   ["liability", "liabilities", "liable"],
    "infringe": ["infringement", "infringe", "infringes", "infringed"],
    "assign":   ["assignment", "assignee", "assignor", "assign", "assigns", "assigned"],
    "breach":   ["breach", "breaches", "breached"],
}
_STEM_MAP: dict = {}
def _build_stem_map():
    if _STEM_MAP:
        return
    for root, forms in _LEGAL_SYNONYMS.items():
        for form in forms:
            _STEM_MAP[form] = root

_STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","by",
    "from","is","are","was","were","be","been","being","have","has","had","do",
    "does","did","will","would","could","should","may","might","shall","that",
    "this","these","those","it","its","not","no","as","up","if","out","so",
    "than","then","such","each","any","all","both","which","who","what","when","where",
}

def tokenize(text: str) -> list:
    _build_stem_map()
    text = text.lower()
    tokens = re.findall(r"[a-z][a-z0-9'-]*[a-z0-9]|[a-z]", text)
    return [_STEM_MAP.get(t, t) for t in tokens if t not in _STOPWORDS and len(t) > 1]

# ── Chunking ─────────────────────────────────────────────────────────────────

CHUNK_SIZE = 1500
OVERLAP = 200

def detect_header(line: str) -> Optional[str]:
    stripped = line.strip()
    if not stripped:
        return None
    md = re.match(r"^(#{1,6})\s+(.+)$", stripped)
    if md:
        return md.group(2).strip()
    num = re.match(
        r"^(?:Section|SECTION|Article|ARTICLE|Clause|CLAUSE)?\s*"
        r"(\d{1,3}(?:\.\d{1,3}){0,3}\.?|[IVXivx]{1,6}\.?)\s+"
        r"(.{3,60})$", stripped,
    )
    if num:
        title = num.group(2).strip()
        if title and title[0].isupper() and not title.endswith("."):
            return f"Section {num.group(1).rstrip('.')} — {title}"
    if stripped.isupper() and 4 <= len(stripped) <= 60 and not any(c.isdigit() for c in stripped[:3]):
        return stripped.title()
    if stripped.endswith(":") and len(stripped) <= 60 and stripped[0].isupper():
        return stripped.rstrip(":")
    return None

def chunk_document(text: str) -> list:
    lines = text.splitlines()
    chunks = []
    current_section = "Document"
    paragraph_num = 0

    def flush(buf, section, para):
        chunk_text = "\n".join(buf).strip()
        if len(chunk_text) > 50:
            chunks.append({
                "text": chunk_text,
                "citation": f"{section}, paragraph {para}",
                "section": section,
                "paragraph": para,
                "_idx": len(chunks),
            })

    buffer_lines = []
    buffer_len = 0

    for line in lines:
        header = detect_header(line)
        if header:
            if buffer_lines:
                flush(buffer_lines, current_section, paragraph_num)
                overlap_lines, carried = [], 0
                for bl in reversed(buffer_lines):
                    carried += len(bl) + 1
                    overlap_lines.insert(0, bl)
                    if carried >= OVERLAP:
                        break
                buffer_lines = overlap_lines if len("\n".join(buffer_lines)) > OVERLAP else []
                buffer_len = sum(len(l) + 1 for l in buffer_lines)
                paragraph_num = 0
            current_section = header
            buffer_lines.append(line)
            buffer_len += len(line) + 1
            continue

        if not line.strip():
            paragraph_num += 1
            buffer_lines.append(line)
            buffer_len += 1
            if buffer_len >= CHUNK_SIZE:
                flush(buffer_lines, current_section, paragraph_num)
                overlap_lines, carried = [], 0
                for bl in reversed(buffer_lines):
                    carried += len(bl) + 1
                    overlap_lines.insert(0, bl)
                    if carried >= OVERLAP:
                        break
                buffer_lines = overlap_lines
                buffer_len = sum(len(l) + 1 for l in buffer_lines)
            continue

        buffer_lines.append(line)
        buffer_len += len(line) + 1
        if buffer_len >= CHUNK_SIZE * 2:
            flush(buffer_lines, current_section, paragraph_num)
            paragraph_num += 1
            overlap_lines, carried = [], 0
            for bl in reversed(buffer_lines):
                carried += len(bl) + 1
                overlap_lines.insert(0, bl)
                if carried >= OVERLAP:
                    break
            buffer_lines = overlap_lines
            buffer_len = sum(len(l) + 1 for l in buffer_lines)

    if buffer_lines:
        flush(buffer_lines, current_section, paragraph_num + 1)
    return chunks

# ── Embedding ────────────────────────────────────────────────────────────────

def get_embedding(text: str, model: str) -> Optional[list]:
    try:
        payload = json.dumps({"model": model, "prompt": text}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()).get("embedding")
    except Exception:
        return None

def cosine_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x*x for x in a)**0.5
    nb = sum(x*x for x in b)**0.5
    return dot / (na * nb) if na and nb else 0.0

def detect_embed_model() -> Optional[str]:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
        for pref in ("nomic-embed-text", "qwen3-embedding:0.6b", "qwen3-embedding"):
            for m in models:
                if m.startswith(pref):
                    return m
        for m in models:
            if "embed" in m.lower():
                return m
        return None
    except Exception:
        return None

# ── BM25 ─────────────────────────────────────────────────────────────────────

def bm25_retrieve(query: str, chunks: list, top_k: int) -> list:
    query_terms = tokenize(query)
    if not query_terms:
        return chunks[:top_k]

    doc_freq = {}
    for chunk in chunks:
        chunk_terms = set(tokenize(chunk["text"]))
        for term in query_terms:
            if term in chunk_terms:
                doc_freq[term] = doc_freq.get(term, 0) + 1

    n_docs = max(len(chunks), 1)
    idf = {t: math.log((n_docs - doc_freq.get(t,0) + 0.5) / (doc_freq.get(t,0) + 0.5) + 1)
           for t in query_terms}

    scored = []
    for chunk in chunks:
        chunk_terms = tokenize(chunk["text"])
        tf_map = {}
        for t in chunk_terms:
            tf_map[t] = tf_map.get(t, 0) + 1
        chunk_len = len(chunk_terms)
        k1, b, avg_len = 1.5, 0.75, 300
        score = 0.0
        for term in query_terms:
            tf = tf_map.get(term, 0)
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * chunk_len / avg_len))
            score += idf.get(term, 0) * tf_norm
        header_terms = set(tokenize(chunk.get("section", "")))
        score += sum(1 for t in query_terms if t in header_terms) * 2.0
        if score > 0:
            scored.append({**chunk, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

# ── RRF ──────────────────────────────────────────────────────────────────────

def rrf_fuse(bm25_ranked: list, sem_ranked: list, k: int = 60) -> list:
    scores: dict = {}
    for rank, chunk in enumerate(bm25_ranked, 1):
        idx = chunk["_idx"]
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)
    for rank, chunk in enumerate(sem_ranked, 1):
        idx = chunk["_idx"]
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)
    seen: dict = {}
    for chunk in bm25_ranked + sem_ranked:
        idx = chunk["_idx"]
        if idx not in seen:
            seen[idx] = chunk
    fused = [{**c, "score": scores[c["_idx"]]} for c in seen.values()]
    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused

# ── Hybrid ───────────────────────────────────────────────────────────────────

def hybrid_retrieve(query: str, chunks: list, top_k: int, embed_model: str,
                    cache: dict) -> list:
    bm25_full = bm25_retrieve(query, chunks, len(chunks))
    bm25_seen = {c["_idx"] for c in bm25_full}
    bm25_ranked = bm25_full + [{**c, "score": 0.0} for c in chunks if c["_idx"] not in bm25_seen]

    query_vec = get_embedding(query, embed_model)
    if query_vec is None:
        return bm25_full[:top_k]

    sem_scored = []
    for chunk in chunks:
        text = chunk["text"]
        if text not in cache:
            vec = get_embedding(text, embed_model)
            if vec is None:
                continue
            cache[text] = vec
        sim = cosine_sim(query_vec, cache[text])
        sem_scored.append({**chunk, "score": sim})

    if not sem_scored:
        return bm25_full[:top_k]

    sem_scored.sort(key=lambda x: x["score"], reverse=True)
    return rrf_fuse(bm25_ranked, sem_scored, k=60)[:top_k]

# ── Presentation ─────────────────────────────────────────────────────────────

def section_hits(results: list, expected: list) -> list:
    hits = []
    for kw in expected:
        kw_lower = kw.lower()
        for c in results:
            if kw_lower in c.get("citation","").lower() or kw_lower in c.get("text","").lower():
                hits.append(kw)
                break
    return hits

def print_results(label: str, results: list, expected: list, verbose: bool) -> int:
    hits = section_hits(results, expected)
    hit_rate = len(hits) / len(expected) * 100 if expected else 0
    print(f"  [{label}]  Hit rate: {len(hits)}/{len(expected)} ({hit_rate:.0f}%)")
    print(f"    Top sections:")
    for i, c in enumerate(results, 1):
        print(f"      {i}. {c['citation']}  (score={c['score']:.4f})")
        if verbose:
            preview = c["text"][:200].replace("\n", " ")
            print(f"         {preview}...")
    matched = ', '.join(hits) if hits else "(none)"
    print(f"    Expected matches: {matched}")
    return len(hits)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    print("=" * 62)
    print("  Document Q&A — BM25 vs Hybrid Retrieval Benchmark")
    print("=" * 62)
    print(f"  Contract: {os.path.basename(CONTRACT)}")

    with open(CONTRACT) as f:
        text = f.read()

    chunks = chunk_document(text)
    print(f"  Chunks:   {len(chunks)}")

    embed_model = detect_embed_model()
    if embed_model:
        print(f"  Embed:    {embed_model} (hybrid enabled)")
    else:
        print("  Embed:    NOT AVAILABLE — hybrid tests will be skipped")
        print("  Tip: ollama pull qwen3-embedding:0.6b")
    print()

    embed_cache: dict = {}
    total_bm25 = 0
    total_hybrid = 0
    total_expected = 0

    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"Query {i}: \"{test['query']}\"")
        print(f"  Note: {test['note']}")
        print()

        bm25_results = bm25_retrieve(test["query"], chunks, args.top_k)
        bm25_hits = print_results("BM25  ", bm25_results, test["expected_sections"], args.verbose)
        print()

        if embed_model:
            print(f"  [Hybrid — embedding chunks, please wait...]")
            hybrid_results = hybrid_retrieve(test["query"], chunks, args.top_k, embed_model, embed_cache)
            hybrid_hits = print_results("Hybrid", hybrid_results, test["expected_sections"], args.verbose)
        else:
            print("  [Hybrid] SKIPPED — no embedding model available")
            hybrid_hits = 0

        total_bm25 += bm25_hits
        total_hybrid += hybrid_hits
        total_expected += len(test["expected_sections"])

        print()
        print("-" * 62)
        print()

    print("=" * 62)
    print("  SUMMARY")
    print("=" * 62)
    print(f"  BM25   hits: {total_bm25}/{total_expected} ({total_bm25/total_expected*100:.0f}%)")
    if embed_model:
        delta = total_hybrid - total_bm25
        sign = "+" if delta >= 0 else ""
        print(f"  Hybrid hits: {total_hybrid}/{total_expected} ({total_hybrid/total_expected*100:.0f}%)  [{sign}{delta} vs BM25]")
        verdict = "CONFIRMED — hybrid finds more relevant sections" if total_hybrid > total_bm25 \
            else "Both modes equal on this contract" if total_hybrid == total_bm25 \
            else "BM25 outperformed hybrid"
        print(f"  Verdict: {verdict}")
    else:
        print("  Hybrid: NOT TESTED — pull an embedding model to enable")
    print()


if __name__ == "__main__":
    main()
