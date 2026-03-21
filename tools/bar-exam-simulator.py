"""
title: Bar Exam Simulator
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Full bar exam simulation tools for law school graduates preparing for the MBE,
  MEE, and MPT. Generates realistic practice questions with explanations, essay questions
  with model answers and IRAC outlines, full MPT-style performance tests, and personalized
  study schedules based on your exam date and weak subjects.

  Runs entirely locally — no API costs, no data leaves your machine. Barbri charges
  $4,000. This is $0.

  Import into Open WebUI: Workspace → Tools → + → paste this file.

  Recommended models:
  - legal-tutor: Interactive Socratic drilling
  - qwen3.5:9b: Direct Q&A and structured output
  - gemma3:12b: Study schedules and longer explanations

  NOTE: This tool generates instructional content only. Verify all rules against current
  official bar prep materials (NCBE outlines, your jurisdiction's bar website). Legal rules
  change and AI training data has a cutoff date. Use this to drill — not as your rulebook.
"""

import math
import re
from datetime import date, datetime, timedelta
from pydantic import BaseModel


# Subject weights on the MBE (200 questions, unequal distribution as of current NCBE)
MBE_SUBJECT_WEIGHTS = {
    "civil-procedure": 25,
    "constitutional-law": 25,
    "contracts": 25,
    "criminal-law": 12,
    "criminal-procedure": 13,
    "evidence": 25,
    "real-property": 25,
    "torts": 25,
}

# MEE subjects tested on the Uniform Bar Exam
MEE_SUBJECTS = {
    "agency": "Agency and Partnership",
    "business-associations": "Business Associations (corporations, LLCs)",
    "civil-procedure": "Civil Procedure",
    "conflict-of-laws": "Conflict of Laws",
    "constitutional-law": "Constitutional Law",
    "contracts": "Contracts/Sales (UCC Article 2)",
    "criminal-law": "Criminal Law and Procedure",
    "evidence": "Evidence",
    "family-law": "Family Law",
    "professional-responsibility": "Professional Responsibility",
    "real-property": "Real Property",
    "secured-transactions": "Secured Transactions (UCC Article 9)",
    "torts": "Torts",
    "trusts-estates": "Trusts and Estates",
    "wills": "Wills",
}

# Subject aliases for fuzzy matching
SUBJECT_ALIASES = {
    "con law": "constitutional-law",
    "conlaw": "constitutional-law",
    "constitutional": "constitutional-law",
    "civ pro": "civil-procedure",
    "civpro": "civil-procedure",
    "civil procedure": "civil-procedure",
    "crim": "criminal-law",
    "criminal": "criminal-law",
    "crim pro": "criminal-procedure",
    "criminal procedure": "criminal-procedure",
    "evidence": "evidence",
    "evid": "evidence",
    "property": "real-property",
    "real property": "real-property",
    "prop": "real-property",
    "torts": "torts",
    "tort": "torts",
    "contracts": "contracts",
    "contract": "contracts",
    "k": "contracts",
    "agency": "agency",
    "partnership": "agency",
    "business associations": "business-associations",
    "corps": "business-associations",
    "corporations": "business-associations",
    "family law": "family-law",
    "family": "family-law",
    "pr": "professional-responsibility",
    "professional responsibility": "professional-responsibility",
    "ethics": "professional-responsibility",
    "secured transactions": "secured-transactions",
    "ucc 9": "secured-transactions",
    "trusts": "trusts-estates",
    "estates": "trusts-estates",
    "wills": "wills",
    "conflict": "conflict-of-laws",
    "conflicts": "conflict-of-laws",
}

# Study time allocation by subject (relative weight for bar prep)
SUBJECT_STUDY_WEIGHTS = {
    "civil-procedure": 12,
    "constitutional-law": 14,
    "contracts": 14,
    "criminal-law": 7,
    "criminal-procedure": 8,
    "evidence": 14,
    "real-property": 12,
    "torts": 12,
    "agency": 3,
    "business-associations": 4,
    "family-law": 3,
    "professional-responsibility": 5,
    "secured-transactions": 3,
    "trusts-estates": 4,
    "wills": 3,
    "conflict-of-laws": 2,
}


class Tools:
    class Valves(BaseModel):
        exam_jurisdiction: str = "UBE"  # e.g., "UBE", "California", "New York"
        show_answer: bool = True         # show correct answer after MBE question
        difficulty: str = "bar"          # "beginner", "bar", "expert"

    def __init__(self):
        self.valves = self.Valves()

    async def mbe_practice(
        self,
        subject: str,
        count: int = 10,
        __event_emitter__=None,
    ) -> str:
        """
        Generate MBE-style multiple choice questions for a specific subject.

        Each question has a realistic fact pattern, four answer choices, the correct
        answer with a full explanation, and analysis of why each wrong answer is wrong.
        This is the closest thing to actual MBE practice outside of NCBE official materials.

        Subjects: constitutional-law, contracts, criminal-law, criminal-procedure, evidence,
                  real-property, torts, civil-procedure

        :param subject: The MBE subject area to practice.
        :param count: Number of questions to generate (1-20, default 10).
        :return: A prompt that generates the requested MBE questions with full answer keys.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Building {count} MBE questions for {subject}...",
                        "done": False,
                    },
                }
            )

        count = max(1, min(int(count), 20))
        subject_key = self._normalize_subject(subject)
        subject_display = subject_key.replace("-", " ").title()

        difficulty_notes = {
            "beginner": "introductory level — test single, clean rule applications with one clearly correct answer",
            "bar": "actual bar exam difficulty — include distractors that require knowing the exception to the rule, not just the rule",
            "expert": "expert level — include minority/majority splits, the UCC vs. common law distinction where relevant, and questions where two answers look equally right to someone who hasn't studied the nuance",
        }
        diff_note = difficulty_notes.get(self.valves.difficulty, difficulty_notes["bar"])

        jurisdiction_note = ""
        if self.valves.exam_jurisdiction.lower() not in ("ube", "uniform bar exam", "general"):
            jurisdiction_note = f"\nJurisdiction focus: {self.valves.exam_jurisdiction}. Note any significant deviations from the majority rule that apply in this jurisdiction."

        answer_section = ""
        if self.valves.show_answer:
            answer_section = """
After each question, provide:
**ANSWER KEY**
Correct answer: [Letter]
Why [Letter] is correct: [2-3 sentence explanation citing the specific rule]
Why [A] is wrong: [1 sentence]
Why [B] is wrong: [1 sentence]
Why [C] is wrong: [1 sentence]
Why [D] is wrong: [1 sentence — omit the correct letter from "wrong" explanations]

Separate each question from its answer key with a horizontal rule (---) so students can fold or scroll past the answer before reading it."""

        prompt = f"""You are an MBE question writer. Generate exactly {count} multiple-choice questions for the MBE subject: **{subject_display}**.

Difficulty: {diff_note}{jurisdiction_note}

For each question, follow this format precisely:

---
**Question [N]**

[Fact pattern: 3-6 sentences. Use real-sounding names, specific dollar amounts, specific places, and concrete timelines. The facts must be precise enough that only one answer is correct. Ambiguous facts that aren't supposed to be ambiguous are bad questions.]

[Question stem: One sentence. Either "What is the most likely result?" / "Which of the following is correct?" / "What is [Party]'s strongest argument?" — vary the stem type across questions.]

(A) [Plausible answer]
(B) [Plausible answer]
(C) [Plausible answer]
(D) [Plausible answer]
{answer_section}

QUESTION QUALITY STANDARDS:
- Every wrong answer should be wrong because the test-taker either misremembered the rule or correctly remembered the rule but misapplied it — not because it's obviously absurd
- Do not make one answer obviously longer or more qualified than the others
- Include at least one question involving an exception or limitation on the primary rule
- At least one question should involve a common misunderstanding (a trap for students who partially know the material)
- Do not repeat similar fact patterns across questions — vary the scenarios

CRITICAL: Do NOT fabricate case names or statute section numbers. Describe rules by principle. The student will verify authority independently.

Begin with Question 1."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"{count} MBE questions ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def mee_practice(
        self,
        subject: str,
        __event_emitter__=None,
    ) -> str:
        """
        Generate an MEE-style essay question with a complete model answer.

        Produces a full essay question including: an issue-spotting checklist,
        IRAC outline, and a complete model answer written at passing standard.
        The MEE tests 6 subjects per exam sitting from the full list below.

        Subjects: agency, business-associations, civil-procedure, conflict-of-laws,
                  constitutional-law, contracts, criminal-law, evidence, family-law,
                  professional-responsibility, real-property, secured-transactions,
                  torts, trusts-estates, wills

        :param subject: The MEE subject area.
        :return: A prompt that generates a complete MEE-style essay question with model answer.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Generating MEE question for {subject}...",
                        "done": False,
                    },
                }
            )

        subject_key = self._normalize_subject(subject)
        subject_display = MEE_SUBJECTS.get(subject_key, subject_key.replace("-", " ").title())

        prompt = f"""You are an MEE question writer for the Uniform Bar Exam. Generate a complete MEE-style essay question for the subject: **{subject_display}**.

The MEE gives examinees 30 minutes to answer one essay. Your question should be answerable at a strong passing standard in that time.

---

**PART 1: THE QUESTION**

Write a fact pattern and call of the question using this format:

[Fact pattern: 4-6 paragraphs. Multiple parties, a specific timeline, concrete facts. The facts should raise 3-5 distinct legal issues within {subject_display}. Some facts should be ambiguous — deliberately raising sub-issues or requiring the examinee to argue both sides. Real MEE questions are dense; pack the facts.]

[Call of the question: List 3-5 specific questions the examinee must answer. Examples: "1. Did [Party] breach his fiduciary duty to [Company]? Discuss. 2. What remedies, if any, are available to [Plaintiff]? Discuss."]

---

**PART 2: ISSUE-SPOTTING CHECKLIST**

Before the model answer, provide a checklist of every legal issue raised by the fact pattern, organized by priority:
- [ ] [Primary issue 1]
- [ ] [Primary issue 2]
- [ ] [Secondary issue — raised by facts but easier to miss]
- [ ] [Potential trap — fact that might distract from the real issue]

---

**PART 3: IRAC OUTLINE**

A skeleton outline for a well-organized answer:

Issue 1: [Name]
  Rule: [1 sentence black-letter rule]
  Key facts: [2-3 facts that drive the analysis]
  Likely conclusion: [probable outcome]

Issue 2: [Name]
  Rule: [1 sentence black-letter rule]
  Key facts: [2-3 facts that drive the analysis]
  Likely conclusion: [probable outcome]

[continue for all issues]

---

**PART 4: MODEL ANSWER**

Write a complete passing-standard answer to the question. The answer should:
- Address every issue in the call of the question
- State each rule clearly and completely (all elements)
- Apply each rule to the specific facts — name the parties and the specific facts, don't just restate the rule
- Address facts that cut against the conclusion
- Reach a definite conclusion on each issue
- Use IRAC structure for each issue
- Be written in plain, direct prose — no headers needed (most bar exam answers are flowing paragraphs)
- Be the length a strong examinee could write in 30 minutes (~500-700 words)

---

CRITICAL RULES:
- Do NOT fabricate case names or citations
- Where rules have majority/minority splits, state the majority rule and note the split
- If facts are genuinely ambiguous, the model answer should argue both sides and conclude
- Label each part clearly (QUESTION, CHECKLIST, OUTLINE, MODEL ANSWER)"""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "MEE question ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def mpt_practice(
        self,
        task_type: str = "memo",
        __event_emitter__=None,
    ) -> str:
        """
        Generate an MPT-style performance test — the most underrated section of the bar exam.

        The MPT gives examinees 90 minutes to complete a lawyering task using a provided
        file (facts) and library (legal authority). No outside knowledge required — but you
        need to know how to organize and write under pressure.

        This generates a complete simulated MPT including: task memo, client file, library
        with cases/statutes, and a model answer showing what a passing response looks like.

        task_type options: memo, brief, letter, discovery-plan, negotiation

        :param task_type: The type of lawyering task (memo, brief, letter, discovery-plan, negotiation).
        :return: A prompt that generates a complete MPT simulation with model answer.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Building MPT simulation: {task_type}...",
                        "done": False,
                    },
                }
            )

        task_type = task_type.lower().strip()
        valid_tasks = {
            "memo": "office memorandum analyzing a legal question",
            "brief": "persuasive brief arguing a specific position",
            "letter": "client letter explaining a legal situation in plain language",
            "discovery-plan": "discovery plan identifying information needed and methods to obtain it",
            "negotiation": "negotiation strategy memo outlining positions, priorities, and fallbacks",
        }

        if task_type not in valid_tasks:
            task_type = "memo"

        task_desc = valid_tasks[task_type]

        prompt = f"""You are an MPT simulation designer. Generate a complete, realistic MPT-style performance test. The assigned task is a **{task_desc}**.

The MPT gives examinees 90 minutes and two documents: a File (facts, instructions) and a Library (legal authorities). Examinees must complete the task using only the provided materials.

Generate all three components:

---

## THE FILE

### Task Memorandum

From: [Supervising Partner Name]
To: Applicant
Re: [Matter Name and specific task]

[3-4 paragraphs:
1. Brief background on the client and matter
2. The specific legal question or problem
3. Explicit instructions for the task — what format, what to include, what to avoid, any constraints
4. Any practical considerations the applicant should know]

### Client File Materials

Include 2-3 of the following as appropriate for the task:
- Interview notes or email from client (2-3 paragraphs of facts)
- Relevant documents (contract excerpts, chronology, correspondence snippets)
- Internal notes from prior attorney work
- Any key facts the applicant needs to complete the task

Make the facts realistic and specific. Include some facts that are not legally relevant (the applicant must identify what matters). Include at least one fact that cuts against the client's position.

---

## THE LIBRARY

Provide 2-3 simulated legal authorities. These should be:

**[Case Name, simulated jurisdiction, simulated year]**
[A 2-3 paragraph simulated case excerpt — just the holding and reasoning relevant to the task. Format like an actual case excerpt with "The court held..." / "We conclude..." language. The case should directly address the legal question raised.]

**[Second Case or Statute]**
[Another simulated authority — either a case that creates tension with the first, OR a relevant statute. If a statute, write it in statutory language with numbered subsections.]

[Optional third authority if needed for completeness]

LIBRARY DESIGN RULES:
- All case names and citations are fictional — do not use real cases
- The library should be sufficient to complete the task but not spell out the answer
- Include at least one authority that requires interpretation — not a clear slam-dunk
- The applicant should need to reconcile or distinguish the authorities

---

## MODEL ANSWER

Write a complete passing-standard answer to the task. The model answer should:
- Follow the exact format requested in the task memo
- Use ONLY the authorities provided in the Library (no outside knowledge)
- Identify and address the key legal question(s)
- Apply the authorities to the client's facts concretely
- Acknowledge any contrary arguments or limitations
- Reach a definite conclusion with a recommendation
- Be formatted professionally for a law firm document

After the model answer, include a brief **SCORING GUIDE** noting:
- The 3-4 things a grader would look for in a passing answer
- The most common mistake examinees make on this type of task
- What separates a passing from a failing response on this particular question

---

CRITICAL: Make the simulated cases and statutes plausible but clearly fictional. Use fictional jurisdiction names (e.g., "Franklin" or "Columbia") and made-up reporter citations. The goal is realistic practice, not a misleading simulation of real law."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "MPT simulation ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def study_schedule(
        self,
        exam_date: str,
        subjects_weak: str = "",
        hours_per_day: int = 8,
        __event_emitter__=None,
    ) -> str:
        """
        Generate a personalized bar prep study schedule from today until your exam date.

        Calculates weeks remaining, allocates study time by subject (weighted by exam
        importance and your weak areas), and builds a day-by-day schedule with:
        - Subject rotation to avoid burnout
        - Front-loaded weak subjects
        - Built-in practice test days
        - Rest days (burnout is real)
        - Final review week structure

        :param exam_date: The date of your bar exam in YYYY-MM-DD, MM/DD/YYYY, or "July 2026" format.
        :param subjects_weak: Comma-separated list of subjects you feel weakest in (optional).
        :param hours_per_day: Study hours per day (default 8, recommended 6-10 for full-time prep).
        :return: A prompt that generates a complete personalized study schedule.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Calculating schedule...",
                        "done": False,
                    },
                }
            )

        # Parse exam date
        weeks_remaining, days_remaining = self._parse_exam_date(exam_date)
        hours_per_day = max(4, min(int(hours_per_day), 14))

        # Parse weak subjects
        weak_list = []
        if subjects_weak.strip():
            raw = [s.strip() for s in subjects_weak.replace("\n", ",").split(",") if s.strip()]
            for s in raw:
                normalized = self._normalize_subject(s)
                display = normalized.replace("-", " ").title()
                weak_list.append(display)

        weak_section = ""
        if weak_list:
            weak_section = f"\nWeakest subjects (front-load these): {', '.join(weak_list)}"

        phase_structure = self._build_phase_structure(weeks_remaining)
        total_hours = days_remaining * hours_per_day

        prompt = f"""You are a bar exam study coach. A student needs a personalized study schedule.

STUDENT INFORMATION:
- Exam date: {exam_date}
- Days until exam: {days_remaining} ({weeks_remaining} weeks)
- Study hours per day: {hours_per_day}
- Total available study hours: {total_hours}{weak_section}
- Jurisdiction: {self.valves.exam_jurisdiction}

PHASE STRUCTURE TO FOLLOW:
{phase_structure}

---

Generate a complete, day-by-day study schedule following these rules:

**SCHEDULING RULES:**

1. **Rest days**: Include 1 full rest day per week (no studying — mandatory for retention). More important than extra hours.

2. **Subject rotation**: Never study the same subject 2 days in a row (unless in final review). Cognitive science shows spaced repetition outperforms massed practice.

3. **Morning vs. afternoon split**: Harder subjects (Constitutional Law, Evidence, Property) in morning sessions when focus is highest. Practice tests and review in afternoon.

4. **Weak subject front-loading**: Weak subjects get extra hours in Weeks 1-3, then regular maintenance. You can't cram weak areas at the end.

5. **Practice test integration**: Full 100-question MBE practice test every 10-14 days. Timed. Score it. Analyze wrong answers before moving on.

6. **MEE/MPT days**: Dedicate 2 half-days per week to MEE essay practice. One MPT simulation per week starting Week 3.

7. **Final week**: No new material. Pure review, targeted drilling of weak spots, logistics preparation.

---

**SCHEDULE FORMAT:**

Organize by week. For each week, provide:

**WEEK [N]: [Phase Name]**
Focus subjects: [list]
Weekly goal: [1 sentence describing what "done" looks like for this week]

Then list each day:
- **[Day, Date if calculable]**: Morning (X hrs) — [Subject: specific task]. Afternoon (X hrs) — [Subject: specific task].

Daily tasks should be specific, not just subject names:
- Bad: "Torts — 3 hours"
- Good: "Torts: negligence elements + strict liability + products liability. Complete 30 MBE practice questions on negligence. Review all wrong answers."

---

**FINAL OUTPUT STRUCTURE:**
1. Schedule overview (total hours per subject)
2. Week-by-week breakdown with daily tasks
3. Practice test schedule (which dates to take full simulations)
4. Final week structure (days 7-1 before exam)
5. Day-before and morning-of protocols (sleep, nutrition, logistics — this matters)

---

Close with a brief note on what to do when the schedule slips — because it will slip. Give practical guidance on how to recalibrate without spiraling into anxiety. Be direct and supportive, not clinical."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Study schedule ready",
                        "done": True,
                    },
                }
            )

        return prompt

    # ─── helpers ────────────────────────────────────────────────────────────────

    def _normalize_subject(self, subject: str) -> str:
        """Normalize a user-supplied subject string to a canonical key."""
        s = subject.lower().strip()
        # Direct match
        if s in MBE_SUBJECT_WEIGHTS or s in MEE_SUBJECTS:
            return s
        # Alias match
        if s in SUBJECT_ALIASES:
            return SUBJECT_ALIASES[s]
        # Partial match against canonical keys
        all_keys = list(MBE_SUBJECT_WEIGHTS.keys()) + list(MEE_SUBJECTS.keys())
        for key in all_keys:
            if s in key or key in s:
                return key
        return s.replace(" ", "-")

    def _parse_exam_date(self, exam_date: str) -> tuple[int, int]:
        """Parse an exam date string and return (weeks_remaining, days_remaining)."""
        today = date.today()

        # Try various formats
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%B %Y",
            "%b %Y",
        ]

        parsed = None
        for fmt in formats:
            try:
                parsed = datetime.strptime(exam_date.strip(), fmt).date()
                if fmt in ("%B %Y", "%b %Y"):
                    # Use the last day of the month as exam date approximation
                    if parsed.month == 12:
                        parsed = date(parsed.year + 1, 1, 1) - timedelta(days=1)
                    else:
                        parsed = date(parsed.year, parsed.month + 1, 1) - timedelta(days=1)
                break
            except ValueError:
                continue

        if parsed is None or parsed <= today:
            # Default to ~10 weeks from today if we can't parse
            parsed = today + timedelta(weeks=10)

        delta = parsed - today
        days_remaining = max(delta.days, 1)
        weeks_remaining = max(days_remaining // 7, 1)
        return weeks_remaining, days_remaining

    def _build_phase_structure(self, weeks: int) -> str:
        """Return a phase structure description based on weeks available."""
        if weeks <= 4:
            return """
SHORT SCHEDULE (4 weeks or less):
- Week 1-2: Intensive MBE subject review (high-yield only: Torts, Contracts, Evidence, Con Law)
- Week 3: MEE essay drilling + MPT practice
- Week 4 / Final Days: Review, practice tests, no new material"""
        elif weeks <= 8:
            return """
STANDARD SCHEDULE (5-8 weeks):
- Phase 1 (Weeks 1-3): Subject-by-subject MBE review, one subject per day
- Phase 2 (Weeks 4-5): MEE essay practice + MPT simulations, continue MBE drilling
- Phase 3 (Weeks 6-7): Full practice tests, weak area targeting
- Phase 4 (Final Week): Review only, no new material"""
        elif weeks <= 12:
            return """
FULL SCHEDULE (9-12 weeks):
- Phase 1 (Weeks 1-4): Foundation — all 7 MBE subjects, systematic outline review
- Phase 2 (Weeks 5-7): Application — practice questions, issue spotting, essay writing
- Phase 3 (Weeks 8-10): Integration — full practice tests, timed simulations, MEE/MPT focus
- Phase 4 (Weeks 11-12): Refinement — weak areas, final review, logistics"""
        else:
            return f"""
EXTENDED SCHEDULE ({weeks} weeks):
- Phase 1 (Weeks 1-{weeks//4}): Foundation — thorough subject review with low time pressure
- Phase 2 (Weeks {weeks//4+1}-{weeks//2}): Application — heavy practice question drilling
- Phase 3 (Weeks {weeks//2+1}-{(3*weeks)//4}): Integration — timed full simulations, MEE/MPT focus
- Phase 4 (Final {weeks - (3*weeks)//4} weeks): Refinement and review
Note: Starting this early is a significant advantage. Use Phase 1 to build solid foundations
without pressure, then ramp intensity in Phases 2-3."""
