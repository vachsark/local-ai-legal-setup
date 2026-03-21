"""
title: Case Briefer
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Law school case briefing tools. Brief cases in FIRAC format, compare holdings, and generate topic outlines. Designed for 1L–3L students who need to build analytical skills, not just get answers.
"""

import json
from pydantic import BaseModel


class Tools:
    class Valves(BaseModel):
        max_case_length: int = 20000
        socratic_follow_up: bool = True

    def __init__(self):
        self.valves = self.Valves()

    async def brief_case(
        self,
        case_text: str,
        __event_emitter__=None,
    ) -> str:
        """
        Generate a case brief from pasted case text.
        Format: Facts, Issue, Rule, Application, Conclusion (FIRAC).
        Also identifies the holding, obiter dicta, and concurrence/dissent summaries.
        Ends with a Socratic question to deepen understanding.

        :param case_text: The full text of the case (paste directly from the reporter or PDF).
        :return: Structured context for the LLM to produce a FIRAC brief.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Parsing case text...", "done": False},
                }
            )

        if not case_text or not case_text.strip():
            return "No case text provided. Paste the full case text (or a substantial excerpt) and try again."

        text = case_text.strip()
        if len(text) > self.valves.max_case_length:
            text = text[: self.valves.max_case_length]
            truncation_note = f"\n\n[NOTE: Case text truncated to {self.valves.max_case_length} characters. Paste a shorter excerpt for best results.]"
        else:
            truncation_note = ""

        char_count = len(text)
        word_count = len(text.split())

        # Detect common court signals
        signals = []
        lower = text.lower()
        if "dissent" in lower or "dissenting" in lower:
            signals.append("dissent present")
        if "concurr" in lower:
            signals.append("concurrence present")
        if "affirm" in lower:
            signals.append("affirmance signal")
        if "revers" in lower or "vacate" in lower:
            signals.append("reversal/vacatur signal")
        if "remand" in lower:
            signals.append("remand signal")

        signals_str = (
            "Detected signals: " + ", ".join(signals) if signals else "No special signals auto-detected."
        )

        socratic_instruction = (
            "\n\nAfter completing the brief, end with a SOCRATIC QUESTION that pushes the student to think one level deeper — "
            "about why the court drew the line where it did, what the rule's limits are, or how the holding would apply to a slightly different fact pattern."
            if self.valves.socratic_follow_up
            else ""
        )

        prompt_context = f"""You are a law school case briefing assistant. A student has pasted a case for you to brief.

CASE STATISTICS:
- Characters: {char_count}
- Approximate words: {word_count}
- {signals_str}

STUDENT'S CASE TEXT:
---
{text}
---{truncation_note}

Produce a complete case brief using FIRAC structure:

**CASE NAME & CITATION**
[Extract the full case name and citation from the text. If not apparent, write "See case text."]

**FACTS** (procedural + substantive)
- Procedural posture: How did this case get to this court?
- Key facts: Which facts did the court rely on? (bullet points, 4–8 items)
- Facts the court ignored or found irrelevant: (brief note — helps students learn what matters)

**ISSUE**
State the precise legal question the court decided. Use "whether...when" format.
(If multiple issues, number them.)

**RULE**
State the legal rule the court applied. Include:
- The standard/test (elements, if any)
- Source of the rule (common law, statute, prior case — without fabricating citations)
- Any exceptions the court acknowledged

**APPLICATION**
How did the court apply the rule to these facts?
- Walk through each element or factor
- Note which facts drove the outcome
- Note what the dissent/concurrence argued, if present

**CONCLUSION / HOLDING**
- Holding: The precise legal conclusion (not just "plaintiff wins")
- Disposition: What happened to the case (affirmed, reversed, remanded, etc.)

**DICTA**
Statements in the opinion that are NOT binding — things the court said but didn't need to decide. Flag these clearly: students often mistake dicta for holdings.

**EXAM ANGLE**
How is this case likely to appear on a law school exam? What issue does it stand for? What fact pattern would trigger it?{socratic_instruction}

IMPORTANT: Do NOT fabricate case names or citations. If the case text contains citations, use them exactly as written. If it does not, describe legal principles without inventing authority."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Brief ready", "done": True},
                }
            )

        return prompt_context

    async def compare_cases(
        self,
        case1: str,
        case2: str,
        __event_emitter__=None,
    ) -> str:
        """
        Compare two cases — distinguish or reconcile their holdings.
        Essential for understanding how doctrine develops across decisions.
        Ends with a Socratic question about the tension between the two rules.

        :param case1: Text or description of the first case (name, facts, holding).
        :param case2: Text or description of the second case (name, facts, holding).
        :return: Structured context for the LLM to compare and distinguish the cases.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Comparing cases...", "done": False},
                }
            )

        if not case1 or not case1.strip():
            return "Case 1 is empty. Provide text or a description of the first case."
        if not case2 or not case2.strip():
            return "Case 2 is empty. Provide text or a description of the second case."

        c1 = case1.strip()[:8000]
        c2 = case2.strip()[:8000]

        socratic_instruction = (
            "\n\nEnd with a SOCRATIC QUESTION: present a new hypothetical fact pattern that sits in the gray zone between these two cases and ask the student which rule applies — and why."
            if self.valves.socratic_follow_up
            else ""
        )

        prompt_context = f"""You are a law school case comparison assistant. A student wants to compare two cases.

CASE 1:
---
{c1}
---

CASE 2:
---
{c2}
---

Produce a structured case comparison:

**SIDE-BY-SIDE OVERVIEW**
| Element | Case 1 | Case 2 |
|---------|--------|--------|
| Name/Citation | | |
| Key Facts | | |
| Issue | | |
| Rule Applied | | |
| Holding | | |
| Outcome | | |

**ARE THESE CASES CONSISTENT OR IN TENSION?**
State clearly: Do these cases follow the same rule (reconcilable) or point in different directions (in tension)?

**HOW TO DISTINGUISH**
If the cases reach different outcomes, explain what factual or legal difference accounts for the distinction.
- Which facts in Case 1 were absent in Case 2 (or vice versa)?
- Did the courts apply the same rule but weigh factors differently?
- Is one case an exception to the other's general rule?

**HOW TO RECONCILE**
If the cases are consistent, show how they fit together as a coherent doctrine:
- Does Case 2 extend, limit, or refine the rule in Case 1?
- What principle unifies both outcomes?

**EXAM STRATEGY**
On an exam, if you see both cases cited in a fact pattern — what does the professor want you to do? (Spot the tension, apply both tests, distinguish?)

**COMMON STUDENT MISTAKE**
What do most students get wrong when they see these two cases together?{socratic_instruction}

IMPORTANT: Do NOT fabricate case names or citations beyond what the student provided."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Comparison ready", "done": True},
                }
            )

        return prompt_context

    async def outline_topic(
        self,
        subject: str,
        topic: str,
        __event_emitter__=None,
    ) -> str:
        """
        Generate a study outline for a law school topic (e.g., subject=Torts, topic=Negligence).
        Covers black-letter rules, exceptions, elements, and exam triggers.
        Ends with a Socratic question about the hardest conceptual issue in the topic.

        :param subject: The law school course (e.g., Torts, Contracts, ConLaw, CivPro, Crim, Evidence).
        :param topic: The specific topic within that subject (e.g., Negligence, Offer and Acceptance, Free Speech).
        :return: Structured context for the LLM to generate a comprehensive study outline.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Building outline: {subject} > {topic}...",
                        "done": False,
                    },
                }
            )

        if not subject or not subject.strip():
            return "Subject is required (e.g., Torts, Contracts, Constitutional Law)."
        if not topic or not topic.strip():
            return "Topic is required (e.g., Negligence, Consideration, Equal Protection)."

        socratic_instruction = (
            "\n\nEnd with a SOCRATIC QUESTION targeting the hardest conceptual issue in this topic — the one most students answer incorrectly on exams."
            if self.valves.socratic_follow_up
            else ""
        )

        prompt_context = f"""You are a law school study guide assistant. A student needs a comprehensive outline for:

SUBJECT: {subject.strip()}
TOPIC: {topic.strip()}

Generate a structured law school study outline following this format:

**{subject.strip().upper()} — {topic.strip().upper()}**

**I. THE BLACK-LETTER RULE**
State the rule concisely. This is what you memorize. No hedging.

**II. ELEMENTS / FACTORS**
List each element or factor required to satisfy the rule.
For each element:
- Definition
- What evidence satisfies it
- Common ways a plaintiff/prosecutor fails to prove it
- Common ways a defendant defeats it

**III. EXCEPTIONS AND LIMITATIONS**
- What carves out of the general rule?
- Majority rule vs. minority rule (where splits exist)
- Restatement position (1st, 2nd, or 3rd, where applicable)
- UCC position (for Contracts/Sales topics)

**IV. KEY CASES TO KNOW**
Do NOT fabricate case names. Instead, describe the type of case (by fact pattern archetype) that established each key sub-rule, and what the court held. Example: "In the leading duty-to-rescue case, the court held that..." This trains pattern recognition without relying on memorized case names.

**V. EXAM TRIGGERS**
What fact patterns signal that this doctrine is being tested?
List 5–8 "trigger facts" — when you see X in a hypo, you should immediately think of this rule.

**VI. COMMON STUDENT MISTAKES**
What are the 3 most frequent errors students make on exams with this topic?
Format: "Most students miss that..." or "Students often confuse..."

**VII. CONNECTIONS TO OTHER TOPICS**
How does this topic interact with others in the same course?
(e.g., Negligence connects to: contributory negligence, assumption of risk, comparative fault, strict liability)

**VIII. ONE-SENTENCE SUMMARY**
Write the single sentence a professor most wants to see on an exam for this topic.{socratic_instruction}

IMPORTANT: Do NOT invent case names, statute numbers, or Restatement section numbers. Describe rules and principles accurately, but flag any authority with "verify independently." """

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Outline ready", "done": True},
                }
            )

        return prompt_context
