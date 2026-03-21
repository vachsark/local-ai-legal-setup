"""
title: Writing Coach
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Legal writing improvement tools for law students. Reviews memos for IRAC structure and analysis depth, rewrites paragraphs with explanations, and generates Bluebook citation exercises. Legal writing is the most career-determinative skill in law school — this tool treats it seriously.
"""

import re
from pydantic import BaseModel


VALID_DOC_TYPES = ["memo", "brief", "motion", "contract", "email", "letter", "note"]

BLUEBOOK_DIFFICULTY_CONFIGS = {
    "basic": {
        "label": "1L first semester",
        "description": "Cases, statutes, and simple law review articles. Standard federal reporters only.",
        "items": ["case citation (federal)", "statute (U.S.C.)", "law review article", "textbook (secondary source)"],
    },
    "intermediate": {
        "label": "1L/2L after Bluebook training",
        "description": "State reporters, short-form citations, id. and supra usage, signals (See, Cf., But see).",
        "items": ["case citation (state court)", "short form / id.", "signal (See, Cf., But see)", "regulatory citation (C.F.R.)"],
    },
    "advanced": {
        "label": "Law review / moot court",
        "description": "Pinpoint citations, subsequent history, pending legislation, international sources, string citations with explanatory parentheticals.",
        "items": ["string citation with parentheticals", "subsequent history (aff'd, rev'd)", "pending legislation", "treaty / international source"],
    },
}


class Tools:
    class Valves(BaseModel):
        socratic_follow_up: bool = True
        max_text_length: int = 15000
        show_revision_rationale: bool = True

    def __init__(self):
        self.valves = self.Valves()

    async def review_memo(
        self,
        memo_text: str,
        __event_emitter__=None,
    ) -> str:
        """
        Review a law school memo for IRAC structure, analysis depth, and writing quality.
        Gives specific, actionable feedback — not generic advice.
        Ends with a Socratic question about the hardest analytical choice in the memo.

        :param memo_text: The full text of the student's memo.
        :return: Structured context for the LLM to produce a detailed writing review.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Analyzing memo structure...", "done": False},
                }
            )

        if not memo_text or not memo_text.strip():
            return "No memo text provided. Paste your memo text and try again."

        text = memo_text.strip()
        if len(text) > self.valves.max_text_length:
            text = text[: self.valves.max_text_length]
            truncation_note = f"\n\n[NOTE: Memo truncated to {self.valves.max_text_length} characters. Paste a shorter memo for complete analysis.]"
        else:
            truncation_note = ""

        # Basic structural checks
        lower = text.lower()
        has_issue = any(k in lower for k in ["issue", "question presented", "whether"])
        has_rule = any(k in lower for k in ["rule", "standard", "test", "elements"])
        has_application = any(k in lower for k in ["here", "in this case", "applying", "under these facts", "the facts show"])
        has_conclusion = any(k in lower for k in ["therefore", "thus", "conclude", "conclusion", "accordingly"])

        structural_flags = []
        if not has_issue:
            structural_flags.append("No clear issue/question presented detected")
        if not has_rule:
            structural_flags.append("Rule section may be weak or absent")
        if not has_application:
            structural_flags.append("Application section may be weak — look for 'here' / 'in this case' language")
        if not has_conclusion:
            structural_flags.append("Conclusion may be absent or unclear")

        flags_str = (
            "\n".join(f"- {f}" for f in structural_flags)
            if structural_flags
            else "- No obvious structural gaps detected (deeper analysis follows)"
        )

        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(re.split(r"[.!?]+", text))
        avg_sentence_length = round(word_count / max(sentence_count, 1))

        socratic_instruction = (
            "\n\n**SOCRATIC QUESTION**\nEnd the review with one question that challenges the student to defend the hardest analytical choice they made — not about grammar, but about substance. "
            "Make it specific to the memo's content."
            if self.valves.socratic_follow_up
            else ""
        )

        prompt_context = f"""You are a law school writing coach reviewing a student's legal memo. Your job is to give honest, specific, actionable feedback — not cheerleading.

MEMO STATISTICS:
- Words: {word_count}
- Approximate sentences: {sentence_count}
- Average sentence length: {avg_sentence_length} words
- Pre-scan structural flags:
{flags_str}

STUDENT'S MEMO:
---
{text}
---{truncation_note}

Review the memo using this framework:

---

## OVERALL ASSESSMENT
One paragraph. What is the memo's biggest strength and its most serious weakness? Be direct.

---

## IRAC STRUCTURE REVIEW

**Issue / Question Presented**
- Is the legal question stated precisely? (Should be "whether...when" format)
- Does it identify the specific legal standard at issue?
- Grade: Strong / Adequate / Weak / Missing

**Rule**
- Is the rule stated accurately? (Flag any rules that seem incorrect — do NOT fabricate corrections, flag for student to verify)
- Are all elements listed?
- Is there an exception the student missed?
- Grade: Strong / Adequate / Weak / Missing

**Application** (this is where most student memos fail)
- Does the student work through every element with the specific facts?
- Does the student acknowledge facts that cut the other way?
- Is there "conclusory application"? (stating a conclusion without analysis — the most common memo error)
- Quote specific sentences that need revision — then explain why
- Grade: Strong / Adequate / Weak / Missing

**Conclusion**
- Does the conclusion follow from the analysis?
- Does the student hedge appropriately (vs. overclaiming or underclaiming)?
- Grade: Strong / Adequate / Weak / Missing

---

## WRITING QUALITY

**Sentence-level issues** (quote specific examples + fix):
- Passive voice overuse (legal writing prefers active voice in the application section)
- Vague language ("arguably," "might," "could" without analysis behind them)
- Sentences over 35 words (split them)
- Starting sentences with "It is" or "There are" (restructure for clarity)

**Paragraph structure**:
- Each paragraph should have a point sentence, rule/application, and connective close
- Flag any paragraph that tries to do too much

**Legal vocabulary**:
- Are defined terms used consistently?
- Any misused terms of art? (flag specifically — do not replace legal terms with plain language equivalents)

---

## TOP 3 PRIORITIES
Number them. First is most important.
1. [Most important fix — structural or analytical]
2. [Second priority]
3. [Third priority — often a writing habit to break]

---

## WHAT'S WORKING
Be specific. What did the student do well that they should keep doing?{socratic_instruction}

IMPORTANT: Do NOT fabricate case citations or legal standards. If the student cited a case, do not comment on whether the citation is accurate — that requires Westlaw/Lexis verification. Flag only structural and analytical issues."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Review ready", "done": True},
                }
            )

        return prompt_context

    async def improve_paragraph(
        self,
        paragraph: str,
        doc_type: str = "memo",
        __event_emitter__=None,
    ) -> str:
        """
        Rewrite a paragraph from a legal document with explanations of every change.
        Teaches the student WHY the revision is better — not just what it looks like.
        Document types: memo, brief, motion, contract, email, letter.

        :param paragraph: The paragraph to improve.
        :param doc_type: The type of legal document (default: memo).
        :return: Structured context for the LLM to rewrite and explain every change.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Analyzing paragraph...", "done": False},
                }
            )

        if not paragraph or not paragraph.strip():
            return "No paragraph text provided. Paste the paragraph you want improved."

        text = paragraph.strip()[:3000]

        doc_type = doc_type.strip().lower()
        if doc_type not in VALID_DOC_TYPES:
            doc_type = "memo"

        # Document-type-specific guidance
        doc_guidance = {
            "memo": "objective analysis. Active voice in application. No advocacy language. Hedge appropriately.",
            "brief": "persuasive advocacy. Strong active verbs. Lead with your best argument. No equivocation.",
            "motion": "formal persuasion. Comply with local rules style. Short declarative sentences for key arguments.",
            "contract": "precision over readability. Avoid ambiguity at all costs. 'Shall' for obligations, 'may' for permissions, 'will' for conditions.",
            "email": "professional but accessible. No legalese for non-lawyer recipients. Short paragraphs. Clear ask.",
            "letter": "formal professionalism. Appropriate formality for recipient. Clear purpose stated early.",
            "note": "accuracy over style. Complete information. Can be dense — it's for internal use.",
        }

        guidance = doc_guidance.get(doc_type, doc_guidance["memo"])

        socratic_instruction = (
            "\n\n**LEARNING QUESTION**: After showing the revision, ask the student one question: "
            "Why is [specific word or structural choice in the revision] better than [the student's original choice]? "
            "Make it specific -- not 'Why is active voice better?' but 'Why does \"the court held\" work better than \"it was held by the court\" in this sentence?'"
            if self.valves.socratic_follow_up
            else ""
        )

        rationale_instruction = (
            "\n\nFor EVERY change you make in the revision, include a brief inline explanation in brackets: "
            "[Changed from passive to active voice — active voice makes clear who is acting] "
            "[Removed 'arguably' — unsupported hedging weakens the point; either make the argument or drop it] "
            "This is the most important part of the exercise — the student needs to understand the principle, not just the fixed text."
            if self.valves.show_revision_rationale
            else ""
        )

        prompt_context = f"""You are a legal writing coach. A student wants you to improve a paragraph from a {doc_type}.

DOCUMENT TYPE: {doc_type}
STYLE STANDARD FOR THIS DOC TYPE: {guidance}

STUDENT'S PARAGRAPH:
---
{text}
---

Produce the following:

## DIAGNOSIS
In 3–5 bullet points, identify the specific problems with this paragraph:
- Be precise: don't say "unclear" — say "the subject of sentence 2 is ambiguous because..."
- Common issues to check: conclusory application (conclusion without analysis), passive voice, vague hedging, run-on sentences, buried topic sentence, missing transition, misused terms of art

## REVISED PARAGRAPH
Rewrite the paragraph for a {doc_type}. Apply {guidance}{rationale_instruction}

## WHAT CHANGED AND WHY
After the revision, provide a numbered list of every significant change:
1. [Original phrase] → [Revised phrase]: [Principle applied]
2. [Original phrase] → [Revised phrase]: [Principle applied]
(continue for all meaningful changes)

The goal is that a student can read this list and understand the underlying principle, then apply it to every paragraph they write going forward — not just this one.{socratic_instruction}

IMPORTANT: Preserve all legal terms of art exactly. Do not replace legal vocabulary with plain language equivalents (e.g., do not replace "promissory estoppel" with "promise enforcement"). If a citation appears in the paragraph, preserve it exactly — do not correct or verify citations."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Revision ready", "done": True},
                }
            )

        return prompt_context

    async def citation_quiz(
        self,
        difficulty: str = "basic",
        __event_emitter__=None,
    ) -> str:
        """
        Generate a Bluebook citation exercise with an answer key.
        Difficulty options: basic, intermediate, advanced.
        Teaches the WHY behind citation rules, not just the format.

        :param difficulty: basic | intermediate | advanced (default: basic).
        :return: Structured context for the LLM to generate a Bluebook quiz with answers.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"Generating {difficulty} citation quiz...", "done": False},
                }
            )

        difficulty = difficulty.strip().lower()
        if difficulty not in BLUEBOOK_DIFFICULTY_CONFIGS:
            difficulty = "basic"

        config = BLUEBOOK_DIFFICULTY_CONFIGS[difficulty]

        socratic_instruction = (
            "\n\n**WRAP-UP QUESTION**: After the answer key, pose one question about WHY a Bluebook rule exists — not what the rule is. "
            "Example: 'Why does Bluebook require pinpoint citations rather than just citing the first page?' "
            "Students who understand the purpose of citation conventions use them more reliably under exam pressure."
            if self.valves.socratic_follow_up
            else ""
        )

        prompt_context = f"""You are a Bluebook citation instructor. Generate a citation exercise for a law student.

DIFFICULTY: {config['label']}
DIFFICULTY DESCRIPTION: {config['description']}
CITATION TYPES TO INCLUDE: {", ".join(config['items'])}

EXERCISE STRUCTURE:

**PART 1: CITATION PROBLEMS**

Generate 6 citation problems at {config['label']} difficulty.

For each problem, provide:
- A source description (enough information to cite it correctly)
- The context (e.g., "Full citation in a law review footnote," "Short citation after citing the same case two footnotes ago," "Inline citation in a court brief")

Format:
---
**Problem N** — [Citation type]
You are writing [context]. Cite the following source:
[Source information — title, author, volume, page, year, court, etc. — everything needed to cite it correctly]

Your citation: _______________
---

PROBLEM QUALITY STANDARDS:
- Include realistic-looking source details (but do NOT use real case names from memory — describe the source type)
- Make the context matter: a law review footnote citation differs from a brief inline citation
- For intermediate/advanced: include at least one problem where the student must choose a signal (See, Cf., etc.)
- For advanced: include at least one string citation problem

---

**PART 2: ANSWER KEY**

After all 6 problems, provide the answer key.

For each answer:
- Show the correct Bluebook citation
- Explain the rule applied (cite the Bluebook rule number if you are certain — if uncertain, describe the rule without a number)
- Note the most common error for that problem type: "Most students miss that..."

---

**PART 3: THE RULE BEHIND THE RULE**

For 3 of the 6 citation types covered, explain the PURPOSE of the Bluebook convention:
- Why does this rule exist?
- What problem does it solve for the reader?
- When do courts relax this requirement in practice (local rules, etc.)?{socratic_instruction}

IMPORTANT: Do NOT fabricate real case names, real reporter volumes, or Bluebook rule numbers you are not certain of. Use placeholder source names like "Smith v. Jones" or "Doe v. Roe" for case citations. Describe the rule accurately even if you omit the specific rule number."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Citation quiz ready", "done": True},
                }
            )

        return prompt_context
