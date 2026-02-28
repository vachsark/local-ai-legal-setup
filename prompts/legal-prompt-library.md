# Legal Prompt Library

20 curated prompt templates organized by task type. Copy-paste ready for Open WebUI with recommended model/preset for each.

---

## Contract Review (5 prompts)

### 1. Full Contract Risk Assessment

**Model**: contract-reviewer | **Expect**: Structured risk analysis with clause-by-clause breakdown

```
Review this contract and provide a risk assessment. For each significant clause:
1. Identify the obligation and which party bears it
2. Rate the risk (LOW / MEDIUM / HIGH / CRITICAL)
3. Explain the risk in plain language
4. Suggest specific revision language if the risk is HIGH or CRITICAL

Focus on: indemnification, liability caps, termination, IP ownership, and dispute resolution.

[paste contract or reference uploaded document with #]
```

### 2. One-Sided Clause Detection

**Model**: contract-reviewer | **Expect**: List of imbalanced provisions with suggested revisions

```
Analyze this contract from [OUR CLIENT'S] perspective as the [PARTY ROLE, e.g., "licensee" or "tenant"]. Identify every clause that disproportionately favors the other party. For each:

- Quote the clause
- Explain why it's one-sided
- Propose balanced alternative language
- Rate how common this language is in similar agreements (standard / aggressive / unusual)

[paste contract]
```

### 3. Missing Provisions Check

**Model**: clause-identifier | **Expect**: JSON inventory including missing_clauses section

```
Produce a complete clause inventory for this [AGREEMENT TYPE, e.g., "software license agreement"]. After cataloging what's present, identify all standard clauses that are MISSING and explain why each matters.

Pay special attention to: force majeure, data protection, audit rights, insurance requirements, and survival provisions.

[paste contract]
```

### 4. Amendment Impact Analysis

**Model**: contract-reviewer | **Expect**: Change-by-change impact assessment

```
This amendment modifies an existing agreement. For each change:
1. Quote the original provision (if available) and the amended language
2. Explain what changed in practical terms
3. Assess whether this helps or hurts [OUR CLIENT]
4. Flag any interaction effects with unchanged provisions

AMENDMENT:
[paste amendment text]

ORIGINAL AGREEMENT CONTEXT:
[paste relevant original sections, or reference with #]
```

### 5. Renewal/Termination Audit

**Model**: contract-reviewer | **Expect**: Deadline summary with action items

```
Extract ALL renewal, termination, and expiration provisions from this agreement. For each, provide:
- The specific deadline or notice period
- What action is required and by whom
- The consequence of missing the deadline
- Whether it auto-renews and on what terms

Organize chronologically from soonest to latest deadline.

[paste contract]
```

---

## Deposition / Testimony (3 prompts)

### 6. Topic-Organized Deposition Summary

**Model**: depo-summarizer | **Expect**: Topic-organized summary with page:line references

```
Summarize this deposition testimony organized by topic, not chronologically. For each topic:
- Key statements and admissions (with page:line references if visible in the text)
- Contradictions with other statements in the same deposition
- Areas where the witness was evasive or non-responsive
- Objections made and their stated grounds

Keep the summary factual — do not characterize testimony as helpful or harmful.

[paste deposition excerpt]
```

### 7. Witness Contradiction Finder

**Model**: depo-summarizer | **Expect**: Side-by-side contradiction comparisons

```
Review this testimony for internal contradictions. Compare statements the witness made at different points about the same topic. For each contradiction:
- Quote both statements with their locations
- Explain the factual conflict
- Note whether the witness was corrected or acknowledged the inconsistency

Also flag statements that are technically consistent but misleading in context.

[paste testimony]
```

### 8. Cross-Examination Prep

**Model**: mistral-small:24b | **Expect**: Question sequences targeting weaknesses

```
Based on this deposition testimony, prepare cross-examination questions that target:
1. Internal contradictions (identified above or in the text)
2. Gaps in the witness's knowledge or memory
3. Statements that conflict with [SPECIFIC DOCUMENTS OR FACTS]
4. Areas where the witness made absolute claims that can be challenged

For each question sequence, note the impeachment source and the specific admission you're driving toward.

[paste testimony excerpt and relevant facts]
```

---

## Memo Drafting (3 prompts)

### 9. Full IRAC Memorandum

**Model**: memo-drafter | **Expect**: Complete memo in standard format with IRAC analysis

```
Draft a legal memorandum analyzing the following issue:

QUESTION: [State the legal question]

FACTS:
[Provide relevant facts]

JURISDICTION: [State/Federal]

Use standard memo format (Question Presented, Short Answer, Statement of Facts, Discussion with IRAC structure, Conclusion). In the Discussion, address the strongest counterargument and explain why our position is stronger.

Note: Do not fabricate case citations. Describe applicable legal principles and note that specific authorities require independent verification.
```

### 10. Multi-Issue Analysis

**Model**: memo-drafter | **Expect**: Separate IRAC analysis for each issue

```
Analyze the following [NUMBER] legal issues arising from the same fact pattern. For each issue, provide a separate IRAC analysis.

FACTS:
[Common fact pattern]

ISSUES:
1. [First legal question]
2. [Second legal question]
3. [Third legal question]

Address each issue independently, but note where the analysis of one issue affects another. Prioritize issues by likelihood of success.
```

### 11. Opposing Argument Anticipation

**Model**: memo-drafter | **Expect**: Balanced analysis with opponent's best arguments

```
We represent [CLIENT] in [MATTER TYPE]. Our primary argument is [STATE ARGUMENT].

Draft the strongest possible counterarguments the opposing party could make. For each:
- State the counterargument clearly
- Identify the legal basis
- Assess its strength (weak / moderate / strong)
- Draft our rebuttal

Be genuinely adversarial in constructing counterarguments — don't create strawmen.

CONTEXT:
[Relevant facts and background]
```

---

## Clause Analysis (3 prompts)

### 12. Indemnification Deep Dive

**Model**: contract-reviewer | **Expect**: Detailed breakdown of indemnification scope and gaps

```
Analyze this indemnification provision in detail:

1. Who indemnifies whom (direction)?
2. What triggers indemnification (scope of covered claims)?
3. Are there any carve-outs or exceptions?
4. Is there a cap? How does it interact with the limitation of liability?
5. Does it cover attorneys' fees and costs?
6. Is there a duty to defend or just indemnify?
7. What is the notice requirement?
8. Does it survive termination?

Flag any gaps or ambiguities that could be exploited.

[paste indemnification clause and related provisions]
```

### 13. Force Majeure Adequacy

**Model**: contract-reviewer | **Expect**: Assessment against modern risks

```
Evaluate this force majeure clause against modern risk scenarios:

- Does it cover pandemics/epidemics explicitly?
- Does it cover cyberattacks/ransomware?
- Does it cover supply chain disruptions?
- Does it cover government orders/sanctions?
- Is the list exclusive ("limited to") or illustrative ("including but not limited to")?
- What is the notice requirement?
- What are the consequences (suspension, termination, both)?
- Is there a duration limit before the other party can terminate?

Compare to current market standard for [INDUSTRY/AGREEMENT TYPE].

[paste clause]
```

### 14. Non-Compete Enforceability Screen

**Model**: mistral-small:24b | **Expect**: Factor-by-factor analysis with jurisdiction notes

```
Evaluate this non-compete/restrictive covenant for likely enforceability:

JURISDICTION: [State]
EMPLOYEE ROLE: [Title/responsibilities]
INDUSTRY: [Industry]

Analyze each factor:
1. Geographic scope — reasonable?
2. Duration — within accepted range for this jurisdiction?
3. Scope of restricted activities — narrowly tailored?
4. Consideration — adequate for the jurisdiction (especially if post-employment)?
5. Hardship to employee vs. employer's legitimate interest

Note: Legal standards vary significantly by state. This analysis provides a framework — verify current law in the specific jurisdiction.

[paste restrictive covenant]
```

---

## Writing Review (3 prompts)

### 15. Brief Proofreading

**Model**: legal-reviewer | **Expect**: Organized feedback by severity (critical, style, consistency)

```
Proofread this brief for filing. Apply the full 7-point checklist:
1. Grammar and mechanics (subject-verb, tense, parallel structure)
2. Legal vocabulary (preserve terms of art and Latin phrases)
3. Defined term consistency (capitalization, usage matches definition)
4. Citation formatting (flag for verification, do NOT auto-correct)
5. Tone and formality (shall/may/must/will usage)
6. Readability (sentence length, passive voice, nested qualifications)
7. Document-type standards for [BRIEF TYPE, e.g., "motion for summary judgment"]

Organize output into: CRITICAL ISSUES, STYLE IMPROVEMENTS, CONSISTENCY NOTES, CITATIONS TO VERIFY.

[paste brief]
```

### 16. Tone Adjustment

**Model**: legal-reviewer | **Expect**: Specific revision suggestions with explanations

```
Review this [DOCUMENT TYPE] for tone. The target audience is [AUDIENCE, e.g., "a sophisticated business client" or "a federal judge"]. The appropriate register is [REGISTER, e.g., "formal but accessible" or "highly formal"].

Flag language that is:
- Too informal for the audience
- Unnecessarily complex (could be simpler without losing precision)
- Passive where active voice would be stronger
- Hedging where confidence is warranted (or vice versa)

For each flag, provide the original and a suggested revision.

[paste text]
```

### 17. Plain Language Translation

**Model**: gemma3:12b | **Expect**: Readable rewrite preserving legal accuracy

```
Rewrite this legal text in plain language that a non-lawyer can understand. Rules:
- Maintain legal accuracy — do not change the meaning
- Where a legal term of art is essential, keep it but define it in parentheses
- Break long sentences into shorter ones
- Replace passive voice with active voice where possible
- Target an 8th-grade reading level

After the rewrite, list any legal nuances that were simplified and might need attorney explanation.

ORIGINAL:
[paste legal text]
```

---

## General (3 prompts)

### 18. Issue Spotter

**Model**: mistral-small:24b | **Expect**: Comprehensive issue list with preliminary analysis

```
Review this fact pattern and identify all potential legal issues. For each issue:
1. Name the legal claim or defense
2. State the applicable standard or test
3. Identify which facts support and undermine each element
4. Rate the overall strength (weak / moderate / strong)
5. Note any additional facts needed to fully assess

Be comprehensive — include even issues that may be marginal.

JURISDICTION: [State/Federal]
AREA OF LAW: [e.g., employment, contract, tort]

FACTS:
[paste fact pattern]
```

### 19. Timeline Builder

**Model**: gemma3:12b | **Expect**: Chronological timeline with source references

```
Extract a chronological timeline from these documents. For each event:
- Date (exact if available, approximate if not)
- What happened
- Who was involved
- Source document and page/section reference
- Legal significance (if apparent)

Flag any gaps where important events likely occurred but aren't documented.
Flag any date inconsistencies between documents.

[paste documents or reference uploaded collection with #]
```

### 20. Demand Letter Framework

**Model**: memo-drafter | **Expect**: Structured letter draft with factual and legal bases

```
Draft a demand letter framework for the following situation:

FROM: [Client — party role]
TO: [Recipient — party role]
RE: [Subject matter]

FACTS:
[Key facts supporting the claim]

DEMANDS:
[What the client wants]

Include these sections:
1. Factual background (professional, not adversarial)
2. Legal basis for each demand (describe applicable principles — do not fabricate citations)
3. Specific demands with deadlines
4. Consequences of non-compliance
5. Professional closing with contact information

Tone: Firm but professional. Not threatening.
```

---

## Usage Tips

- **Upload documents first** — Create a Knowledge collection, upload your files, then reference with `#` in chat
- **Iterate** — First response not ideal? Say "Expand on point 3" or "Too formal, adjust tone"
- **Verify everything** — These prompts instruct models not to fabricate citations, but always verify independently
- **Combine prompts** — Use the timeline builder first, then feed the timeline into the issue spotter
- **Switch models** — Start with gemma3:12b for speed; re-run with mistral-small if quality isn't sufficient
