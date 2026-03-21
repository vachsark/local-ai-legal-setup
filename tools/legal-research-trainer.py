"""
title: Legal Research Trainer
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Teaches legal research methodology to law students, new associates, and
  paralegals. Covers research strategy, Bluebook citation format, how to verify case
  status (Shepardizing concepts), and source hierarchy (binding vs. persuasive authority).
  Runs entirely locally — no API costs, no Westlaw/Lexis access required.

  Import into Open WebUI: Workspace → Tools → + → paste this file.

  Recommended model: legal-tutor (Socratic mode) or qwen3.5:9b for direct instruction.

  NOTE: This tool teaches research methodology, not substantive law. It cannot access
  Westlaw, Lexis, Google Scholar, or any external database. Treat all procedural
  guidance as general instruction — always verify current rules for your jurisdiction.
"""

from pydantic import BaseModel


# Jurisdiction categories for binding authority analysis
FEDERAL_COURTS = ["supreme court", "circuit court", "district court", "court of appeals"]
JURISDICTION_TYPES = {
    "federal": "federal courts applying federal law",
    "state": "state courts applying state law",
    "diversity": "federal courts applying state law under diversity jurisdiction",
    "administrative": "federal or state administrative agencies",
}

# Primary vs secondary source classifications
SOURCE_HIERARCHY = {
    "binding_primary": [
        "constitutions (federal or applicable state)",
        "statutes (federal or applicable state)",
        "regulations (federal or applicable state)",
        "controlling case law (same jurisdiction, higher court)",
    ],
    "persuasive_primary": [
        "case law from other jurisdictions",
        "case law from lower courts in same jurisdiction",
        "dicta from binding cases",
        "unpublished opinions (jurisdiction-dependent)",
    ],
    "secondary_sources": [
        "law review articles and journals",
        "treatises (e.g., Moore's Federal Practice, Wigmore on Evidence)",
        "Restatements (ALI)",
        "legal encyclopedias (Am. Jur., C.J.S.)",
        "practice guides and form books",
        "ALR annotations",
        "bar association ethics opinions",
    ],
}

# Common Bluebook formats
BLUEBOOK_FORMATS = {
    "supreme_court_case": 'Brown v. Board of Education, 347 U.S. 483 (1954)',
    "circuit_case": 'Smith v. Jones, 234 F.3d 567 (9th Cir. 2001)',
    "district_case": 'Doe v. Roe, 123 F. Supp. 3d 456 (S.D.N.Y. 2015)',
    "state_case": 'People v. Davis, 45 Cal. 4th 1234, 201 P.3d 456 (2009)',
    "federal_statute": '42 U.S.C. § 1983 (2018)',
    "state_statute": 'Cal. Civ. Code § 1714 (West 2024)',
    "regulation": '29 C.F.R. § 1604.11 (2023)',
    "law_review": 'Jane Author, Article Title, 100 Harv. L. Rev. 1 (1987)',
    "restatement": 'Restatement (Second) of Torts § 402A (Am. L. Inst. 1965)',
    "constitution": 'U.S. Const. art. I, § 8, cl. 3',
}


class Tools:
    class Valves(BaseModel):
        experience_level: str = "new"  # "student", "new", "paralegal"
        include_database_tips: bool = True  # tips on Westlaw/Lexis even though we can't access them
        bluebook_edition: str = "21st"  # current Bluebook edition

    def __init__(self):
        self.valves = self.Valves()

    async def research_strategy(
        self,
        legal_question: str,
        jurisdiction: str = "federal",
        __event_emitter__=None,
    ) -> str:
        """
        Outline a complete legal research strategy for any legal question.

        Given a legal question, this generates a step-by-step research plan covering:
        which sources to consult first, recommended search terms, how to move from
        secondary to primary sources, and how to know when you're done.

        :param legal_question: The legal question you need to research (e.g., "Can an employer terminate an employee for off-duty social media posts?").
        :param jurisdiction: The jurisdiction for the research (e.g., "federal", "california", "new york", "texas").
        :return: A complete research strategy prompt for the LLM to execute.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Building research strategy...", "done": False},
                }
            )

        level_map = {
            "student": "a law student in their first or second year",
            "new": "a new associate or recent law school graduate",
            "paralegal": "an experienced paralegal with some legal research background",
        }
        audience = level_map.get(self.valves.experience_level, "a new associate")

        db_note = ""
        if self.valves.include_database_tips:
            db_note = """
**Database Tips**: Include brief guidance on where in Westlaw or Lexis to start (e.g., "Start with a secondary source search in Westlaw's Practice Guides" or "Use Lexis Practice Advisor for [area]"). Acknowledge that actual database access is separate from this planning step."""

        prompt = f"""Create a complete legal research strategy for the following question, written for {audience}.

LEGAL QUESTION: {legal_question}
JURISDICTION: {jurisdiction}

Structure your response as a step-by-step research plan:

**STEP 1 — ISSUE FRAMING**
Before researching, frame the legal question precisely. What is the specific legal issue? What are the key facts that would affect the legal outcome? What terms of art should be used (not lay language)?

**STEP 2 — IDENTIFY CONTROLLING SOURCES**
What type of law governs this issue (constitutional, statutory, common law, regulatory)? Which court or body has final authority? What is the hierarchy of authority in {jurisdiction} for this type of question?

**STEP 3 — START WITH SECONDARY SOURCES**
Which secondary sources should be consulted first and why? Be specific:
- What treatise or practice guide covers this area?
- Is there a relevant Restatement section?
- Are there useful law review articles or ALR annotations?
- What legal encyclopedia entries apply?
Why start here before jumping to cases?
{db_note}

**STEP 4 — PRIMARY SOURCE RESEARCH**
- What statutes or regulations control this issue? How would you find them?
- What constitutional provisions (if any) are relevant?
- What case law do you need? What courts? What time period?

**STEP 5 — SEARCH TERMS**
Generate 3 sets of search terms:
- Natural language searches (for Westlaw/Lexis natural language mode)
- Boolean/terms-and-connectors searches (e.g., "employ! /s terminat! /p social media")
- Alternative terms (synonyms, related concepts, terms of art vs. lay terms)

**STEP 6 — VERIFICATION**
How do you verify that cases are still good law? What signals indicate a case may have been overruled or limited? What does it mean to "Shepardize" or "KeyCite" a case?

**STEP 7 — KNOWING WHEN YOU'RE DONE**
How does a researcher know when they've found enough? What does "research saturation" look like? What should the research memo document about the research process?

**COMMON TRAPS IN THIS AREA**
What are the most common research mistakes for this type of question?

IMPORTANT: Do not fabricate specific case names or statutory citations. Describe research methodology using the structure and types of sources, not invented authorities."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Research strategy ready", "done": True},
                }
            )

        return prompt

    async def bluebook_citation(
        self,
        source_description: str,
        citation_type: str = "case",
        __event_emitter__=None,
    ) -> str:
        """
        Generate a proper Bluebook citation and explain the format rules.

        Given a description of a legal source, produces a correctly formatted Bluebook
        citation and teaches the underlying format rules so you can apply them independently.
        Uses the current Bluebook (21st edition) rules.

        :param source_description: Description of what you need to cite (e.g., "a 2019 Ninth Circuit case, page 456 of volume 234 of F.3d" or "42 U.S.C. section 1983").
        :param citation_type: Type of source: "case", "statute", "regulation", "constitution", "law_review", "book", "restatement", or "other".
        :return: A Bluebook citation instruction prompt for the LLM to execute.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Building citation guidance...", "done": False},
                }
            )

        # Show relevant examples for this citation type
        example_key = None
        type_map = {
            "case": ["supreme_court_case", "circuit_case", "district_case", "state_case"],
            "statute": ["federal_statute", "state_statute"],
            "regulation": ["regulation"],
            "constitution": ["constitution"],
            "law_review": ["law_review"],
            "restatement": ["restatement"],
        }
        relevant_examples = []
        for ex_key in type_map.get(citation_type.lower(), []):
            if ex_key in BLUEBOOK_FORMATS:
                relevant_examples.append(f"  {ex_key.replace('_', ' ').title()}: {BLUEBOOK_FORMATS[ex_key]}")

        examples_block = ""
        if relevant_examples:
            examples_block = "\n\nRelevant Bluebook format examples for reference:\n" + "\n".join(relevant_examples)

        prompt = f"""Generate a proper Bluebook ({self.valves.bluebook_edition} edition) citation for the following source, and teach the format rules.

SOURCE TO CITE: {source_description}
CITATION TYPE: {citation_type}
{examples_block}

Provide:

**FORMATTED CITATION**
Write the complete, correctly formatted Bluebook citation. If any information is missing from the description, note what's needed and show the citation with [MISSING: field] placeholders.

**FORMAT RULES EXPLAINED**
Break down the citation element by element:
- What does each component mean?
- What are the punctuation and spacing rules?
- What abbreviations are required (Bluebook Table abbreviations)?
- What would make this citation wrong? (Most common formatting errors for this source type)

**FULL CITATION vs. SHORT CITATION**
If this source will be cited more than once in a document:
- Show the full citation (first reference)
- Show the proper short citation form (subsequent references)
- When is "id." appropriate vs. a short citation?

**PRACTITIONER FORMAT vs. ACADEMIC FORMAT**
Bluebook has two formats — academic (law review footnotes) and practitioner (court documents, memos). Show both if they differ for this source type, and explain when to use each.

**PINPOINT CITATIONS**
Explain how to add a pinpoint citation (specific page) to this source type.

**COMMON MISTAKES**
List 3 common errors students make with this citation type.

IMPORTANT: Use real Bluebook rules. If the source description is ambiguous or incomplete, ask clarifying questions rather than guessing. A wrong citation in a court filing is a professional failure."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Citation guidance ready", "done": True},
                }
            )

        return prompt

    async def shepardizing_guide(
        self,
        concept: str = "general",
        __event_emitter__=None,
    ) -> str:
        """
        Explain how to verify a case is still good law (Shepardizing / KeyCiting).

        Covers the concepts and process of case validation — what the signals mean,
        what to look for, and how to decide if a case is safe to rely on.
        Note: This teaches the methodology; actual Shepard's/KeyCite requires Lexis/Westlaw access.

        :param concept: Specific aspect to focus on: "general" (full overview), "signals" (meaning of Shepard's signals), "negative treatment" (how to read negative history), or "depth of treatment" (how much a citing case matters).
        :return: A Shepardizing instruction prompt for the LLM to execute.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Preparing Shepardizing guide...", "done": False},
                }
            )

        focus_map = {
            "general": "Provide a complete overview of the Shepardizing / KeyCiting process.",
            "signals": "Focus specifically on the meaning of Shepard's signals (red stop sign, yellow flag, orange Q, blue circle, etc.) and KeyCite signals (red flag, yellow flag, blue stripe). Explain what each means, what action it requires, and common misconceptions.",
            "negative treatment": "Focus on negative treatment — what 'distinguished,' 'limited,' 'criticized,' 'questioned,' 'overruled,' and 'superseded' mean, and how to evaluate whether negative treatment affects your ability to rely on the case.",
            "depth of treatment": "Focus on depth of treatment — what the 1-4 star depth signals mean in Shepard's and how to use depth of treatment to prioritize which citing references to read.",
        }
        focus_instruction = focus_map.get(concept.lower(), focus_map["general"])

        prompt = f"""Explain how to verify that a legal case is still good law using Shepard's Citations (Lexis) and KeyCite (Westlaw).

{focus_instruction}

Cover the following topics as appropriate:

**WHY THIS MATTERS**
Explain the professional obligation to verify case status (FRCP 11, state equivalents, malpractice risk). What happens if an attorney cites overruled precedent?

**SHEPARD'S CITATIONS (Lexis)**
- How to access Shepard's for a case
- What the signals mean (red, yellow, orange, blue)
- How to read the citing references list
- How to filter by jurisdiction and treatment type
- What "overruled in part" means vs. "overruled"

**KEYCITE (Westlaw)**
- How to access KeyCite
- What the flags mean (red, yellow, blue stripe)
- The depth of treatment stars (how much a citing case discusses your case)
- How to set a KeyCite alert for future changes

**READING NEGATIVE HISTORY**
When a case has negative treatment:
- Does it affect YOUR use of the case?
- The case may be overruled on point A but still good law on point B — how do you evaluate this?
- What questions to ask when you see a yellow or red signal

**FREE ALTERNATIVES (for students without Lexis/Westlaw access)**
- Google Scholar's "How cited" feature
- CourtListener and the Free Law Project
- Limitations of free tools compared to commercial citators

**STEP-BY-STEP CHECKLIST**
A 5-step process for verifying a case before citing it in any document.

NOTE: This is educational content about methodology. The student needs actual Lexis or Westlaw access (or law school library access) to run a real Shepard's or KeyCite check."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Guide ready", "done": True},
                }
            )

        return prompt

    async def source_hierarchy(
        self,
        jurisdiction: str,
        issue_type: str = "common law",
        __event_emitter__=None,
    ) -> str:
        """
        Explain which legal sources are binding vs. persuasive for a given jurisdiction and issue.

        Produces a clear authority hierarchy map showing which courts and sources control,
        which are merely persuasive, and how to argue from non-binding authority when
        binding authority is absent or unclear.

        :param jurisdiction: The court or jurisdiction you're researching for (e.g., "9th Circuit", "California state court", "Texas federal district court", "New York family court").
        :param issue_type: The type of legal issue: "common law", "statutory", "constitutional", "regulatory", or "procedural".
        :return: An authority hierarchy analysis prompt for the LLM to execute.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Mapping authority hierarchy...", "done": False},
                }
            )

        # Build source type context
        source_types = "\n".join(
            [f"  - {s}" for s in SOURCE_HIERARCHY["binding_primary"]]
        )
        secondary_list = "\n".join(
            [f"  - {s}" for s in SOURCE_HIERARCHY["secondary_sources"]]
        )

        prompt = f"""Explain the hierarchy of legal authority for the following situation, from most binding to least authoritative.

JURISDICTION: {jurisdiction}
ISSUE TYPE: {issue_type}

Map out the complete authority structure:

**TIER 1 — MANDATORY/BINDING AUTHORITY**
What sources MUST the court follow? List them in order of supremacy:
- Constitutional provisions (federal/state)
- Statutes
- Regulations
- Controlling case law (which courts are "above" this court?)

**TIER 2 — PERSUASIVE AUTHORITY (often cited, not binding)**
What sources may influence the court but are not controlling?
- Cases from coordinate courts (same level, different circuit/district)
- Cases from lower courts
- Cases from other jurisdictions
- Dicta from binding cases
- Restatements and their relationship to case law in this jurisdiction

**TIER 3 — SECONDARY SOURCES (for background, never as authority)**
When are secondary sources cited in briefs vs. never cited?

**THE DIVERSITY JURISDICTION WRINKLE** (if applicable)
If this is a federal court sitting in diversity, explain the Erie doctrine: when does federal vs. state law apply? What's the basic Erie analysis?

**VERTICAL VS. HORIZONTAL STARE DECISIS**
- Vertical: lower courts follow higher courts in the same system
- Horizontal: courts generally follow their own prior decisions (but can depart — explain when/how)
- How does this apply in {jurisdiction}?

**ARGUING WITHOUT CONTROLLING AUTHORITY**
When there's no binding case on point:
1. How do you argue by analogy from the closest controlling case?
2. When is it appropriate to cite other circuits/states?
3. What makes one persuasive authority stronger than another?
4. How do you argue from secondary sources (Restatements, law reviews) without overstating their weight?

**PRACTICAL TIPS FOR {jurisdiction.upper()}**
Any jurisdiction-specific quirks in how courts treat authority? (e.g., some state courts follow the Restatement closely; some circuits are resistant to out-of-circuit citations)

IMPORTANT: Describe authority rules by principle. Do not fabricate specific jurisdictional rules you are uncertain about — flag any uncertainty clearly."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Authority map ready", "done": True},
                }
            )

        return prompt
