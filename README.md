# Local AI for Legal Work

Private, local AI that runs entirely on your machine. No data leaves your computer — ever.

**Hardware**: AMD RX 9070 XT (16GB VRAM), Arch Linux
**Stack**: Ollama (model server) + Open WebUI (chat interface)

---

## Quick Start

```bash
chmod +x setup.sh
./setup.sh
```

The script installs everything, downloads 3 models (~31GB), and starts the chat interface. Takes 15-30 minutes depending on internet speed.

When done, open **http://localhost:3000** in your browser.

First visit: create a local account (just a username/password for the UI — stays on your machine, no email needed).

---

## The Models

You have 3 models. Each has different strengths — use the right one for the job.

### gemma3:12b — The Workhorse

**Speed**: ~50 tokens/second | **Best for**: Daily tasks

Use this for most work. It's fast and handles the bread-and-butter tasks well:

- Summarizing depositions, transcripts, case documents
- Drafting first-pass memos and correspondence
- Extracting key terms and dates from contracts
- Reformatting and organizing notes
- Explaining legal concepts in plain language (for clients)

### qwen3:14b — The Analyst

**Speed**: ~40 tokens/second | **Best for**: Structured analysis

Better than gemma3 at following complex instructions and producing structured output:

- Comparing two contract versions side-by-side
- Building argument outlines with supporting points
- Analyzing fact patterns against legal elements
- Generating checklists (due diligence, compliance, discovery)
- Structured Q&A preparation

### mistral-small:24b — The Heavy Hitter

**Speed**: ~25 tokens/second | **Best for**: Complex reasoning

Slowest but smartest. Use when quality matters more than speed:

- Complex legal analysis requiring multi-step reasoning
- Drafting detailed legal memoranda
- Evaluating strengths/weaknesses of legal positions
- Synthesizing information from multiple sources
- Any task where gemma3 or qwen3 gave a weak answer

---

## Example Prompts for Legal Work

### Contract Review

```
Review the following contract clause and identify:
1. Key obligations for each party
2. Potential risks or ambiguities
3. Missing protections that should be added
4. Any unusual or non-standard terms

[paste clause here]
```

### Deposition Summary

```
Summarize the following deposition testimony. For each topic discussed, provide:
- The key admissions or statements made
- Any contradictions with prior statements
- Questions that were objected to and the grounds

Keep the summary factual. Do not editorialize or add legal conclusions.

[paste transcript excerpt]
```

### Legal Research Starting Point

```
I need to research [legal issue] in [jurisdiction]. Outline:
1. The key legal standard/test that applies
2. The main elements that must be proven
3. Common defenses or counterarguments
4. The type of cases/statutes I should search for

Note: I will verify all citations independently. Provide the framework, not specific case names.
```

### Memo Drafting

```
Draft a legal memorandum analyzing [issue]. Use this structure:

QUESTION PRESENTED: [restate the issue]
SHORT ANSWER: [1-2 sentence conclusion]
FACTS: [summarize from what I provide below]
DISCUSSION: [analysis with IRAC structure]
CONCLUSION: [recommendation]

Context: [paste your facts and relevant information]
```

### Contract Clause Drafting

```
Draft a [type of clause, e.g., "limitation of liability clause"] for a
[type of agreement] between [parties]. It should:
- [specific requirement 1]
- [specific requirement 2]
- [specific requirement 3]

Jurisdiction: [state/country]
Governing law preference: [if any]
```

### Document Comparison

```
Compare these two versions of [document type]. For each difference:
1. Quote the original language
2. Quote the revised language
3. Explain the practical impact of the change
4. Flag if the change favors one party over the other

VERSION 1:
[paste]

VERSION 2:
[paste]
```

### Plain Language Translation

```
Rewrite the following legal text in plain language that a non-lawyer client
can understand. Maintain accuracy but eliminate jargon. Where a legal term
is essential, define it in parentheses.

[paste legal text]
```

---

## Important Limitations

Read this section carefully. These limitations are real and matter for legal work.

### Accuracy

These models are significantly less accurate than GPT-4 or Claude. Specifically:

- **They invent case citations.** If you ask for cases, they will confidently cite cases that don't exist. NEVER include an AI-generated citation in any filing or document without independently verifying it in Westlaw/Lexis/etc.
- **They can misstate legal standards.** The model may describe a legal test incorrectly or mix up elements from different tests. Always verify against authoritative sources.
- **They hallucinate details.** Dates, numbers, names, and statutory references may be fabricated. Treat all specific facts as unverified.

**Rule of thumb**: Use these models for _structure and drafting_, not for _legal authority_. Let the AI organize your thoughts and generate first drafts. You provide the legal accuracy.

### Context Window

The models can process roughly 12,000-16,000 words at a time. This means:

- A 5-page contract: fits easily
- A 20-page brief: fits, but quality may degrade toward the end
- A 50-page deposition transcript: too long — break it into sections
- A full case file: way too long — feed documents one at a time

**Tip**: If a document is too long, break it into logical sections and process each one separately. Then ask the model to synthesize your section-by-section summaries.

### What These Models Do Well

- Drafting from your outline (you provide structure, AI fills in prose)
- Summarizing documents you've already read (sanity check your understanding)
- Generating checklists and frameworks
- Reformatting and organizing information
- Brainstorming arguments and counterarguments
- Plain language translation of legal text
- First-pass review to flag issues for your deeper analysis

### What These Models Do Poorly

- Legal research (they can't access databases and will fabricate sources)
- Final-quality legal writing (still needs significant editing)
- Nuanced jurisdictional analysis
- Multi-step reasoning chains (they lose the thread)
- Anything requiring current case law (training data has a cutoff)
- Mathematical calculations in damages analysis

---

## Tips for Best Results

### Be Specific

Bad: "Review this contract"
Good: "Review the indemnification clause in Section 8 and identify any gaps in coverage for [specific risk]"

### Provide Context

Bad: "Is this enforceable?"
Good: "Under California law, is this non-compete clause enforceable given that the employee is a software engineer and the restriction is 2 years / 50 miles?"

### Use the Right Model

Start with gemma3:12b for speed. If the answer isn't good enough, re-ask with mistral-small. Don't wait 2x as long for every question when the fast model handles 80% of tasks fine.

### Break Up Long Documents

Instead of pasting a 30-page document and saying "summarize this," break it into sections:

1. "Summarize Section 1-3 (Definitions and Scope)" [paste]
2. "Summarize Section 4-7 (Obligations and Performance)" [paste]
3. "Now synthesize these summaries into an executive overview" [paste both summaries]

### Ask for Structure

The models are better when you tell them exactly what format you want:

```
Analyze this clause. Use this format:
- PLAIN MEANING: [what it says in simple terms]
- RISK TO CLIENT: [potential problems]
- SUGGESTED REVISION: [improved language]
- PRIORITY: [high/medium/low]
```

### Iterate

First response not great? Don't start over. Say:

- "Expand on point 3 — that's the key issue"
- "Too formal. Rewrite in a more conversational tone for the client"
- "You missed [X]. Add analysis of that factor"

---

## Managing the System

### Start/Stop

```bash
# Models (Ollama)
sudo systemctl start ollama     # start
sudo systemctl stop ollama      # stop
sudo systemctl status ollama    # check status

# Chat UI (Open WebUI)
docker start open-webui         # start
docker stop open-webui          # stop
```

Both are set to auto-start on boot. To disable auto-start:

```bash
sudo systemctl disable ollama
docker update --restart no open-webui
```

### Add More Models

Browse models at https://ollama.com/library — then:

```bash
ollama pull modelname:size
```

The model appears in the Open WebUI dropdown automatically.

### Update

```bash
# Update Ollama
sudo pacman -Syu ollama-rocm   # or: curl -fsSL https://ollama.com/install.sh | sh

# Update Open WebUI
docker pull ghcr.io/open-webui/open-webui:main
docker stop open-webui && docker rm open-webui
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway \
    -v open-webui:/app/backend/data --name open-webui --restart always \
    ghcr.io/open-webui/open-webui:main
```

### Check GPU Usage

```bash
# See if models are using the GPU
ollama ps                              # shows loaded models and VRAM usage

# Monitor GPU in real-time
watch -n 1 cat /sys/class/drm/card*/device/gpu_busy_percent
```

---

## Troubleshooting

### "Ollama is not running"

```bash
sudo systemctl start ollama
journalctl -u ollama --no-pager -n 20   # check for errors
```

### Open WebUI shows "Connection failed"

Make sure Ollama is running first. Open WebUI connects to it at `http://host.docker.internal:11434`.

```bash
# Check Ollama is responding
curl http://localhost:11434/api/tags

# Check Open WebUI container
docker logs open-webui --tail 20
```

### Model is very slow

If you're getting ~5 tokens/second instead of ~50, the model may be running on CPU instead of GPU:

```bash
# Check if GPU is being used
ollama ps    # VRAM column should show usage

# Verify Vulkan is available
vulkaninfo --summary 2>/dev/null | grep -i "radv\|driver"

# Restart Ollama to pick up GPU
sudo systemctl restart ollama
```

### Response cuts off mid-sentence

The model hit its output token limit. In Open WebUI, go to Settings (gear icon) > Models > set "Max Tokens" higher (try 4096).

### Model gives nonsensical output

Some prompts are too long for the context window. Try:

- Shortening your input
- Breaking the document into smaller pieces
- Using a simpler, more direct prompt

---

## Privacy & Security Notes

- **All processing is local.** Ollama runs models directly on your GPU. No API calls, no cloud services, no telemetry.
- **Open WebUI stores chat history locally** in a Docker volume on your machine. It does not phone home.
- **No internet required** after initial setup. You can disconnect from the internet and everything still works.
- **To verify**: Run `sudo ss -tlnp | grep ollama` — Ollama only listens on `127.0.0.1:11434` (localhost). It is not accessible from other machines on your network.
- **To fully air-gap**: After setup, you can block all outbound traffic and the system will continue to function.

---

## Uninstall

To completely remove everything:

```bash
# Remove Open WebUI
docker stop open-webui && docker rm open-webui
docker volume rm open-webui

# Remove Ollama and models
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo pacman -R ollama-rocm   # or ollama
rm -rf ~/.ollama             # removes all downloaded models
sudo rm -rf /etc/systemd/system/ollama.service.d/
sudo systemctl daemon-reload
```
