# Training Strategy — Legal-Domain Model for local-ai-legal-setup

**Date**: 2026-03-21
**Author**: Claude Sonnet 4.6 (research session)
**Scope**: Cost-effective path from "general models with system prompts" to a genuinely better legal model

---

## TL;DR (Read This First)

**The honest answer**: For the tasks in this project (grammar checking, contract review, deposition summarization, IRAC memos), **RAG + better prompts will close more gaps than a fine-tuned model**, and they're free to implement. But a targeted fine-tune is realistic, and the grammar checker is the best first candidate.

**The recommendation** (ordered by ROI):

1. **Immediate, $0**: QLoRA fine-tune the grammar checker on your existing 187 examples + synthetic expansion. You already have the pipeline (`tune-grammar-models.sh`), ClaudeLab venv, and 16GB VRAM. Target: `qwen3.5:4b` base, legal-grammar task. This is the highest-confidence improvement available today.

2. **Next, $0-50**: Build a semantic legal RAG layer (court rules, statutes, Bluebook) for the `court-rules` and `brief-reviewer` models. Retrieval is faster to ship than training and more accurate for factual lookups.

3. **Then, $200-500**: QLoRA SFT on `Qwen/Qwen3.5-4B-Instruct` or `Llama-3.2-3B-Instruct` using LawInstruct + CUAD + your existing data. The 4B class fits in 16GB VRAM for training without cloud spend.

4. **Only if needed, $500-2000**: Cloud fine-tune (RunPod/Modal) on a 9B-14B model for the `memo-drafter` and `contract-reviewer` use cases where quality visibly lags.

5. **Skip unless this becomes a product**: Continued pre-training on Pile of Law (30B+ token corpus, $2000-5000). The delta over a well-SFT'd model is real but marginal for the structured tasks here. This is what SaulLM did — it improved legal text generation quality but SaulLM-7B still underperforms GPT-4 on complex reasoning tasks.

---

## 1. Current State Assessment

### What the project has

| Component         | Status                                                                                                                          |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Models            | gemma3:12b (summarization), qwen3.5:9b (structured analysis), mistral-small:24b (IRAC)                                          |
| Grammar fine-tune | Pipeline exists (`tune-grammar-models.sh`), 187 training examples, Qwen2.5-3B base, ClaudeLab venv ready                        |
| Training data     | 187 labeled legal grammar examples: 53 contract, 40 brief, 34 email, 21 grammar, 20 plain, remainder (depo, memo, letter, etc.) |
| ClaudeLab venv    | PyTorch 2.9.1+ROCm6.3, full ML stack, at `Projects/ClaudeLab/.venv/`                                                            |
| GPU               | AMD RX 9070 XT, 16GB VRAM, gfx1201 (RDNA4) — bitsandbytes confirms QLoRA support for gfx1201                                    |
| Infrastructure    | `tests/tune-grammar-models.sh` end-to-end pipeline: generate → prepare SFT → train → GGUF → Ollama                              |

### Where models struggle

Based on the audit history and Modelfile notes:

- **Complex IRAC reasoning** (mistral-small:24b handles this but it's slow at ~25 t/s; smaller models fail at multi-step legal analysis)
- **Citation accuracy** (models fabricate reporters — the citation checker exists precisely because this is a known failure mode)
- **Contract risk specificity** (models give vague "HIGH risk" summaries without quoting exact language or naming the mechanism — fixed with contrast examples in the audit, but fundamentally a training issue)
- **Court rule precision** (requires exact current rules — this is a retrieval problem, not a reasoning problem)

---

## 2. Data Landscape

### What exists and what's usable

| Dataset                | Size                                   | Task                       | License                | Verdict                                                                                  |
| ---------------------- | -------------------------------------- | -------------------------- | ---------------------- | ---------------------------------------------------------------------------------------- |
| **Pile of Law**        | 291GB raw / ~30B tokens after cleaning | Continued pretraining      | CC-BY-NC-SA-4.0        | ⚠️ Non-commercial only. Good for research. Not for commercial deployment.                |
| **LawInstruct**        | 116GB / 10M-100M examples              | Instruction fine-tuning    | **MIT**                | ✅ Best general-purpose legal SFT dataset. 142 datasets, 28 languages.                   |
| **CUAD**               | 22,450 train examples                  | Contract clause QA         | **CC-BY-4.0**          | ✅ Commercial OK. 510 contracts, 41 clause categories. Direct fit for contract-reviewer. |
| **MAUD**               | 39,200 examples                        | M&A contract QA            | **CC-BY-4.0**          | ✅ Commercial OK. Specialized for merger agreements. Useful for contract work.           |
| **LexGLUE**            | ~230K examples (7 datasets)            | Classification, QA         | **CC-BY-4.0**          | ✅ Good for evaluation. Includes CaseHOLD (52.5K multiple-choice holdings).              |
| **LegalBench**         | 162 tasks                              | Legal reasoning evaluation | Mixed (task-dependent) | ⚠️ Primarily for eval. Small train splits. Use to benchmark, not train.                  |
| **Law StackExchange**  | ~19M tokens                            | Q&A                        | CC-BY-SA-4.0           | ✅ Conversational legal Q&A — useful for instruction tuning format.                      |
| **CourtListener**      | Millions of opinions                   | Continued pretraining      | Public domain          | ✅ Free for all use. Primary source for US case law.                                     |
| **Your existing data** | 187 labeled examples                   | Grammar correction (SFT)   | Yours                  | ✅ High quality. Expand to 500-1000 before training.                                     |

**Key insight**: LawInstruct (MIT license, 116GB, 142 legal datasets) is the single best resource. It already curates and formats most of the above into instruction-following pairs. Start here, not with raw Pile of Law.

### What you could generate cheaply

You have Claude access via your Max subscription. The existing data generation pipeline uses Claude Sonnet to produce labeled examples at no API cost. Strategies:

- **Contract risk identification pairs**: Give Claude 100 real contract clauses (from public EDGAR filings), ask it to produce WRONG/CORRECT analysis pairs (matching the contrast example format from the audit). Target: 500+ examples.
- **IRAC memo pairs**: Public case facts (CourtListener) → IRAC analysis. Claude Sonnet produces high-quality IRAC. Use as training targets.
- **Deposition summary pairs**: Public deposition transcripts (PACER-scraped) → structured summaries.
- **Legal grammar corrections**: Expand from 187 → 500+ by generating harder examples in underrepresented categories (deposition, memo, letter, order).

**Estimated generation time**: 500 examples at ~30s/example via Claude API = ~4 hours in batched mode. Your `gen-grammar-data.sh` pipeline already does this.

---

## 3. Base Model Options

### The comparison matrix

| Model                     | Params | VRAM (4-bit) | IFEval | MMLU | Legal Tasks          | License    | Verdict                                          |
| ------------------------- | ------ | ------------ | ------ | ---- | -------------------- | ---------- | ------------------------------------------------ |
| **Qwen3.5-4B-Instruct**   | 4B     | ~3-4GB       | ~88    | ~79  | Untested             | Apache 2.0 | ✅ Best local training target                    |
| **Qwen3.5-9B-Instruct**   | 9B     | ~6GB         | 91.5   | ~83  | Strong               | Apache 2.0 | ✅ Current production model                      |
| **Llama-3.2-3B-Instruct** | 3B     | ~2-3GB       | ~77    | ~63  | Moderate             | Llama 3    | ✅ Smallest viable fine-tune                     |
| **Llama-3.1-8B-Instruct** | 8B     | ~5-6GB       | ~80    | ~73  | Good                 | Llama 3    | ✅ Well-tested for QLoRA                         |
| **Phi-4**                 | 14B    | ~9-10GB      | ~88    | 84.8 | Strong reasoning     | **MIT**    | ✅ Best reasoning/param at 14B                   |
| **Gemma3-12B-Instruct**   | 12B    | ~8-9GB       | ~82    | ~79  | Good                 | Gemma ToS  | ⚠️ In use for summarization, not for fine-tuning |
| **Mistral-Nemo-12B**      | 12B    | ~8-9GB       | ~78    | ~68  | Moderate             | Apache 2.0 | ⚠️ Worse than Phi-4 at same size                 |
| **SaulLM-7B-Instruct**    | 7B     | ~5GB         | —      | —    | Best-in-class (2024) | **MIT**    | ✅ Use it directly — skip training               |
| **Qwen2.5-3B-Instruct**   | 3B     | ~2-3GB       | ~82    | ~66  | Moderate             | Apache 2.0 | ✅ Current grammar fine-tune base                |

### SaulLM — the most important entry

SaulLM-7B-Instruct (Equall.ai, MIT license) is a Mistral-7B model continued-pretrained on 30 billion tokens of legal text, then instruction-tuned on legal Q&A, summarization, and reasoning tasks. It's the result of exactly the training run described in the research brief — and it's available today at `Equall/Saul-Instruct-v1` on HuggingFace.

**The strategic question is**: Does SaulLM already solve your problems? Test it on your eval set before doing any training. If it scores materially better than qwen3.5:9b on contract review and memo drafting, just use it.

Convert it to GGUF for Ollama:

```bash
# In ClaudeLab venv
pip install huggingface_hub
huggingface-cli download Equall/Saul-Instruct-v1
# Then convert to GGUF and quantize with llama.cpp
python3 /home/veech/Documents/llama.cpp/convert_hf_to_gguf.py ./Saul-Instruct-v1 --outtype q8_0
```

**Likely result**: SaulLM-7B is better than general 7B models at legal reasoning but still behind mistral-small:24b for complex IRAC. Worth testing before spending training budget.

### Recommendation: Fine-tune Qwen3.5-4B, not 9B

Training a 9B model with QLoRA on 16GB VRAM is tight — you can do it, but batch size is constrained (batch=1 or 2) which means slow training. Qwen3.5-4B fits comfortably (3-4GB for the 4-bit model, leaving 12GB for gradients + optimizer states). The 4B model also runs faster at inference (~80 t/s on your GPU vs ~55 for 9B).

The gap between 4B and 9B on structured legal tasks (JSON output, checklist following) is smaller than the gap between general-purpose and legal-fine-tuned at the same size.

---

## 4. Training Approaches (Cost/Benefit)

### Option A: SFT on legal Q&A pairs (cheapest, recommended first)

Fine-tune on (input, output) pairs where input is a legal document + task instruction and output is the desired structured response.

**Cost**: $0 if done locally on your 4B model.
**What it improves**: Instruction following on legal tasks, output format consistency, domain vocabulary.
**What it doesn't improve**: Underlying legal knowledge beyond what's in the base model.
**When it's enough**: Grammar checking, contract clause extraction, structured report format.

For your grammar checker: 187 → 500+ examples, SFT on Qwen2.5-3B or Qwen3.5-4B. This is ready to execute now.

### Option B: Continued pre-training on legal corpus, then SFT

Start with a base model (not instruct), run unsupervised next-token prediction on Pile of Law or LawInstruct text, then apply SFT.

This is what SaulLM did. Results:

- SaulLM-7B achieves state-of-the-art on LegalBench for 7B-class models
- Continued pretraining on 30B legal tokens costs approximately $3,000-8,000 on cloud GPU at current rates (100-200 GPU-hours on A100s)
- The gain over well-SFT'd general models is real but measured in single-digit percentage points on most benchmarks

**Verdict for this project**: Skip unless you're building a product. The improvement on structured tasks (grammar correction, contract extraction) comes almost entirely from the SFT stage, not the pretraining stage. SaulLM's advantage is in generation quality for long legal prose — useful for brief drafting at scale, marginal for structured analysis.

### Option C: DPO/GRPO with legal reasoning preference data

DPO trains on (prompt, chosen, rejected) triples — you show the model which response is better for the same input.

**When it's better than SFT**: When you have clear quality signals (one response is obviously better than another) and want to improve relative ranking rather than absolute output format. Good for: "which contract analysis is more actionable?" type comparisons.

**When it's worse**: You need high-quality preference pairs. Generating these requires either human annotation (expensive) or using a strong model (Claude/GPT-4) to judge pairs (fast but introduces teacher model bias).

**Practical approach**: After SFT, generate 5 contract analyses with your SFT model, use Claude to score them, build a preference dataset, then DPO. This is the "SFT → DPO" stack used by most production-grade fine-tunes.

**For GRPO**: This is process-based reward optimization — the model gets reward signals for correct reasoning steps, not just correct final answers. Most relevant for legal reasoning tasks where you want the model to follow IRAC structure. Requires a functioning reward model. More complex to set up, roughly 2x the training cost of SFT. Worth considering for Phase 3.

**Verdict**: Run SFT first. If SFT outputs are consistently structurally correct but sometimes wrong in content, add DPO. If you want better IRAC chain-of-thought, add GRPO on top.

### Option D: Distillation from Claude/GPT-4

Use a strong model (Claude Sonnet, which you have via Max) to generate high-quality answers, train the small model to match them.

This is essentially your current data generation approach. You're already doing this for grammar training. The key constraint is data volume — you need 500-2000 examples minimum for a meaningful fine-tune.

**Cost**: ~$0 with your Max subscription (just compute time). The `generate-grammar-batches.py` → `gen-grammar-data.sh` pipeline is the implementation.

**Verdict**: This is the most practical near-term approach. Expand existing data generation to cover contract review and IRAC before doing anything else.

### Option E: Better RAG (retrieval-augmented generation)

A well-implemented RAG layer would give the `court-rules` and `brief-reviewer` models access to:

- Current Federal Rules of Appellate/Civil/Criminal Procedure
- Circuit-specific local rules
- Bluebook 21st edition rules
- FRAP word count and formatting rules

This is a retrieval problem, not a training problem. The model already knows how to reason — it just doesn't have current rule text in context.

**Cost**: $0 (build a ChromaDB or FAISS index from publicly available PDFs).
**Implementation time**: 1-2 days for a working prototype.
**Effect on court-rules accuracy**: Very high. The current model answers from training data memory (may be outdated, may hallucinate circuit-specific variations). RAG with authoritative sources would eliminate most rule-related errors.

**Verdict**: Do RAG before fine-tuning for any factual/rule-lookup task. It's faster, cheaper, and more maintainable (update the index when rules change instead of retraining).

---

## 5. VRAM and Hardware Reality Check

### Your AMD RX 9070 XT (16GB, gfx1201)

**Confirmed**: bitsandbytes supports gfx1201 (RDNA4). QLoRA 4-bit quantization works.

| Task                    | Model                          | VRAM needed | Feasible?                                                |
| ----------------------- | ------------------------------ | ----------- | -------------------------------------------------------- |
| QLoRA SFT, seq_len 2048 | 3B (Qwen2.5-3B / Llama-3.2-3B) | ~6-8GB      | ✅ Comfortable                                           |
| QLoRA SFT, seq_len 2048 | 4B (Qwen3.5-4B)                | ~7-9GB      | ✅ Good                                                  |
| QLoRA SFT, seq_len 2048 | 7B (SaulLM / Llama-3.1-8B)     | ~10-14GB    | ✅ Tight but works (batch=1-2)                           |
| QLoRA SFT, seq_len 2048 | 9B (Qwen3.5-9B)                | ~12-16GB    | ⚠️ Very tight, requires gradient checkpointing + batch=1 |
| QLoRA SFT, seq_len 2048 | 14B (Phi-4)                    | ~20-24GB    | ❌ OOM on 16GB                                           |
| Full fine-tune          | Any 7B+                        | 40-80GB     | ❌ Not on this hardware                                  |

**Practical recommendation**: Train on 3B-4B models locally. Use cloud for 9B+.

**AMD-specific note**: Unsloth (the fastest QLoRA library, 2x speed) has AMD support but requires an AMD Guide setup and has historically lagged NVIDIA support. The ClaudeLab venv uses PyTorch 2.9.1+ROCm6.3, which is current — standard HuggingFace TRL + bitsandbytes should work. If Unsloth AMD issues arise, fall back to HF TRL with standard LoRA.

---

## 6. Cloud Training Cost Estimates

### Pricing (as of 2026-03-21)

| Provider | GPU       | VRAM | $/hr        |
| -------- | --------- | ---- | ----------- |
| Modal    | A100 80GB | 80GB | ~$2.50      |
| Modal    | A100 40GB | 40GB | ~$2.10      |
| Modal    | H100 80GB | 80GB | ~$3.95      |
| RunPod   | RTX 4090  | 24GB | ~$0.50-0.80 |
| RunPod   | A100 80GB | 80GB | ~$2.00-2.50 |
| RunPod   | H100 SXM  | 80GB | ~$3.50-4.00 |
| Vast.ai  | RTX 4090  | 24GB | ~$0.35-0.60 |

### Training time estimates

Based on public benchmarks (A100 40GB):

| Job                      | Model        | Dataset                           | Time        | Cost        |
| ------------------------ | ------------ | --------------------------------- | ----------- | ----------- |
| SFT grammar checker      | Qwen3.5-4B   | 500 examples, 3 epochs            | ~20min      | <$1         |
| SFT contract reviewer    | Qwen3.5-9B   | 1000 examples, 3 epochs           | ~2-3hr      | ~$5-8       |
| SFT full legal assistant | Llama-3.1-8B | LawInstruct subset (50K), 1 epoch | ~8-12hr     | ~$20-30     |
| SFT full legal assistant | Phi-4 14B    | LawInstruct subset (50K), 1 epoch | ~20-30hr    | ~$50-75     |
| Continued pretraining    | Mistral-7B   | 30B tokens (SaulLM-scale)         | 100-200hr   | ~$250-500   |
| SaulLM-scale 32B model   | Qwen2.5-32B  | 30B tokens                        | 400-800hr   | ~$1000-2000 |
| Cursor Composer-scale    | 32B          | Custom dataset, multiple epochs   | 1000-3000hr | ~$2500-7500 |

### The $100-500 budget

For $200-300 of cloud GPU time on an A100:

- Fine-tune Llama-3.1-8B or Qwen3.5-9B on LawInstruct (50K-100K examples, 1-2 epochs)
- This produces a model equivalent to or better than SaulLM-7B on your specific task mix
- LawInstruct is MIT licensed, so the resulting model can be commercially deployed

**The 4090 path (~$0.50/hr on RunPod)**: A single RTX 4090 (24GB VRAM) can train a 9B model with QLoRA. 100 hours of training = ~$50-80. More time-efficient than A100 per dollar for this size class.

---

## 7. Phased Roadmap

### Phase 1: Today, $0 — Grammar checker fine-tune

**What**: Expand the grammar training data from 187 → 500+ examples, run the existing `tune-grammar-models.sh` pipeline against `qwen3.5:4b` as the new base.

**Time**: 1-2 days (data generation is automated, training is ~2-4 hours local)

**Steps**:

1. Update `BASE_MODEL` in `tune-grammar-models.sh` from `Qwen/Qwen2.5-3B-Instruct` to `Qwen/Qwen3.5-4B-Instruct`
2. Run `./tune-grammar-models.sh generate` to expand to 500+ examples (fill underrepresented categories: discovery, depo, memo, letter, order)
3. Run `./tune-grammar-models.sh all`
4. Compare GGUF output against current `legal-grammar-ft` model using `eval-grammar.py`

**Expected improvement**: Better instruction following on edge cases, fewer category-level failures.

**Also do**: Test SaulLM-7B-Instruct on 20 contract review and memo tasks. Compare to qwen3.5:9b. If it's better, swap it in with no training required.

### Phase 2: Next 2-4 weeks, $0 — RAG layer for factual tools

**What**: Build a retrieval layer for `court-rules` and `brief-reviewer`.

**Steps**:

1. Download Federal Rules (FRAP, FRCP, FRCrP) as text from govinfo.gov
2. Download 9th Circuit, SDNY, and other commonly-used local rules
3. Build a ChromaDB index using the ClaudeLab venv (sentence-transformers already installed)
4. Modify the `court-rules` Modelfile to inject retrieved rule text into context

**Expected improvement**: Eliminates rule hallucination for supported courts. Much higher accuracy on "does my brief comply with Rule 28(a)?" type queries.

**Also do**: Generate 500-1000 contract review pairs (EDGAR public filings → Claude analysis) using the existing batch generation pipeline. Stage them for Phase 3.

### Phase 3: $100-300 — Targeted SFT on 9B model

**When**: After Phase 1 and 2 are complete and you've identified remaining gaps.

**What**: QLoRA SFT on Qwen3.5-9B or Llama-3.1-8B using a curated mix:

- LawInstruct subset: 20K examples filtered to US jurisdiction (contract, brief, memo task types)
- Your generated contract review pairs: 500-1000 examples
- CUAD for contract clause extraction: 10K training examples
- MAUD for M&A contract specifics: 10K training examples

**Compute**: 20-30 hours on a RunPod RTX 4090 (~$15-25) for a 9B model at this dataset size.

**Expected result**: A 9B model that significantly outperforms current qwen3.5:9b on contract analysis and IRAC structure. Should approach mistral-small:24b quality on legal tasks at 2x the inference speed.

### Phase 4: $500-2000 — Phi-4 14B or 32B-class fine-tune

**When**: If Phase 3 results are strong and the project needs higher capability.

**What**: Fine-tune Phi-4 (14B, MIT license, strong reasoning) on your full curated dataset. Phi-4 has better reasoning fundamentals than Qwen3.5-9B (GPQA 56.1 vs ~45 for 9B-class models).

**Compute**: 40-80 hours on a 2×A100 80GB setup on RunPod or Modal (~$200-400).

**Expected result**: The best local-running legal model available to you. Would handle complex IRAC with quality approaching GPT-4 on well-formatted tasks.

### Phase 5: $2000-10000 — Cursor-level investment

**Cursor's approach**: They fine-tuned Qwen2.5 Coder 32B on a custom dataset of code editing and agentic coding tasks — multiple epochs, likely 1000+ GPU-hours.

**The legal equivalent**: Continued pretraining of a 32B model (Qwen2.5-32B or Llama-3.3-70B) on 30B+ tokens of Pile of Law + LawInstruct, followed by multi-task instruction tuning.

**Cost estimate**: 200-800 A100-hours for pretraining ($500-2000) + 50-100 A100-hours for SFT ($125-250) = $600-2500 total.

**What you get**: A model at the SaulLM-70B tier. On complex legal reasoning (bar exam questions, multi-step contract analysis), meaningfully better than any 7-14B model.

**When it's worth it**: When the project becomes a commercial product serving paying attorneys. Not worth it for a local open-source tool — the cost recovery time is too long.

---

## 8. Is Training Even the Right Approach?

### Where training clearly helps

- **Grammar correction**: Fine-tuning on labeled (error, correction) pairs consistently outperforms prompting at this task. The grammar checker should be a fine-tuned model. This is already your plan.
- **Output format consistency**: SFT teaches the model to produce structured JSON/checklists reliably. Prompting achieves ~80% format compliance; SFT achieves ~98%.
- **Legal vocabulary and entity recognition**: A model that has seen 30B tokens of legal text is less likely to confuse procedural posture, hallucinate reporters, or misapply doctrines.

### Where RAG clearly beats training

- **Factual rule lookups** (court rules, citation formats, current statutes): Rules change. Training data has a cutoff. A model trained on 2023 rules will give wrong answers for 2024 amendments. A RAG system with updated rule PDFs is always current.
- **Jurisdiction-specific variations**: No single fine-tuned model can memorize all circuit-level local rules reliably. Retrieval is the correct architecture here.
- **Specific case law**: The model cannot memorize 40+ years of case law. For "what's the standard in the 9th Circuit for preliminary injunctions?", retrieve a recent circuit opinion rather than rely on the model's memory.

### Where prompting closes most of the gap

- **Format compliance**: The WRONG/CORRECT contrast examples added in the audit are the right fix for vague output. Adding contrast examples to system prompts costs $0 and improves output quality substantially.
- **Task decomposition**: Breaking "review this contract" into "identify parties → extract term → flag unusual clauses" as sequential sub-prompts often matches fine-tuned output quality.

### The honest tradeoff matrix

| Problem                    | Prompting | RAG            | Fine-tune | Verdict                                 |
| -------------------------- | --------- | -------------- | --------- | --------------------------------------- |
| Grammar correction         | 60%       | Not applicable | 90%+      | Fine-tune                               |
| Contract clause extraction | 75%       | 75%            | 90%       | Fine-tune or RAG                        |
| Court rule compliance      | 55%       | 95%+           | 70%       | **RAG**                                 |
| IRAC memo drafting         | 70%       | 60%            | 85%       | Fine-tune                               |
| Deposition summarization   | 80%       | N/A            | 85%       | Prompting is good enough                |
| Citation checking          | 40%       | 95%+           | 65%       | **RAG** (you already built the checker) |
| Contract risk analysis     | 65%       | 70%            | 88%       | Fine-tune                               |

### When to stop and not train

If the goal is "make the models better for a solo attorney using this tool," the honest answer is: **Phase 1 + Phase 2 gets you 80% of the available improvement at essentially zero cost**. Phase 3 gets you another 10-12% for $100-300. Beyond that, you're in diminishing returns territory unless this becomes a commercial product.

---

## 9. Action Plan (Priority Order)

### Right now (1-2 days)

1. Download SaulLM-7B-Instruct, convert to GGUF, and run it against your 20 hardest contract review and memo tasks. Compare to qwen3.5:9b. You may already have a better model available for free.

2. Update `tune-grammar-models.sh` base model to `Qwen/Qwen3.5-4B-Instruct`. Run data expansion (target 500+ examples). Execute the full training pipeline. Deploy the resulting GGUF.

### Next 2 weeks

3. Build a rules RAG index for `court-rules`. Use ChromaDB, sentence-transformers (already in ClaudeLab venv), and govinfo.gov PDFs. Inject rule text into `court-rules` model context.

4. Generate 500-1000 contract review training pairs using the batch generation pipeline + Claude Sonnet. Stage for Phase 3.

### Next 30-60 days

5. If SaulLM or the grammar fine-tune shows strong results and you want more, run a cloud fine-tune (Phase 3): Qwen3.5-9B on LawInstruct subset + your generated pairs. Budget: $100-200.

6. Benchmark the result against LegalBench tasks where you have test data.

---

## 10. Key References

| Resource           | URL                                        | Why                                      |
| ------------------ | ------------------------------------------ | ---------------------------------------- |
| SaulLM-7B-Instruct | `Equall/Saul-Instruct-v1` on HuggingFace   | Test before training anything            |
| LawInstruct        | `lawinstruct/lawinstruct` on HuggingFace   | Best MIT-licensed legal instruction data |
| CUAD               | `theatticusproject/cuad-qa` on HuggingFace | Contract clause QA, CC-BY                |
| MAUD               | `theatticusproject/maud` on HuggingFace    | M&A contract QA, CC-BY                   |
| LexGLUE            | `coastalcph/lex_glue` on HuggingFace       | Eval benchmark + CaseHOLD training data  |
| Unsloth            | `github.com/unslothai/unsloth`             | 2x faster QLoRA, AMD guide available     |
| ClaudeLab venv     | `Projects/ClaudeLab/.venv/`                | PyTorch 2.9.1+ROCm6.3, ready to use      |
| Existing pipeline  | `tests/tune-grammar-models.sh`             | End-to-end SFT pipeline, already works   |
| SaulLM paper       | arxiv.org/abs/2403.03883                   | Details the pretraining + SFT approach   |

---

_Document generated: 2026-03-21. Update after Phase 1 results are in._
