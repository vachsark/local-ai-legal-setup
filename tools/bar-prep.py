"""
title: Bar Exam Prep Assistant
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Bar exam preparation tools for law students. Generates MBE-style practice
  questions, spots issues in fact patterns, produces memorizable rule statements,
  creates mnemonics, and grades practice essays on IRAC structure. Runs entirely
  locally — no API costs, no data leaves your machine.

  Import into Open WebUI: Workspace → Tools → + → paste this file.

  Recommended model: legal-tutor (see Modelfile.legal-tutor) for Socratic guidance,
  or qwen3.5:9b / mistral-small:24b for direct answers.

  NOTE: This tool generates instructional content only. All rules and legal principles
  should be verified against current bar prep materials (BarBri, Themis, NCBE outlines).
  Legal rules change and AI training data has a cutoff date.
"""

import re
from pydantic import BaseModel


# MBE subject areas with sub-topics for structured question generation
MBE_SUBJECTS = {
    "civil procedure": [
        "personal jurisdiction", "subject matter jurisdiction", "venue",
        "pleading standards", "joinder", "class actions", "discovery",
        "summary judgment", "res judicata", "collateral estoppel",
    ],
    "constitutional law": [
        "due process", "equal protection", "first amendment", "fourth amendment",
        "fifth amendment", "commerce clause", "state action", "standing",
        "ripeness", "mootness", "executive power", "judicial review",
    ],
    "contracts": [
        "offer and acceptance", "consideration", "statute of frauds",
        "conditions", "breach", "anticipatory repudiation", "damages",
        "UCC article 2", "third party beneficiaries", "assignment and delegation",
        "defenses", "promissory estoppel",
    ],
    "criminal law": [
        "actus reus", "mens rea", "homicide", "theft offenses", "assault and battery",
        "defenses", "inchoate crimes", "accomplice liability", "constitutional limits",
    ],
    "criminal procedure": [
        "fourth amendment search and seizure", "fifth amendment self-incrimination",
        "sixth amendment right to counsel", "miranda", "exclusionary rule",
        "grand jury", "bail", "double jeopardy", "speedy trial",
    ],
    "evidence": [
        "relevance", "hearsay", "hearsay exceptions", "character evidence",
        "impeachment", "expert witnesses", "privileges", "authentication",
        "best evidence rule", "lay witnesses",
    ],
    "real property": [
        "freehold estates", "future interests", "concurrent ownership",
        "landlord-tenant", "easements", "covenants and equitable servitudes",
        "adverse possession", "recording acts", "mortgages", "deed requirements",
    ],
    "torts": [
        "negligence", "duty", "breach", "causation", "damages", "strict liability",
        "products liability", "intentional torts", "defamation", "privacy torts",
        "nuisance", "defenses",
    ],
    "mee": [
        "agency", "partnerships", "corporations", "family law", "wills",
        "trusts", "conflict of laws", "secured transactions", "professional responsibility",
    ],
}

IRAC_INSTRUCTIONS = """
Use strict IRAC structure for each issue:
- ISSUE: State the precise legal question raised by the facts
- RULE: State the applicable rule of law concisely and completely
- APPLICATION: Apply each element of the rule to the specific facts — use the facts, don't just recite them
- CONCLUSION: State the likely outcome on this issue

Be thorough — bar graders credit spotting and analysis, not just conclusions.
""".strip()


class Tools:
    class Valves(BaseModel):
        difficulty: str = "bar"  # "1L", "bar", or "advanced"
        show_answer_hint: bool = True  # include answer explanation in practice Qs
        essay_strict_mode: bool = False  # True = harsh grading like actual bar

    def __init__(self):
        self.valves = self.Valves()

    async def practice_question(
        self,
        topic: str,
        subject: str = "torts",
        __event_emitter__=None,
    ) -> str:
        """
        Generate an MBE-style multiple choice practice question on any bar exam topic.

        Produces a realistic 4-option question with a detailed explanation of the correct
        answer and why each wrong answer is wrong. Use this to drill specific weak areas.

        :param topic: The specific topic to test (e.g., "negligence per se", "hearsay exceptions", "adverse possession").
        :param subject: The MBE subject area. Options: torts, contracts, civil procedure, constitutional law, criminal law, criminal procedure, evidence, real property, mee (Multistate Essay Exam subjects).
        :return: A complete MBE-style question with answer explanation for the LLM to present.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Generating practice question...", "done": False},
                }
            )

        subject_norm = subject.lower().strip()
        matched_subject = self._match_subject(subject_norm)
        sub_topics = MBE_SUBJECTS.get(matched_subject, [])
        sub_topic_hint = (
            f"Related sub-topics in this area: {', '.join(sub_topics[:6])}." if sub_topics else ""
        )

        difficulty_map = {
            "1l": "appropriate for a first-year law student",
            "bar": "at bar exam difficulty level (MBE standard)",
            "advanced": "at an advanced level, involving nuanced distinctions or minority rules",
        }
        difficulty_label = difficulty_map.get(
            self.valves.difficulty.lower(), "at bar exam difficulty level (MBE standard)"
        )

        answer_hint_instruction = ""
        if self.valves.show_answer_hint:
            answer_hint_instruction = """
After the question and answer choices, provide:
**Correct Answer: [Letter]**
**Explanation:** A detailed explanation (3-5 sentences) of why the correct answer is right and why each of the other three options is wrong. For wrong answers, explain the rule that would apply if the facts were different."""

        prompt = f"""Generate one MBE-style multiple choice practice question about "{topic}" in the subject area of {matched_subject or subject}. {sub_topic_hint}

The question should be {difficulty_label}.

Format:
- A realistic fact pattern (3-6 sentences setting up the scenario)
- A clear question stem asking what result or what the best argument is
- Exactly four answer choices labeled (A), (B), (C), (D)
- Each wrong answer should represent a plausible but incorrect legal theory or misapplication of the rule
- Do not make one answer obviously correct — the distractors should require real knowledge to rule out
{answer_hint_instruction}

IMPORTANT: Do not fabricate specific case citations. Describe the legal rule by principle, not by case name."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Question ready", "done": True},
                }
            )

        return prompt

    async def spot_issues(
        self,
        fact_pattern: str,
        __event_emitter__=None,
    ) -> str:
        """
        Identify all legal issues in a fact pattern using IRAC structure.

        Give this tool a fact pattern (like those used in bar exam essays or law school exams)
        and it will systematically identify every legal issue present, organized by subject area
        and analyzed in IRAC format. Useful for issue-spotting practice before writing your answer.

        :param fact_pattern: The full fact pattern text to analyze for legal issues.
        :return: A structured issue-spotting analysis prompt for the LLM to execute.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Analyzing fact pattern for legal issues...", "done": False},
                }
            )

        word_count = len(fact_pattern.split())
        if word_count < 30:
            return (
                "The fact pattern is too short for meaningful issue spotting. "
                "Please provide a complete scenario (at least 50 words) describing the parties, "
                "their actions, and the context."
            )

        if len(fact_pattern) > 8000:
            fact_pattern = fact_pattern[:8000] + "\n\n[Fact pattern truncated at 8,000 characters]"

        prompt = f"""Perform a complete issue-spotting analysis of the following fact pattern. This is bar exam practice.

TASK:
1. First, list ALL legal issues you can identify, organized by subject area (torts, contracts, criminal law, constitutional law, civil procedure, property, evidence, etc.)
2. Then, analyze each significant issue in full IRAC format

{IRAC_INSTRUCTIONS}

ISSUE-SPOTTING STANDARDS:
- Identify both obvious issues AND subtle/secondary issues
- Flag issues even if the facts are ambiguous — note the ambiguity and analyze both possibilities
- Note any issues that are raised but where insufficient facts are given to resolve them
- Call out when the same facts raise issues in multiple subject areas
- Do not ignore issues just because they seem to favor one party

FACT PATTERN:
{fact_pattern}

Begin with a quick issue inventory (bulleted list by subject area), then work through each issue in IRAC format. Be thorough — on the bar exam, you earn points for spotting issues, not just reaching correct conclusions."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Analysis complete", "done": True},
                }
            )

        return prompt

    async def rule_statement(
        self,
        topic: str,
        jurisdiction: str = "general",
        __event_emitter__=None,
    ) -> str:
        """
        Generate a clear, memorizable rule statement for any legal doctrine.

        Produces a concise, bar-exam-ready rule statement with the elements broken out,
        important exceptions, and a memory hook. Use this to build your rule bank.

        :param topic: The legal doctrine or rule to explain (e.g., "res ipsa loquitur", "mailbox rule", "rule against perpetuities").
        :param jurisdiction: "general" for majority rule, or specify a state for any known majority/minority splits (e.g., "california", "UCC").
        :return: A structured rule statement prompt for the LLM to generate.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Generating rule statement...", "done": False},
                }
            )

        juris_note = ""
        if jurisdiction.lower() not in ("general", "majority", "common law", ""):
            juris_note = f"Focus on the rule as applied in {jurisdiction}, noting any deviation from the majority rule."
        else:
            juris_note = "State the majority/general common law rule. Note significant minority rules or UCC variations where relevant."

        prompt = f"""Generate a complete, memorizable rule statement for: **{topic}**

{juris_note}

Format your response as follows:

**THE RULE (memorizable statement)**
Write the rule in 1-3 sentences that can be stated verbatim on a bar exam essay. This should be precise and complete — every element, no fluff.

**ELEMENTS** (if the rule has distinct elements)
List each element with a one-line explanation.

**KEY EXCEPTIONS**
List the most important exceptions or limitations. Include common bar exam traps.

**MAJORITY VS. MINORITY**
Note any significant splits between majority rule, minority rule, Restatement, or UCC approach.

**TRIGGER FACTS** (what fact pattern signals this rule applies)
List 3-5 key facts that should make a bar exam student think of this rule immediately.

**COMMON MISTAKES**
List 2-3 mistakes students commonly make when applying this rule.

**MEMORY HOOK** (optional but useful)
A mnemonic, analogy, or pattern that makes the rule stick.

IMPORTANT: Do not cite specific cases by name. Describe the rule by principle. This is a learning tool — the student will verify rules against their official bar prep materials."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Rule statement ready", "done": True},
                }
            )

        return prompt

    async def mnemonic(
        self,
        topic: str,
        rule_description: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Generate memory aids and mnemonics for complex legal rules.

        Creates acronyms, visual associations, rhymes, stories, and other memory
        techniques to help rules stick. Especially useful for multi-element tests
        and rules-within-rules (like the hearsay exception exceptions).

        :param topic: The rule or concept to create memory aids for (e.g., "elements of negligence", "hearsay exceptions under FRE 803").
        :param rule_description: Optional — paste the rule text if you want mnemonics tailored to specific language.
        :return: A prompt for the LLM to generate multiple memory techniques.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Creating memory aids...", "done": False},
                }
            )

        rule_context = ""
        if rule_description.strip():
            rule_context = f"\nThe rule/elements to memorize:\n{rule_description.strip()}\n"

        prompt = f"""Generate multiple memory aids to help a bar exam student remember: **{topic}**
{rule_context}
Create at least THREE different types of memory techniques:

1. **ACRONYM** — If the rule has elements, create an acronym. Show the acronym, what each letter stands for, and a sentence using the acronym in context.

2. **STORY OR SCENARIO** — A vivid, memorable mini-story that encodes the rule. The weirder or more memorable, the better. The details should map directly to the rule elements.

3. **PATTERN RECOGNITION** — What's the "shape" of this rule? Describe what makes fact patterns that trigger this rule distinctive, so the student learns to recognize it instantly.

4. **CONTRAST** (if applicable) — What does this rule sound like but isn't? What's most commonly confused with it? Creating a clear contrast between similar rules is one of the most effective memory techniques.

5. **ONE-LINER** — A single sentence that captures the essence of the rule in plain English. Not the rule itself — a plain-language description of what it's really doing.

Make the aids memorable and bar-exam-practical. Prioritize accuracy over creativity — the student will stake their bar exam on this."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Memory aids ready", "done": True},
                }
            )

        return prompt

    async def grade_essay(
        self,
        essay: str,
        topic: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Grade a practice bar exam essay on IRAC structure and analysis quality.

        Provides detailed feedback on issue spotting, rule accuracy, application quality,
        and writing mechanics. Identifies strengths and specific areas for improvement.
        This mirrors how bar examiners evaluate essays.

        :param essay: The full practice essay text to grade.
        :param topic: Optional — the subject area or specific question the essay was answering (e.g., "torts essay — negligence and strict liability").
        :return: A detailed grading prompt for the LLM to execute.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Grading essay...", "done": False},
                }
            )

        word_count = len(essay.split())
        if word_count < 50:
            return (
                "The essay is too short to grade meaningfully. "
                "Please paste a complete practice essay (at least 200 words)."
            )

        if len(essay) > 12000:
            essay = essay[:12000] + "\n\n[Essay truncated at 12,000 characters for grading]"

        topic_context = f"\nEssay topic/question: {topic}" if topic.strip() else ""
        strict_note = ""
        if self.valves.essay_strict_mode:
            strict_note = "\nGrading mode: STRICT — apply actual bar exam grader standards. Do not be encouraging if the work is deficient."

        prompt = f"""Grade the following practice bar exam essay. Provide detailed, actionable feedback.{topic_context}{strict_note}

GRADING RUBRIC — evaluate each category:

**1. ISSUE SPOTTING (25%)**
- Were all major issues identified?
- Were secondary/subtle issues identified?
- Were any issues missed entirely? What were they?
- Were issues organized logically (by subject area or chronologically through the facts)?

**2. RULE STATEMENTS (25%)**
- Were rules stated accurately and completely?
- Were all elements of each rule included?
- Did the student confuse majority vs. minority rules?
- Were any rules stated incorrectly or incompletely?

**3. APPLICATION/ANALYSIS (35%)**
- Did the student apply the rule to the SPECIFIC FACTS (not just restate the facts)?
- Did the student reach and analyze the hard questions, or did they skip to conclusions?
- Were both sides of contested issues analyzed?
- Was reasoning sound and logically structured?

**4. CONCLUSIONS (5%)**
- Were conclusions reached for each issue?
- Were conclusions supported by the analysis?
- Did the student avoid conclusory statements that skip the analysis?

**5. ORGANIZATION AND WRITING (10%)**
- Was IRAC structure used consistently?
- Was the essay organized and easy to follow?
- Were sentences clear and concise?
- Was legal terminology used accurately?

OUTPUT FORMAT:
1. **Overall Score**: X/10 with a one-paragraph summary
2. **What You Did Well**: Genuine strengths (be specific, not generic)
3. **Critical Issues**: Problems that would cause significant point loss on an actual bar exam
4. **Missed Issues**: Issues not addressed that should have been
5. **Analysis Quality**: Where the application section fell short and how to improve it
6. **Rule Accuracy**: Any rule statements that need correction
7. **Rewrite This Paragraph**: Pick the weakest paragraph and show how to rewrite it at a passing standard
8. **One Priority for Your Next Essay**: The single most important thing to fix

PRACTICE ESSAY:
{essay}

Be honest and direct. This student is preparing for a high-stakes exam. Vague encouragement doesn't help them pass."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Grading complete", "done": True},
                }
            )

        return prompt

    # ─── helpers ────────────────────────────────────────────────────────────────

    def _match_subject(self, subject_input: str) -> str:
        """Fuzzy-match a user-supplied subject string to a known MBE subject."""
        subject_input = subject_input.lower().strip()
        # Direct match
        if subject_input in MBE_SUBJECTS:
            return subject_input
        # Partial match
        for key in MBE_SUBJECTS:
            if subject_input in key or key in subject_input:
                return key
        # Common abbreviations
        abbrev = {
            "civ pro": "civil procedure",
            "civpro": "civil procedure",
            "con law": "constitutional law",
            "conlaw": "constitutional law",
            "crim": "criminal law",
            "crim pro": "criminal procedure",
            "crimes": "criminal law",
            "prop": "real property",
            "property": "real property",
            "k": "contracts",
            "contracts": "contracts",
            "evid": "evidence",
        }
        return abbrev.get(subject_input, subject_input)
