# Local AI for Legal Work

Private, local AI that runs entirely on your machine. After initial setup (which downloads models from the internet), all AI inference is local — no API calls, no cloud services.

**Hardware**: AMD RX 9070 XT (16GB VRAM), Arch Linux (Windows script also included)
**Stack**: Ollama (model server) + Open WebUI (chat interface)

---

## Quick Start

### Linux (Arch)

```bash
chmod +x setup.sh
./setup.sh
```

### Windows

**Easiest**: Double-click **`setup-windows.bat`** — it handles everything.

**Alternative** (if you prefer the command line):

```powershell
# Open PowerShell as Administrator, then run:
powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1
```

> **Note**: Don't double-click the `.ps1` file directly — Windows opens it in Notepad instead of running it. Use the `.bat` launcher or the PowerShell command above.

The script installs everything, downloads 3 models + 3 legal presets (~32GB), and starts the chat interface. Takes 15-30 minutes depending on internet speed.

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

## Document Upload (RAG)

Open WebUI has built-in document upload and retrieval. Upload contracts, depositions, or any legal document as a PDF, and the model can reference it during your conversation.

There are two ways to use documents:

### Method 1: In-Chat Upload (Quick, Temporary)

Click the **attachment icon** (paperclip) in the chat input to upload a file directly into the conversation. The model processes it on the spot and can answer questions about it.

- **Scope**: Only available in that specific chat session
- **Best for**: Quick one-off questions about a single document
- **Limitation**: If you start a new chat, you'll need to upload again

### Method 2: Knowledge Collections (Persistent, Recommended)

Knowledge collections are permanent document libraries that you can reference from any chat.

1. **Create a Collection**: Click your name (top-left) → Knowledge → Create. Name it by case or matter (e.g., "Smith v. Jones Discovery" or "ABC Corp Lease Review").

2. **Upload Documents**: Add PDFs, Word docs, or text files to the collection. Each document is automatically split into chunks and indexed for search.

3. **Reference in Chat**: Start a new chat, type `#` and select your collection. The model will search the uploaded documents to answer your questions.

- **Scope**: Available across all chats — just type `#` to reference
- **Best for**: Case files, matters, or any documents you'll reference repeatedly
- **Tip**: Organize by case or matter. You can reference multiple collections in one chat.

### Practical Limits

This setup runs on your local machine, so document capacity depends on your hardware:

| Scale                             | What works well                                                                                |
| --------------------------------- | ---------------------------------------------------------------------------------------------- |
| **1-50 documents per collection** | Great performance. This is the sweet spot for a single matter or case.                         |
| **50-200 documents total**        | Works well across multiple collections. Search stays fast.                                     |
| **200-500 documents total**       | Still functional but search may slow down. Consider splitting into focused collections.        |
| **500+ documents**                | You'll hit practical limits. Embeddings take longer, search accuracy drops as the index grows. |

**For large-scale document review** (thousands of documents, full case databases), you'd need a dedicated document management system or a server with more RAM and storage. This setup is designed for active working documents — the contracts, depositions, and memos you're actively analyzing, not long-term archival.

**Tips for best results**:

- Upload the specific documents relevant to your current work, not everything in the case
- Keep collections focused (e.g., "Smith Depositions" and "Smith Contracts" rather than one giant "Smith" collection)
- Remove documents from collections when you're done with them to keep search fast

### About Chunk Size

Documents are split into 512-token chunks with 75-token overlap. This means:

- A typical contract clause (1-2 paragraphs) stays in one chunk — the model sees the full clause
- Cross-references between adjacent sections are captured in the overlap
- Both keyword and semantic search are used to find relevant chunks (hybrid search)

For short documents (under 5 pages), toggle **Full Context Mode** (in the chat settings) to feed the entire document to the model instead of just matching chunks.

### Scanned PDFs

Standard text-based PDFs work immediately. Scanned PDFs (images of paper) need OCR first — see the optional Docling section below.

---

## Legal Presets

The setup script creates 3 specialized models that appear in the Open WebUI dropdown alongside the base models. Each has a tuned system prompt for a specific legal task.

### contract-reviewer (based on qwen3:14b)

**Use for**: Reviewing contracts, clauses, and agreements

Analyzes obligations, risks, ambiguities, and missing protections. Best paired with RAG — upload a contract to a Knowledge collection, then ask the contract-reviewer to analyze specific sections.

### depo-summarizer (based on gemma3:12b)

**Use for**: Summarizing depositions and witness testimony

Organizes summaries by topic (not chronologically), includes page:line references, flags contradictions and key admissions. Fast enough to process deposition excerpts iteratively.

### memo-drafter (based on mistral-small:24b)

**Use for**: Drafting legal memoranda and analysis

Uses IRAC structure (Issue, Rule, Application, Conclusion) and standard memo format. Slower but produces the most thorough analysis. Best for final work product.

### When to Use Presets vs. Base Models

| Task                              | Use                                               |
| --------------------------------- | ------------------------------------------------- |
| Quick question, general drafting  | Base model (gemma3:12b)                           |
| Contract review with uploaded PDF | contract-reviewer                                 |
| Deposition summary                | depo-summarizer                                   |
| Formal memo or detailed analysis  | memo-drafter                                      |
| Anything else                     | Start with base model, switch to preset if needed |

---

## Tips for Document Upload (RAG)

### Organize by Case or Matter

Create separate Knowledge collections for each case or matter. This keeps searches focused — when you reference `#smith-v-jones`, the model only searches documents in that collection, not your entire upload history.

### Upload Before Chatting

Upload all relevant documents to a collection first, then start your chat. The model can only reference documents that were in the collection when the chat started.

### Use `#` to Scope Your Query

Type `#` in the chat to select which collection to search. You can reference multiple collections in one chat if needed.

### Full Context Mode for Short Documents

For documents under ~5 pages, toggle **Full Context Mode** in chat settings. This sends the entire document to the model instead of just the most relevant chunks. Better for short contracts where every clause matters.

### Break Up Very Large Files

If a document is over 50 pages, consider splitting it into logical sections (e.g., separate the exhibits from the main agreement) and uploading each as a separate file in the same collection. This improves retrieval accuracy.

---

## Demo: Contract Review Walkthrough

Here's a complete walkthrough using the contract-reviewer preset with document upload. Follow along after setup to see everything working.

### 1. Pull Up Open WebUI

Open **http://localhost:3000** and log in (or create your first account).

### 2. Create a Knowledge Collection

- Click your name (bottom-left) → **Knowledge** → **+ Create**
- Name it: `ABC Corp Lease`
- Click **Create**

### 3. Upload a Document

- In the `ABC Corp Lease` collection, click **+ Add Content** → **Upload Files**
- Upload your contract PDF (or any text-based PDF you have handy)
- Wait for the green checkmark — this means it's been chunked and embedded

### 4. Start a Chat with the Contract Reviewer

- Click **New Chat** (top-left)
- In the model dropdown, select **contract-reviewer**
- In the message box, type `#` — a popup appears listing your Knowledge collections
- Select `ABC Corp Lease`

### 5. Ask Questions

Try these prompts (the model will pull relevant chunks from your uploaded contract):

```
What are the key obligations for each party under this agreement?
```

```
Identify any clauses that create open-ended liability exposure.
```

```
Are there any missing protections that are standard in commercial leases
but absent from this document?
```

```
Summarize the termination provisions. Under what conditions can either
party exit early, and what are the penalties?
```

### 6. Try the Other Presets

Switch models in the dropdown to try different tasks on the same document:

- **depo-summarizer**: "Summarize the key terms and dates in this agreement, organized by topic"
- **memo-drafter**: "Draft a memo analyzing whether the indemnification clause in this lease adequately protects our client as tenant"

### What You Should See

- The model's response includes references to specific language from your uploaded document
- Responses from presets are more focused than base models (the system prompt guides the analysis)
- Hybrid search finds relevant sections even if your question uses different words than the contract
- Follow-up questions are fast (RAG context is cached in the system message)

> **Tip**: If the model doesn't seem to reference your document, make sure you selected the collection with `#` before sending your first message. The `#` tag scopes the search to that collection.

---

## Optional: Community Tools

Open WebUI supports community-built tools that extend model capabilities (web search, calculators, document formatters, etc.).

Browse available tools at **https://openwebui.com/tools**

To install a tool:

1. Find a tool on the marketplace
2. Copy its URL
3. In Open WebUI: your name → Settings → Tools → Import from URL
4. Enable the tool in your chat settings

No tools are installed by default. Only install tools you trust — they run locally but execute code within the Open WebUI environment.

---

## Optional: Scanned PDF Support (Docling)

Standard text-based PDFs work with RAG out of the box. But scanned depositions, exhibits, and older documents (image-based PDFs) need OCR to extract text first.

[Docling](https://github.com/DS4SD/docling) handles this. It runs as a separate Docker container:

```bash
docker run -d \
    -p 127.0.0.1:5001:5001 \
    --name docling \
    --restart unless-stopped \
    quay.io/docling-project/docling-serve
```

Then in Open WebUI: **Admin Panel → Settings → Documents → Content Extraction Engine** → set to **Docling** and enter `http://host.docker.internal:5001`.

**Note**: Docling requires ~4GB RAM and takes 30-60 seconds per page for OCR. Only set this up if you regularly work with scanned documents.

---

## After a Restart

Everything is set to auto-start, but if the chat interface isn't loading after a reboot:

### Windows

1. **Check Ollama** — look for the Ollama icon in your system tray (bottom-right, near the clock). If it's not there, open **Ollama** from the Start menu.
2. **Check Docker** — look for the Docker whale icon in your system tray. If it's not there, open **Docker Desktop** from the Start menu. Wait until the whale icon stops animating (this can take 1-2 minutes).
3. **Open the chat** — go to **http://localhost:3000** in your browser.

If localhost:3000 still doesn't load after both are running, open PowerShell and run:

```powershell
docker start open-webui
```

Then refresh the browser.

### Linux

Both services auto-start on boot. If something's not working:

```bash
sudo systemctl start ollama      # start the model server
docker start open-webui          # start the chat interface
```

Then open **http://localhost:3000**.

---

## Managing the System

### Start/Stop

**Windows:**

```powershell
# Start (if not auto-started)
# Open Ollama and Docker Desktop from Start menu, then:
docker start open-webui

# Stop
docker stop open-webui
# Right-click Ollama tray icon -> Quit
```

**Linux:**

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

**Windows:** Docker Desktop -> Settings -> General -> uncheck "Start Docker Desktop when you sign in". For Ollama, remove it from Windows startup apps (Settings -> Apps -> Startup).

**Linux:**

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
# Update Ollama (Arch Linux)
sudo pacman -Syu ollama-rocm

# Update Open WebUI (pin to a specific version for safety)
# Check latest release at: https://github.com/open-webui/open-webui/releases
docker pull ghcr.io/open-webui/open-webui:v0.6.5
docker stop open-webui && docker rm open-webui
docker run -d -p 127.0.0.1:3000:8080 --add-host=host.docker.internal:host-gateway \
    -v open-webui:/app/backend/data --name open-webui --restart always \
    ghcr.io/open-webui/open-webui:v0.6.5
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

- **All inference is local.** After initial setup, Ollama runs models directly on your GPU. No API calls, no cloud services.
- **Initial setup requires internet** to download Ollama, Docker images, and AI models (~31GB). After that, no internet is needed.
- **Both services bind to localhost only** (`127.0.0.1`). They are not accessible from other machines on your network.
- **Open WebUI stores chat history locally** in a Docker volume on your machine.
- **The setup script adds your user to the `docker` group** (with your confirmation). This grants root-equivalent access on the local machine. If this is a concern, use `sudo docker` commands instead.

### Verify Network Security

```bash
# Linux: Verify both services are localhost-only
sudo ss -tlnp | grep -E "11434|3000"
# Should show 127.0.0.1 for both ports

# Windows:
netstat -an | findstr "11434 3000"
# Should show 127.0.0.1 for both ports
```

### Air-Gap After Setup

After the initial model download, you can disconnect from the internet entirely. Everything still works. For maximum security, block all outbound traffic after setup.

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
