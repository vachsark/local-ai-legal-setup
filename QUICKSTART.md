# Get Started in 2 Minutes

Everything runs on your machine. Nothing goes to the cloud.

> **New to the command line?** The commands below go into your Terminal app (Mac/Linux) or Command Prompt (Windows). Copy each line exactly, paste it in, and press Enter. The setup wizard will guide you through the rest.

---

## Step 1: Install (one command)

**Linux (Arch/Manjaro):**

Open a Terminal (Ctrl+Alt+T or search "Terminal") and run:

```bash
chmod +x setup.sh && ./setup.sh
```

**macOS (Apple Silicon — M1/M2/M3/M4):**

Open Terminal (search "Terminal" in Spotlight) and run:

```bash
chmod +x setup-mac.sh && ./setup-mac.sh
```

**Windows:**
Double-click **`setup-windows.bat`** — no command line needed.

The installer downloads AI models (~32GB) and sets everything up. Takes 15–30 minutes depending on your internet speed. You will see progress as it downloads.

---

## Step 2: Check some text

Paste text directly, or point it at a file:

```bash
legal-check "Review this clause: The Contractor shall provide services in a timely manner and shall endeavor to complete all deliverables by the dates specified herein, subject to reasonable delays."
```

Or pass a filename (`.txt`, `.pdf`, `.docx`):

```bash
legal-check my-brief.txt
```

---

## Step 3: Ask a question about a document

```bash
legal-check -d your-contract.pdf "What are the key obligations?"
legal-check -d deposition.txt "What did the witness say about the accident?"
```

> **What does `-d` mean?** The `-d` flag means "document" — it tells the tool to load the file and let you ask questions about its contents.

For PDFs, you need `pdftotext` installed (`sudo apt install poppler-utils` on Linux, `brew install poppler` on Mac). The tool will tell you how to get it if it's missing.

---

## Step 4: Have a conversation with a document

```bash
legal-check -i contract.pdf
```

> **What does `-i` mean?** The `-i` flag means "interactive" — the document loads once, and then you can type as many questions as you want without reloading. Type `exit` when done.

This opens an interactive session — load the document once, then ask as many questions as you want:

```
> What are the payment terms?
[answer]
> Is there a non-compete clause?
[answer]
> What happens if either party breaches?
[answer]
> exit
```

---

## Step 5: Open the chat interface

Open **http://localhost:3000** in your browser. (This is a local address — it only works on your machine, not the internet.)

This gives you a ChatGPT-style interface with all the legal models available in the dropdown. Good for longer documents and back-and-forth conversations.

First visit: create a local account (just a username/password for the UI — stays on your machine, no email needed, nothing is sent anywhere).

---

## Other things you can do

**Summarize a document:**

```bash
legal-check -s contract.pdf
legal-check --summarize deposition.txt
```

**Use a specialized model:**

```bash
legal-check -m contract clause.txt     # Contract-focused review
legal-check -m email draft-email.txt   # Quick email polish
legal-check -m plain dense-clause.txt  # Rewrite in plain English
legal-check -m saulm agreement.txt     # SaulLM specialist legal model (30B legal tokens)
```

> **What does `-m` mean?** The `-m` flag means "model" — it selects a specialized AI tuned for that type of work (contracts, emails, plain language, etc.).

**Check from clipboard:**

```bash
legal-check -c                         # Analyze whatever text you just copied
legal-check -c -m email                # Email-specific check from clipboard
```

---

---

## That's it.

> **Important**: AI outputs are a starting point, not a final product. Always review and verify AI-generated text before using it in any client matter, filing, or correspondence. See the ABA Ethics section in [README.md](README.md) for your professional obligations.

For advanced usage — model details, document upload in the browser, voice dictation, prompt templates — see [README.md](README.md).
