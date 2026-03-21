# MSA Framework Analysis — Legal AI Application

**Date**: 2026-03-21
**Author**: Claude Sonnet 4.6 (research session)
**Scope**: EverMind-AI MSA (Memory Sparse Attention) framework — what it does, what we can steal, and what it would take to implement fully

---

## What MSA Does and Why It Matters

MSA is an end-to-end trainable framework that extends transformer models to **100M-token contexts** — roughly 75,000 pages of text — with near-linear O(L) complexity instead of the quadratic O(L²) that makes standard attention prohibitive at scale.

The core problem MSA solves is identical to our biggest limitation: standard transformers can't reason across an entire document collection simultaneously. You have to chunk, retrieve, and hope the relevant pieces end up in context together. MSA eliminates that compromise.

### How It Works (Three-Stage Pipeline)

**Stage 1: Offline Encoding (build-time)**
Documents are pre-encoded into compressed "memory blocks" using chunk-mean pooling over KV cache states. A full document library is compressed into a persistent index — not text chunks, but dense neural representations of what the model has already "read." Cost is paid once at index time.

**Stage 2: Online Routing (query-time)**
When a question arrives, sparse routing selects which memory blocks are relevant — similar in spirit to RAG retrieval, but operating on pre-computed model states rather than raw text. The model "knows" what it already compressed, so routing is precise.

**Stage 3: Sparse Generation (inference)**
The model interleaves retrieval and generation in multiple hops ("Memory Interleave"). It generates a partial answer, realizes it needs more context, pulls additional memory blocks, refines — all in a single forward pass chain. Multi-hop reasoning without explicit chain-of-thought prompting.

### The Key Architectural Innovation: Document-wise RoPE

Standard RoPE (Rotary Position Embedding) encodes position as a global offset from position 0. When you concatenate 500 documents into one context, document 500 gets positions 499,000+, far outside training distribution — the model's positional encoding degrades.

MSA resets position IDs to 0 at the start of each document. A model trained on 64K-token contexts can extrapolate to 100M tokens across 1,500 documents because no single document exceeds its training window. Position encoding stays meaningful throughout.

### Performance Numbers

- **94.84% NIAH accuracy at 1M tokens** on just 2×A800 GPUs (baseline RAG gets ~78%)
- **+16% over RAG baselines** on multi-hop reasoning tasks
- **Backbone**: Qwen3-4B with 158.95B tokens of continued pretraining
- **Near-linear scaling**: 10× the documents adds ~10× the index size, not 100× the compute

---

## What We Can Implement NOW (No Training Required)

These are architectural patterns from MSA that can be applied directly to our existing Python code. They require no new model training — just smarter orchestration.

### 1. Iterative Retrieval ("Memory Interleave Lite") in document-qa.py

**The MSA insight**: Don't retrieve once and answer. Retrieve → partial answer → retrieve more → refine.

**Current state**: `document-qa.py` does a single `_retrieve()` call (BM25 + semantic), returns top-K chunks, sends to model. Single-pass.

**What to add**: A two-pass retrieval loop.

```python
# In query_document(), after first retrieval:

# Pass 1: retrieve on original query
initial_chunks = self._retrieve(query, chunks, scaled_max)

# Extract key terms from the initial answer to guide pass 2
# (Run a lightweight extraction — no model call needed)
initial_text = " ".join(c["text"] for c in initial_chunks[:3])
followup_terms = self._extract_followup_terms(query, initial_text)

# Pass 2: retrieve on expanded query if new terms found
if followup_terms:
    expanded_query = query + " " + " ".join(followup_terms)
    followup_chunks = self._retrieve(expanded_query, chunks, scaled_max // 2)
    # Merge, deduplicate by _idx, re-rank by combined score
    top_chunks = self._merge_passes(initial_chunks, followup_chunks)
else:
    top_chunks = initial_chunks
```

`_extract_followup_terms` can be pure Python — extract capitalized phrases and legal nouns from initial_text that don't appear in the original query. No model call needed. This is "poor man's Memory Interleave": if the top chunks mention "Exhibit A" or "Section 12(b)" and the query didn't mention them, retrieve those sections too.

**Impact on legal queries**: Especially valuable for multi-hop questions like "what are the consequences of the indemnification cap being exceeded?" — pass 1 finds the indemnification clause, pass 2 finds the liability limitation section that interacts with it.

**Implementation time**: ~2 hours. Self-contained change to `document-qa.py`.

---

### 2. Document-wise Position Reset for Multi-Document Queries in document-qa.py

**The MSA insight**: Reset positional context per document to prevent position overflow degradation.

**Current state**: When multiple contracts are uploaded (possible via future batch queries), the chunker treats the concatenated text as one long document. Chunks near the end of the second document get high paragraph numbers, confusing the model about where they are.

**What to add**: Mark document boundaries in citations and in the context sent to the model.

```python
# In _chunk_document(), add document boundary awareness:

def _chunk_documents_multi(self, doc_texts: list[tuple[str, str]]) -> list:
    """
    doc_texts: [(filename, text), ...]
    Each document's chunks are tagged with doc_source and reset paragraph_num to 0.
    The assembled context prompt explicitly marks document transitions:
      [DOCUMENT: contract-a.pdf]
      ... chunks ...
      [DOCUMENT: contract-b.pdf]
      ... chunks ...
    """
    all_chunks = []
    for doc_name, text in doc_texts:
        doc_chunks = self._chunk_document(text)
        for c in doc_chunks:
            c["doc_source"] = doc_name
            c["citation"] = f"{doc_name} — {c['citation']}"
        all_chunks.extend(doc_chunks)
    return all_chunks
```

The prompt assembled from these chunks should include `[DOCUMENT: filename]` markers between documents. This is the application-layer equivalent of document-wise RoPE: the model sees explicit document boundaries and won't confuse Section 3.2 of contract A with Section 3.2 of contract B.

**Implementation time**: ~1 hour. Mostly an extension of `_chunk_document`.

---

### 3. Persistent Memory Index for batch-scanner.py

**The MSA insight**: Pre-encode documents once, query the index repeatedly. Don't re-read and re-chunk on every scan.

**Current state**: `batch-scanner.py` reads and re-processes every document on every run. If you run it twice on the same contract folder, it does all the text extraction and pattern matching from scratch.

**What to add**: A simple disk-cached index of extracted signals.

```python
import hashlib, pickle
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "legal-scanner"

def _doc_cache_key(path: Path) -> str:
    stat = path.stat()
    return hashlib.md5(f"{path}{stat.st_mtime}{stat.st_size}".encode()).hexdigest()

def load_cached_result(path: Path) -> Optional[dict]:
    key = _doc_cache_key(path)
    cache_file = CACHE_DIR / f"{key}.pkl"
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    return None

def save_cached_result(path: Path, result: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _doc_cache_key(path)
    with open(CACHE_DIR / f"{key}.pkl", "wb") as f:
        pickle.dump(result, f)
```

In `process_batch()`, check the cache before calling `extract_risk_signals()`. This makes repeated scans instant for unchanged documents and allows incremental processing when new contracts arrive.

**Impact**: If a firm has 200 contracts and adds 5 new ones, the scanner processes only the 5 new ones. The "persistent memory index" idea from MSA at the simplest possible level.

**Implementation time**: ~1 hour.

---

### 4. Cross-Document Query Mode for batch-scanner.py

**The MSA insight**: Query across the entire document collection at once ("find every contract with an uncapped indemnification").

**Current state**: `batch-scanner.py` processes documents sequentially, produces a per-document report. No way to run a cross-document query like "which contracts have indemnification without a liability cap?"

**What to add**: A `--query` mode that loads cached signals and filters/aggregates across all documents.

```python
# New CLI mode:
# python3 tools/batch-scanner.py contracts/ --mode query \
#   --query "uncapped indemnification"

def query_index(directory: Path, query: str) -> list[dict]:
    """
    Load cached scan results for all docs in directory.
    Return docs where any signal label/hint matches query terms.
    """
    results = []
    for doc_path in glob_documents(directory):
        cached = load_cached_result(doc_path)
        if not cached:
            continue  # Skip unscanned docs — run --mode risk first
        signals = cached.get("signals", [])
        query_lower = query.lower()
        matching_signals = [
            s for s in signals
            if query_lower in s["label"].lower() or query_lower in s["hint"].lower()
        ]
        if matching_signals:
            results.append({
                "doc": cached["doc"],
                "matching_signals": matching_signals,
            })
    return results
```

This enables the use case: "find every contract with an uncapped indemnification" — the answer comes back in milliseconds from the cached index, no re-reading required.

**Implementation time**: ~2 hours (depends on caching being implemented first).

---

## What We Could Implement With Moderate Effort

These require building new infrastructure but no model training.

### 5. Embedding-based Memory Index (MSA's "Offline Encoding" simplified)

Instead of pre-computing KV cache states (which requires a modified model), pre-compute embeddings for every paragraph in the document library using our existing `nomic-embed-text` or `qwen3-embedding` model.

```
Document Library → Extract paragraphs → Embed each → Store in FAISS/ChromaDB index
                                                           ↓
                                               Query → Embed query → ANN search → relevant paragraphs
```

This is a standard RAG index, but built on the **entire firm document library** rather than per-query document loading. The key difference from current behavior:

- **Current**: Upload one document, chunk it, retrieve from that document
- **With persistent index**: Build index once across 500 contracts, query returns relevant paragraphs from any of them

Libraries needed: `chromadb` or `faiss-cpu`, `sentence-transformers` (already in ClaudeLab venv).

**Use case unlocked**: "In any of our vendor contracts, what is the standard payment term?" returns relevant clauses from all vendor contracts simultaneously.

**Implementation time**: 1-2 days. Requires a new `index-library.py` script and modifications to `document-qa.py` to support "query library" vs "query uploaded document" mode.

**VRAM note**: Embedding 500 contracts (~300 pages average = 150,000 chars each) takes approximately 10-20 minutes on CPU/GPU with nomic-embed-text. Index size: ~500MB for 500 contracts. Manageable.

---

### 6. Two-Stage SFT with Curriculum Learning (MSA's training approach)

MSA trained on progressively longer contexts: 8K → 64K in two stages. This prevents the model from failing on short examples when optimizing for long-context performance.

**Our equivalent for contract review fine-tuning**:

- Stage 1: Train on single-clause examples (1K-2K tokens) — teach correct output format and legal reasoning on clean, isolated examples
- Stage 2: Train on full contracts (8K-32K tokens) — teach integration and cross-section reasoning

This is more effective than mixing short and long examples randomly, which causes the model to optimize for the average length and fail at the extremes.

**Implementation**: Modify `tune-grammar-models.sh` / the training pipeline to sort training examples by length and train in two passes with different `max_seq_length` settings (2048 for Stage 1, 8192 for Stage 2).

**Implementation time**: ~4 hours (data sorting + training config changes). Requires ClaudeLab venv + QLoRA setup from TRAINING-STRATEGY.md Phase 1.

---

## What Would Require Significant Investment

These require training a new model, substantial compute, or both.

### 7. Full MSA Architecture (True Sparse Attention + Document-wise RoPE at Model Level)

**What it takes**:

- A Qwen3-4B base model (not instruct — you need to modify the architecture)
- Implementing chunk-mean KV cache compression in the model's attention mechanism
- Continued pretraining for position-reset adaptation (MSA used 158.95B tokens — even a 1/100 mini-version is ~1.6B tokens, ~40-80 GPU-hours on an A100)
- Two-stage SFT on long-context legal tasks

**Cost estimate**: $500-2000 for compute, 2-4 weeks of engineering.

**When it's worth it**: If this becomes a legal AI product serving firms with 500+ contract libraries where cross-document reasoning is the core value proposition. Not worth it as a solo practitioner tool.

**Shortcut**: EverMind-AI will likely release the MSA-pretrained Qwen3-4B checkpoint on HuggingFace. Watch for it. If they release the weights, the full capability is available at zero training cost — convert to GGUF, use as a drop-in replacement for qwen3.5:9b.

---

### 8. Neural KV Cache Compression (chunk-mean pooling applied to our documents)

**What it is**: Instead of storing raw text chunks, store compressed neural representations of what the model "understood" about each chunk. This is MSA's offline encoding applied to our use case.

**What it requires**: Access to the model's KV cache states during inference — not possible with Ollama as currently configured. Would require running the model directly via llama.cpp or transformers, extracting intermediate activations, and storing them.

**Cost**: High engineering effort, breaks the current Ollama-based architecture, requires significant VRAM during index build (the full model must process every document).

**Verdict**: Skip unless we move off Ollama to a custom inference stack.

---

## Specific Code Changes

### document-qa.py — Priority Changes

1. **Add iterative retrieval** (2-pass query expansion) — Section 1 above
   - New method: `_extract_followup_terms(query: str, initial_text: str) -> list[str]`
   - New method: `_merge_passes(pass1: list, pass2: list) -> list`
   - Modify: `query_document()` to call two-pass retrieve when doc has >50 chunks

2. **Add document boundary markers** in assembled context — Section 2 above
   - New method: `_chunk_documents_multi(doc_texts: list[tuple]) -> list`
   - Modify: prompt assembly to include `[DOCUMENT: filename]` separators

3. **Add embedding cache persistence** (write to disk, not just in-memory per-instance)
   - Current `_embed_cache` is a dict that dies when the tool session ends
   - Persist to `~/.cache/legal-qa/{doc_hash}.pkl` keyed by document content hash
   - Saves ~30s of re-embedding on the second query to the same document

### batch-scanner.py — Priority Changes

1. **Add disk cache** for scan results — Section 3 above
   - New functions: `load_cached_result()`, `save_cached_result()`, `_doc_cache_key()`
   - Modify: `process_batch()` to check cache before processing, save after

2. **Add `--mode query` with cross-document index search** — Section 4 above
   - New function: `query_index(directory: Path, query: str) -> list[dict]`
   - New CLI arg: `--query "search terms"`
   - Add to `main()` argparse handling

3. **Add `--mode compare` for two-contract comparison**
   - Takes two document paths
   - Runs extract_risk_signals on both
   - Outputs a side-by-side diff of signals present in one but not the other
   - High-value for "compare this new vendor contract against our standard template"

---

## Minimum Viable Implementation That Captures MSA's Key Insight

MSA's core insight is: **pre-encode documents once, route sparsely, reason iteratively**.

The minimum viable version of this for our project, achievable in a week with zero training:

1. **Pre-encode**: Disk cache for scan results + embedding cache persistence. One-time cost, instant on repeat.

2. **Route sparsely**: Cross-document query mode (`--mode query`). Instead of reading 500 contracts, load cached signals and filter. Near-instant.

3. **Reason iteratively**: Two-pass retrieval in document-qa.py. Second pass uses terms extracted from first-pass results. No model change, just smarter Python.

This gives us:

- Cross-document queries across an entire firm's contract library
- Sub-second response on repeat queries to cached documents
- Better multi-hop answers for complex contract questions

**Total implementation**: ~1.5 days of focused work.

---

## Summary Table

| Enhancement                   | Effort    | Impact                                   | Ready Now?                 |
| ----------------------------- | --------- | ---------------------------------------- | -------------------------- |
| Two-pass iterative retrieval  | 2h        | High — better multi-hop answers          | Yes                        |
| Document boundary markers     | 1h        | Medium — fewer cross-doc confusions      | Yes                        |
| Persistent embedding cache    | 1h        | Medium — faster repeat queries           | Yes                        |
| Disk cache for scan results   | 1h        | High — incremental batch scans           | Yes                        |
| Cross-document query mode     | 2h        | Very High — firm-wide contract search    | Yes (needs cache first)    |
| Persistent FAISS/Chroma index | 1-2d      | Very High — full library semantic search | Moderate effort            |
| Curriculum SFT (Stage 1→2)    | 4h        | Medium — better long-context fine-tune   | Moderate (needs GPU setup) |
| Full MSA model training       | 2-4 weeks | Very High                                | Significant investment     |
| Watch for MSA weights release | 0h        | Very High if released                    | Wait and see               |

---

_Analysis generated 2026-03-21. Update when MSA weights are released publicly or when iterative retrieval is implemented and benchmarked._
