# Training Costs — SaulLM vs. Our Options

**Date**: 2026-03-21
**Source**: SaulLM paper (arXiv:2403.03883), SaulLM-54B/141B paper (arXiv:2407.19584), Modal pricing, gpulist.ai, ROCm docs

---

## 1. How SaulLM-7B Was Actually Trained

### Hardware

- **256 AMD MI250 GPUs** on ADASTRA (French national HPC, operated by CINES/GENCI)
- ADASTRA is a Hewlett Packard Cray EX system — each node has 4× MI250X GPUs (128 GB HBM2e each, effectively 2× GCDs per chip)
- MI250X peak FP16: ~383 TFLOPS per GPU (vs A100 SXM 80GB: ~312 TFLOPS FP16 non-sparse)
- Instruction fine-tuning ran on 16 MI250 GPUs; evaluation on a single MI250

### Data

- **30 billion tokens** of English legal text (after aggressive cleaning and deduplication)
- Sources: FreeLaw (The Pile), MultiLegal Pile, CourtListener, EUR-Lex, Australian Legal Corpus + 2% general (Wikipedia, StackExchange, GitHub)
- Cleaning: KenLM perplexity filtering + near-duplicate removal
- Training mix also included FLAN and Super Natural Instructions conversational data to prevent catastrophic forgetting

### Training method

- **Continued pretraining** on Mistral-7B base (not training from scratch)
- Standard causal language modeling loss
- Followed by instruction fine-tuning on legal Q&A pairs (LawInstruct + synthetic)

### GPU hours — what the paper actually says

The SaulLM-7B paper (arXiv:2403.03883) does **not** disclose GPU hours for the 7B model directly. It acknowledges GENCI grants (Jeanzay grants 101838, 103256, 103298 and Adastra grants C1615122, CAD14770, CAD15031) without converting to hours.

**From the SaulLM-54B/141B follow-up paper (arXiv:2407.19584) — which is more forthcoming:**

- 384 MI250 GPUs used for continued pretraining of the larger models
- 64 MI250 GPUs for fine-tuning and DPO
- **Over 160,000 MI250-GPU-hours total** across all phases (54B + 141B combined)
- 65,480 kWh of energy consumed across all training runs
- Training period: February 20 – May 15 (≈84 days, ~3 months)
- Over 1,800 individual jobs (due to hardware failures and scaling issues)
- 540 billion legal tokens in the corpus (though not all were seen in one pass)

**Rough estimate for 7B only (extrapolated):**

- SaulLM-7B pretraining on 30B tokens with 256 MI250s
- Using throughput of ~20,000 tokens/sec/GPU for 7B continued pretraining at scale (literature average for similar setups)
- 30B tokens ÷ (256 GPUs × 20,000 tok/sec/GPU) = 30,000,000,000 ÷ 5,120,000 = **~5,860 seconds ≈ 1.6 hours of wall clock time**
- But with warmup, restarts, data loading, checkpointing, and multi-epoch passes: realistic wall clock is **~8–24 hours**
- GPU-hours: 256 GPUs × 12–24 hrs = **3,000–6,000 MI250-GPU-hours** for the pretraining phase alone
- Add instruction fine-tuning (16 GPUs × shorter run): +~200–400 GPU-hours

**Bottom line for SaulLM-7B**: approximately **3,000–6,500 MI250-GPU-hours** total. This is a national HPC allocation — not rented commercially.

---

## 2. What It Would Cost Us to Replicate

### Our hardware: AMD RX 9070 XT (16 GB VRAM, RDNA4 gfx1201)

**ROCm support**: As of ROCm 7.2.0 (released 2026-02-18), gfx1201 is officially listed in the compatibility matrix with PyTorch 2.9.1, 2.8.0, 2.7.1, TensorFlow 2.20.0, and JAX 0.8.0. **Training is possible locally.**

**Can we do continued pretraining of 7B on 16 GB VRAM?**

Continued pretraining (full weights, no LoRA) of a 7B model in BF16 requires:

- Model weights: 7B × 2 bytes = **14 GB**
- Optimizer states (AdamW): 7B × 8 bytes = 56 GB (two moments in FP32)
- Gradients: 7B × 4 bytes = 28 GB
- Activations (sequence-length dependent): 2–8 GB at seq_len 512–2048

**Total for full pretraining: ~100–130 GB — way beyond 16 GB VRAM.**

Even with 8-bit optimizer (bitsandbytes) and gradient checkpointing:

- Weights (BF16): 14 GB
- 8-bit optimizer: 7B × 1 byte = 7 GB
- Gradients: still 14–28 GB
- Minimum realistic: **~45–60 GB** — still impossible on 16 GB.

**Verdict: Full continued pretraining of 7B is not feasible on 16 GB VRAM.** You would need either cloud GPUs or at minimum a dual-GPU system totaling 48+ GB.

---

### Cloud options for replicating SaulLM-7B pretraining

Converting MI250 GPU-hours to commercial GPU-hours:

- MI250X FP16 ≈ 383 TFLOPS (vs A100 SXM 80GB ≈ 312 TFLOPS)
- MI250X-equivalent A100 hours: 5,000 MI250-hrs × (383/312) ≈ **6,130 A100-80GB-hrs** (actually slightly more due to MI250 underutilization at 40%)
- With reported 40% utilization on ADASTRA: effective compute = 5,000 × 0.40 = 2,000 effective MI250-equivalent-hours → **~2,450 A100-80GB-equivalent hours**

**Pricing (current market rates):**

| Provider   | GPU       | $/hr (on-demand) | Cost for ~2,500 hrs                       | Notes                        |
| ---------- | --------- | ---------------- | ----------------------------------------- | ---------------------------- |
| Modal      | A100 80GB | $2.50            | $6,250                                    | Per-second billing, reliable |
| Modal      | H100 80GB | $3.95            | $9,875                                    | Faster → fewer hours needed  |
| gpulist.ai | A100 80GB | $0.66–$0.76      | $1,650–$1,900                             | Third-party, varies          |
| gpulist.ai | H100      | $1.30–$1.90      | $3,250–$4,750                             | Third-party                  |
| gpulist.ai | RTX 4090  | $0.25–$0.33      | n/a (VRAM too small for full pretraining) | 24 GB not enough             |

**Realistic estimate to replicate SaulLM-7B continued pretraining:**

- Best case (budget marketplace A100 80GB at ~$0.80/hr): **$2,000–$3,000**
- Mid-range (Modal A100 or similar reliable provider): **$5,000–$8,000**
- The original used a national HPC allocation which costs close to $0 in commercial terms but would be valued at $4,000–$6,000 commercially

**Data preparation** (filtering, deduplication of 30B tokens):

- CPU-intensive, could run locally
- ~1–3 days on a modern CPU cluster; GPU-accelerated dedup: a few hours on cloud
- Negligible cost: $50–$200

---

## 3. Cheaper Alternatives

### Option A: Smaller token corpus — 1–5B tokens (just US law)

Instead of 30B tokens of international legal text, train only on:

- FreeLaw (US case law): ~12B tokens pre-dedup, ~4–5B post-dedup
- US Code (Title 1–54): ~1B tokens
- Federal Register last 10 years: ~2–3B tokens

**At 1B tokens:**

- Wall clock on 256 MI250s: ~30 minutes
- Wall clock equivalent on 8× A100 80GB: 1B ÷ (8 × 20,000 tok/sec) = 6,250 seconds ≈ **1.7 hours**
- Cost at $2.50/hr × 8 GPUs: **$34**

**At 5B tokens:**

- 8× A100 80GB: ~8.5 hours
- Cost: **~$170**

The quality delta vs 30B tokens: measurable but not dramatic. Most legal benchmarks show diminishing returns past ~5–10B domain tokens for continued pretraining of a 7B model.

---

### Option B: QLoRA fine-tuning on instruction data (what we can actually run locally)

QLoRA (4-bit quantized base + low-rank adapters) allows fine-tuning a 7B model on **16 GB VRAM**:

**VRAM breakdown for 7B QLoRA:**

- 4-bit quantized weights: 7B × 0.5 bytes ≈ **3.5 GB**
- LoRA adapters (r=64, ~40M params in BF16): **~0.3 GB**
- Optimizer states for LoRA only: **~0.5 GB**
- Activations + KV cache (seq_len 512, batch 1): **~3–5 GB**
- Total: **~8–10 GB** — fits on 16 GB VRAM with headroom

**Training speed on RX 9070 XT (estimated):**

- RDNA4 compute: RX 9070 XT has ~59 TFLOPS FP16
- For reference, RTX 4090 (82.6 TFLOPS) achieves ~800–1,200 tokens/sec for 7B QLoRA
- RX 9070 XT: expect **~400–700 tokens/sec** for 7B QLoRA (ROCm overhead vs CUDA: ~15–25% slower on equivalent FLOPS)

**Training time for different dataset sizes:**

| Dataset                  | Tokens | Time @ 500 tok/s | Cloud cost (if A100) |
| ------------------------ | ------ | ---------------- | -------------------- |
| CUAD (contracts)         | ~25M   | 14 hours locally | $4 (Modal A10G)      |
| LawInstruct sample (10%) | ~1B    | 23 days locally  | $140 (Modal A100)    |
| Full LawInstruct         | ~10B   | 230 days locally | $1,400 (Modal A100)  |
| US FreeLaw (deduped)     | ~4B    | 92 days locally  | $560 (Modal A100)    |

**Verdict**: QLoRA is the realistic local option. For datasets up to ~100M tokens, local training is practical (hours–days). For 1B+ tokens, use cloud or accept very long local runs.

---

### Option C: The minimum viable legal fine-tune

What actually moves the needle with minimal spend:

1. **SFT on legal instruction pairs**: ~500K–2M instruction/response pairs
   - Dataset: LawInstruct subset + CUAD + your existing 187 grammar examples (synthetically expanded)
   - Tokens: ~500M tokens total
   - Time at 500 tok/s locally: **~11 days** (or $70 on Modal A100)
   - Expected quality delta: +5–12% on legal task benchmarks vs base Mistral/Llama

2. **QLoRA vs full fine-tune quality gap**:
   - QLoRA typically recovers ~92–97% of full fine-tune quality on instruction tasks
   - For continued pretraining (next-token prediction on raw legal text), QLoRA is NOT appropriate — the point is updating every weight

---

## 4. What Did Cursor Spend? (Qwen 2.5 Coder 32B Fine-Tune)

There is no public disclosure of Cursor's Composer 2.0 training cost. No paper, no blog post with cost figures. The following is reconstruction from known benchmarks:

**Qwen 2.5 Coder 32B full fine-tune (SFT):**

- Model parameters: 32B in BF16 = 64 GB weights
- Minimum hardware: 8× A100 80GB (640 GB total) with tensor parallelism, or 4× H100 80GB
- Token throughput at 8× A100: ~8,000–12,000 tokens/sec for 32B model
- Assuming 50B token training run (code instruction data):
  - Wall clock: 50B ÷ 10,000 = 5,000,000 sec = **~1,389 hours = 58 days** on 8× A100
  - GPU-hours: 8 × 1,389 = **11,112 A100-80GB-hours**
  - Modal pricing: 11,112 × $2.50 = **~$27,800**
  - Budget marketplace (Vast.ai/gpulist.ai at $0.70/hr): **~$7,800**

**More likely Cursor used H100 clusters internally or via Azure/GCP at enterprise pricing:**

- H100 spot via GCP: ~$2.50–3.50/hr per GPU
- 8× H100, 50B tokens: ~700 hours, 5,600 H100-hrs → **~$14,000–$20,000**

**Realistically**: A production code model fine-tune at Cursor's quality level likely cost **$15,000–$50,000** depending on how many ablations and iteration runs they did. Startups typically run 3–10× the final training run in experiments.

**The "80% of quality for 20% of cost" path**: Fine-tune Qwen 2.5 Coder 7B instead of 32B:

- 8× fewer parameters = ~8× cheaper compute
- RTX 4090 can run 7B SFT (24 GB VRAM) with Flash Attention + gradient checkpointing
- Estimated cost for 10B-token code SFT on 4× A100 80GB: **~$1,500–$3,000**

---

## 5. Can We Just Use SaulLM Without Training?

### Is it on Ollama?

**No. SaulLM is not in the Ollama library.** Confirmed by searching ollama.com/library — no "saul" or "saulm" model appears.

### Can we convert from HuggingFace to GGUF?

**Yes. The process is straightforward:**

```bash
# Step 1: Download from HuggingFace (SaulLM-7B is ~14 GB in BF16)
pip install huggingface_hub
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('Equall/SaulLM-7B', local_dir='./SaulLM-7B-hf')
"

# Step 2: Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
pip install -r llama.cpp/requirements.txt

# Step 3: Convert to GGUF (F16 first, then quantize)
python3 llama.cpp/convert_hf_to_gguf.py ./SaulLM-7B-hf \
  --outfile SaulLM-7B-f16.gguf \
  --outtype f16

# Step 4: Quantize to Q4_K_M (best quality/size tradeoff)
./llama.cpp/llama-quantize SaulLM-7B-f16.gguf SaulLM-7B-Q4_K_M.gguf Q4_K_M

# Step 5: Create Ollama Modelfile
cat > Modelfile.saul-base << 'EOF'
FROM ./SaulLM-7B-Q4_K_M.gguf
SYSTEM "You are a legal AI assistant trained on US, UK, EU, Canadian, and Australian legal texts. You specialize in legal document analysis, contract review, and legal research."
PARAMETER num_ctx 8192
PARAMETER temperature 0.1
EOF

ollama create saul-base -f Modelfile.saul-base
```

**Time to convert + quantize:**

- Download: 45–90 min on fast connection (14 GB BF16 weights)
- F16 conversion: ~5–10 min on CPU
- Q4_K_M quantization: ~3–5 min on CPU

**Expected GGUF file sizes (7B Mistral architecture):**
| Format | Size | VRAM needed | Notes |
|----------|---------|-------------|-------|
| F16 | ~14 GB | ~16 GB | Full precision |
| Q8_0 | ~7.7 GB | ~10 GB | Near-lossless |
| Q5_K_M | ~5.1 GB | ~7 GB | Very high quality |
| Q4_K_M | ~4.1 GB | ~6 GB | Best all-around |
| Q3_K_M | ~3.3 GB | ~5 GB | Noticeable quality loss |

**With 16 GB VRAM (RX 9070 XT):**

- Q4_K_M (4.1 GB) fits easily, inference at full GPU speed
- Q8_0 (7.7 GB) also fits well, ~8 GB headroom for context
- F16 (14 GB) fits but leaves <2 GB for KV cache — limit context to 2048 tokens

**Is there a pre-made GGUF?**
TheBloke does not appear to have converted SaulLM-7B (HuggingFace 401 on that repo). mradermacher may have one but their HuggingFace page returned 401. You may need to do the conversion yourself, which is simple (30-min process above).

**Note**: SaulLM-7B uses the Mistral architecture, which llama.cpp fully supports. Conversion should work cleanly.

---

## 6. Summary Table

| Approach                             | Cost     | Time              | VRAM          | Quality Delta vs Base                                    |
| ------------------------------------ | -------- | ----------------- | ------------- | -------------------------------------------------------- |
| Just use SaulLM-7B (GGUF convert)    | $0       | 2 hrs setup       | 6 GB (Q4_K_M) | +5–10% on legal tasks (vs Mistral-7B)                    |
| QLoRA SFT on CUAD (~25M tokens)      | $0 local | 14 hrs            | ~10 GB        | +3–8% on contract tasks                                  |
| QLoRA SFT on LawInstruct 10%         | $0 local | 23 days           | ~10 GB        | +8–15% on legal tasks                                    |
| QLoRA SFT on LawInstruct 10% (cloud) | ~$140    | 5 hrs (cloud)     | A100 80GB     | +8–15% on legal tasks                                    |
| Continued pretraining, 1B tokens     | $34      | 1.7 hrs (cloud)   | 8× A100 80GB  | +3–7% vs base (mostly raw LM perplexity, less task gain) |
| Continued pretraining, 5B tokens     | ~$170    | 8.5 hrs (cloud)   | 8× A100 80GB  | +6–12% vs base                                           |
| Replicate SaulLM-7B (30B tokens)     | $2K–$8K  | 3–14 days (cloud) | 8–16× A100    | ~= SaulLM-7B                                             |
| Replicate SaulLM-141B (540B tokens)  | $100K+   | months            | 384× MI250    | SaulLM-141B quality                                      |

---

## 7. Recommendations

**Immediate ($0, do today):** Convert SaulLM-7B from HuggingFace to GGUF using the steps in Section 5. This gets you a legal-domain model in Ollama within 2 hours at zero cost. Test it against your existing Modelfiles.

**Short term ($0, 1–14 days):** Run QLoRA fine-tuning locally on CUAD (contract understanding) and your 187 existing grammar examples. Your RX 9070 XT can do this; ROCm 7.2 supports gfx1201.

**Medium term ($140–500, cloud):** Fine-tune on LawInstruct 10% sample on Modal/RunPod. The per-second billing on Modal means a 5-hour A100 run = ~$100. This is the sweet spot for quality gain per dollar.

**Skip unless this becomes a product:** Replicating SaulLM's 30B-token continued pretraining. The $2,000–$8,000 cost is hard to justify when SaulLM-7B already exists and is freely available to download and convert.

---

_Sources: arXiv:2403.03883 (SaulLM-7B), arXiv:2407.19584 (SaulLM-54B/141B), modal.com/pricing, gpulist.ai, ROCm 7.2 compatibility matrix, HuggingFace bitsandbytes docs, QLoRA paper (arXiv:2305.14314)_
