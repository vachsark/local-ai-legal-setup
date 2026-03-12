# Legal Grammar Checker — Research Summary

Research conducted 2026-03-11 via 9 parallel research agents. This document indexes the findings. Full agent transcripts are in `/tmp/` (session-ephemeral) — key content has been incorporated into the training data generator and system prompts.

## Sources Covered

### Agent 1: Legal Writing Errors (Bryan Garner, bar associations)

- 43 specific error patterns with bad→good examples
- Categories: grammar/syntax, word choice, legalese, punctuation, contract drafting, Bluebook citations, real-world disasters
- Highlights: "sea sponge" find-replace, "PROBABLY NOT WORTH ARGUING?" filed note, squinting modifiers

### Agent 2: Legal Document Templates (10 types)

- Demand letters, motion briefs, client emails, discovery responses, settlement agreements, legal memos, cease & desist, court orders, deposition summaries, engagement letters
- Each: structure, 2-3 realistic snippets, common errors, tone guidelines

### Agent 3: Grammar Style Guide Rules (47 rules)

- Modal verbs (shall/may/must/will) — 5 rules
- Active voice and sentence construction — 4 rules
- Legalese to avoid — 7 rules (said, aforementioned, hereinafter, etc.)
- Legal doublets and triplets — comprehensive list with cut/keep guidance
- Defined term conventions — 5 rules
- Punctuation — 3 rules (Oxford comma, semicolons, em dashes)
- Ambiguity rules — 3 rules (and/or, efforts standards, tabulation)
- Gender-neutral language — 4 rules
- Numbers — 3 rules
- Paragraph structure — 3 rules (CREAC, topic sentences, party names)
- Word choice — 7 rules (prior to→before, pursuant to→under, etc.)
- Citations — 2 rules

### Agent 4: Legal NLP Datasets & Tools

- Key finding: NO existing GEC dataset for legal writing (all target ESL learner errors)
- Corpora: Pile of Law (256GB), CUAD (510 contracts), LegalBench (162 tasks)
- Tools: BriefCatch (11K suggestions), WordRake (50K algorithms), PerfectIt (13K terms)
- Framework: Vale prose linter could be extended with legal rules
- GEC datasets: CoNLL-2014, BEA-2019, C4_200M (domain-mismatched but useful for architecture)

### Agent 5: Court-Published Style Guides

- FRAP Rules 28/32, Supreme Court Rule 33 (Century font family only)
- 7th Circuit typography guide (warns against Times New Roman)
- State rules: California (14K words, 13pt min), New York (14pt body), Texas (50 pages)
- Judicial opinions criticizing bad writing: Bradshaw v. Unity Marine, Judge Kozinski "The Wrong Stuff"
- Sanction cases: fees reduced, appeals dismissed, costs doubled for poor writing
- Appellate writing techniques from Scalia/Garner, Posner, Wydick

### Agent 6: Contract Drafting Errors (Ken Adams / MSCD)

- MSCD language categories: obligation, discretion, prohibition, condition, declaration, policy
- Famous cases: O'Connor v. Oakhurst Dairy ($5M comma), Rogers v. Bell Aliant ($2.13M comma)
- "Including" + ejusdem generis traps
- Efforts standards: best/reasonable/commercially reasonable — courts split on interpretation
- Cross-reference rot: one contract had 88 stale references
- Boilerplate errors: force majeure gaps, indemnity/cap conflicts, survival clause omissions

### Agent 7: Email/Letter Legal Writing

- Privilege traps: CC'ing doesn't create privilege, forwarding chains, "on advice of counsel"
- Settlement binding risks: emails can form contracts under UETA/E-SIGN
- "Without prejudice" and "subject to contract" — when to use
- Meet-and-confer requirements
- "Govern yourself accordingly" — universally mocked cliche
- Engagement letter malpractice traps: vague scope, retainer confusion, no-guarantee disclaimer

### Agent 8: Plain Language Legal Rules

- Federal Plain Language Guidelines + Plain Writing Act 2010
- Wydick's "Plain English for Lawyers" — working words vs glue words
- 30+ legalese→plain mappings in 5 categories (here-/there-/where- compounds, ceremonial, formal words, doublets, wordy phrases)
- Terms of art that MUST be preserved: 25+ terms with why
- Readability targets: consumer contracts at 8th grade, briefs at 12th grade
- International standards: UK Crystal Mark, Australia Consumer Law, Canada accessibility

### Agent 9: Jurisdiction-Specific Rules

- Federal vs state writing conventions
- Practice-area writing: employment, real estate, IP/patent, family, criminal, immigration, bankruptcy
- Bluebook deep dive: Id. rules, supra rules, signal usage (15 common errors from Fordham)
- Parenthetical format: present participle, no capital, no period
- Writing by audience: judges vs clients vs opposing counsel vs regulators
- E-filing: CM/ECF format, hyperlink standards, NextGen citation recognition

## How This Research Was Used

1. **Modelfile system prompts** — Comprehensive error checklists derived from Garner, Adams, plain language movement
2. **Training data generator** — 38 samples across 10 doc types, 103 error types, informed by all 9 research streams
3. **Gold-standard training prompt** — 200+ line system prompt for Claude Sonnet covering every error category
4. **Eval script** — Scoring rubric based on moot court/bar exam evaluation criteria
5. **CLI tool** — Model selection and document type detection based on document template research
