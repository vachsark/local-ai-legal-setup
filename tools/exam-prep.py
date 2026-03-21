"""
title: Exam Prep
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Law school exam preparation tools. Generates practice hypotheticals with model answers, builds study outlines from topic lists, and creates flashcard Q&A sets. All tools are exam-focused — the goal is pattern recognition, not rule memorization.
"""

import json
import random
from pydantic import BaseModel


# Canonical subject list for validation hints
VALID_SUBJECTS = [
    "Torts",
    "Contracts",
    "Property",
    "Constitutional Law",
    "Criminal Law",
    "Criminal Procedure",
    "Civil Procedure",
    "Evidence",
    "Administrative Law",
    "Corporations",
    "Business Associations",
    "Trusts and Estates",
    "Family Law",
    "Professional Responsibility",
    "Conflicts of Law",
    "Federal Courts",
    "Tax",
    "Secured Transactions",
    "Remedies",
    "Environmental Law",
    "Immigration Law",
    "Intellectual Property",
    "International Law",
]

DIFFICULTY_CONFIGS = {
    "easy": {
        "label": "1L / bar-prep baseline",
        "description": "Single issue, clean facts, one party clearly in the right. Tests whether students know the basic rule.",
        "issues": 1,
        "twists": "none",
    },
    "medium": {
        "label": "Standard 1L/2L exam",
        "description": "2–3 issues, some ambiguous facts that cut both ways. Tests whether students can IRAC under time pressure.",
        "issues": "2–3",
        "twists": "one fact that favors defendant and one that favors plaintiff on the same element",
    },
    "hard": {
        "label": "Advanced / professor-written",
        "description": "Multiple issues, at least one hidden sub-issue, facts that trigger both majority and minority rules. Tests analytical depth and issue-spotting under time pressure.",
        "issues": "3–5",
        "twists": "one red herring fact, one issue that requires knowing an exception to an exception",
    },
}


class Tools:
    class Valves(BaseModel):
        socratic_follow_up: bool = True
        include_model_answer: bool = True

    def __init__(self):
        self.valves = self.Valves()

    async def practice_hypo(
        self,
        subject: str,
        difficulty: str = "medium",
        __event_emitter__=None,
    ) -> str:
        """
        Generate a law school exam-style hypothetical with a model answer.
        Difficulty options: easy, medium, hard.
        Ends with a Socratic question that pushes one step beyond the model answer.

        :param subject: The law school course (e.g., Torts, Contracts, ConLaw).
        :param difficulty: easy | medium | hard (default: medium).
        :return: Structured context for the LLM to generate a hypo + model answer.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Generating {difficulty} {subject} hypo...",
                        "done": False,
                    },
                }
            )

        if not subject or not subject.strip():
            return (
                "Subject is required. Examples: Torts, Contracts, Constitutional Law, "
                "Criminal Law, Civil Procedure, Evidence, Property."
            )

        difficulty = difficulty.strip().lower()
        if difficulty not in DIFFICULTY_CONFIGS:
            difficulty = "medium"

        config = DIFFICULTY_CONFIGS[difficulty]

        socratic_instruction = (
            "\n\n**SOCRATIC FOLLOW-UP**\nAfter the model answer, pose one question that the model answer does NOT resolve — "
            "a wrinkle in the facts that would change the outcome if true. Make it a genuine hard question, not a hint."
            if self.valves.socratic_follow_up
            else ""
        )

        model_answer_instruction = (
            "\n\n**MODEL ANSWER**\nWrite a full IRAC-structured answer to the hypothetical above. "
            "For each issue: state the issue, state the rule, apply it to the facts (both sides), and conclude. "
            "Hedge where the law is genuinely uncertain. "
            "Flag any majority/minority split and state which rule a bar-prep student should know."
            if self.valves.include_model_answer
            else "\n\n[Model answer suppressed — student is answering independently first.]"
        )

        prompt_context = f"""You are a law school exam hypo generator. A student needs a practice hypothetical.

SUBJECT: {subject.strip()}
DIFFICULTY: {config['label']}
DIFFICULTY DESCRIPTION: {config['description']}
NUMBER OF ISSUES TO INCLUDE: {config['issues']}
REQUIRED TWISTS: {config['twists']}

**INSTRUCTIONS FOR GENERATING THE HYPOTHETICAL:**

1. Write a fact pattern in narrative form (no bullet points). 2–4 paragraphs.
2. The facts must be specific — give names, places, dollar amounts, timelines. Vague hypos are bad teaching.
3. End the fact pattern with 1–3 call-of-the-question prompts. Example: "What claims, if any, does Alice have against Bob? Discuss."
4. Do NOT include any legal analysis in the fact pattern. The facts are neutral — analysis goes in the model answer.
5. The fact pattern should reward students who know the rule AND students who understand the policy behind it.

**HYPO QUALITY CHECKLIST** (satisfy all of these before writing):
- [ ] The facts trigger the core doctrine of {subject.strip()}
- [ ] At least one fact is arguably ambiguous (cuts both ways on an element)
- [ ] The call-of-the-question is open-ended, not "Did X commit battery?" (too narrow)
- [ ] The hypo is self-contained — a student who doesn't know the jurisdiction can still analyze it
- [ ] No party is obviously 100% in the right (that's a policy discussion, not an exam)
{model_answer_instruction}{socratic_instruction}

IMPORTANT: Do NOT fabricate case names or citations in the model answer. Describe rules accurately. If a rule has a common name (e.g., "the Hand Formula"), use it. Otherwise describe the standard."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Hypo ready", "done": True},
                }
            )

        return prompt_context

    async def outline_builder(
        self,
        subject: str,
        topic_list: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Build a study outline — either from scratch for a subject, or organized around a user-provided topic list.
        Produces a hierarchical outline with black-letter rules, elements, exceptions, and exam triggers.

        :param subject: The law school course (e.g., Torts, Contracts, Property).
        :param topic_list: Optional comma-separated or newline-separated list of topics to cover (e.g., "Negligence, Strict Liability, Products Liability"). If empty, the model generates a full-course outline.
        :return: Structured context for the LLM to build the outline.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"Building {subject} outline...", "done": False},
                }
            )

        if not subject or not subject.strip():
            return (
                "Subject is required. Provide the course name (e.g., Torts, Contracts, Property) "
                "and optionally a list of topics to cover."
            )

        topic_instruction = ""
        if topic_list and topic_list.strip():
            # Parse topic list — accept commas or newlines
            raw_topics = [
                t.strip() for t in topic_list.replace("\n", ",").split(",") if t.strip()
            ]
            topics_formatted = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(raw_topics))
            topic_instruction = f"""
STUDENT-PROVIDED TOPICS TO COVER:
{topics_formatted}

Build the outline around these topics in this order. Add any critical sub-topics the student may have missed."""
        else:
            topic_instruction = f"""
No topic list provided. Generate a complete course outline for {subject.strip()} covering all major topics typically tested on law school finals and the bar exam."""

        socratic_instruction = (
            "\n\nAt the end of the outline, pose a SYNTHESIS QUESTION: a hypothetical fact pattern that requires the student to integrate at least 3 topics from the outline. Don't answer it — let the student work through it."
            if self.valves.socratic_follow_up
            else ""
        )

        prompt_context = f"""You are a law school study outline builder. A student needs a structured outline.

SUBJECT: {subject.strip()}
{topic_instruction}

Build the outline using this structure for each topic:

---
## [TOPIC NAME]

**Black-Letter Rule**: [The rule in one or two sentences. Memorizable.]

**Elements / Test**:
1. Element one — definition + what satisfies it
2. Element two — definition + what satisfies it
(continue for all elements)

**Key Exceptions**:
- Exception 1: when the general rule does NOT apply
- Majority vs. minority rule split (if any)
- Restatement/UCC position (if applicable — do not fabricate section numbers)

**Exam Triggers**: What facts in a hypo signal that this doctrine applies? (3–5 bullet points)

**Common Mistakes**: What do students get wrong? (2–3 bullet points, "Most students miss that...")

**Connects To**: Which other topics in this course interact with this one?
---

Repeat this structure for every topic.

OUTLINE QUALITY STANDARDS:
- Every rule must be stated precisely enough to apply to a fact pattern
- Exceptions must be complete (rule → exception → exception-to-exception where it exists)
- Exam triggers must be specific facts, not abstract concepts
- Common mistakes must be real mistakes, not obvious errors
{socratic_instruction}

IMPORTANT: Do NOT invent case names, statute section numbers, or Restatement section numbers. Describe rules accurately. Flag any authority as "verify independently." """

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Outline ready", "done": True},
                }
            )

        return prompt_context

    async def flashcard_set(
        self,
        subject: str,
        topic: str,
        count: int = 20,
        __event_emitter__=None,
    ) -> str:
        """
        Generate flashcard Q&A pairs for a law school topic.
        Cards cover rules, elements, exceptions, policy, and exam applications.
        Mix of recall, application, and policy cards — not just definitions.

        :param subject: The law school course (e.g., Torts, Contracts).
        :param topic: The specific topic within that course (e.g., Negligence Per Se, Battle of the Forms).
        :param count: Number of flashcards to generate (default 20, max 50).
        :return: Structured context for the LLM to generate flashcard Q&A pairs.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Generating {count} flashcards for {subject} > {topic}...",
                        "done": False,
                    },
                }
            )

        if not subject or not subject.strip():
            return "Subject is required (e.g., Torts, Contracts, Property)."
        if not topic or not topic.strip():
            return "Topic is required (e.g., Negligence, Consideration, Search and Seizure)."

        count = max(5, min(int(count), 50))

        # Calculate card type distribution
        recall_count = round(count * 0.40)
        application_count = round(count * 0.35)
        policy_count = count - recall_count - application_count

        prompt_context = f"""You are a law school flashcard generator. A student needs flashcards for:

SUBJECT: {subject.strip()}
TOPIC: {topic.strip()}
TOTAL CARDS REQUESTED: {count}

Generate exactly {count} flashcard Q&A pairs using this distribution:
- {recall_count} RECALL cards: test whether the student knows the rule, element, or definition
- {application_count} APPLICATION cards: present a mini-fact pattern and ask how the rule applies
- {policy_count} POLICY cards: ask why the rule exists or what the tradeoffs are

FORMAT: Output each card as:
---
**Card N** [RECALL / APPLICATION / POLICY]
**Q:** [question]
**A:** [answer]
---

CARD QUALITY STANDARDS:

RECALL cards:
- Q should require more than a one-word answer
- A should include the rule AND its key exception (if any)
- Bad: "Q: What is battery? A: Harmful or offensive contact."
- Good: "Q: What is the intent required for battery? A: Purpose to cause harmful or offensive contact, OR substantial certainty that contact will result. Most students miss that transferred intent applies — intent to commit assault satisfies battery if contact results."

APPLICATION cards:
- Q should be a 2–3 sentence fact pattern ending with "Does the rule apply? Why or why not?"
- A should walk through each element, state which are satisfied, and conclude
- Flag any facts that cut the other way

POLICY cards:
- Q should ask: "Why does the law treat X this way?" or "What's the tension between Rule A and Rule B?"
- A should give the policy rationale AND note which policy arguments cut against the rule
- These cards train students to argue policy, which matters in essays and moot court

IMPORTANT: Do NOT fabricate case names. If a leading case is commonly known (e.g., Palsgraf for proximate cause), you may reference the general concept ("the Palsgraf principle") but do not invent citations or details not established by the student."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"{count} flashcards ready", "done": True},
                }
            )

        return prompt_context
