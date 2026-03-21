"""
title: Virtual Legal Mentor
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: A virtual mentor for new attorneys, associates, and paralegals starting
  their legal career. Covers billing practices, client communication templates, professional
  development guidance, ethics scenarios under the Model Rules, and courtroom basics.
  Runs entirely locally — no API costs, no data leaves your machine.

  Import into Open WebUI: Workspace → Tools → + → paste this file.

  Recommended model: legal-tutor (see Modelfile.legal-tutor) for interactive guidance.

  IMPORTANT: This tool provides general professional guidance and educational content.
  It is NOT a substitute for your firm's policies, your supervising partner, your state
  bar's ethics counsel, or a licensed attorney advisor. For actual ethics opinions,
  contact your state bar's ethics hotline — most provide free guidance to attorneys.
"""

from pydantic import BaseModel


# Common billable task types with typical time ranges
BILLABLE_TASK_REFERENCE = {
    "legal research": ("1-4 hours", "Document every source reviewed, even dead ends"),
    "memo drafting": ("2-6 hours", "Break into research, outline, draft, and revision entries"),
    "contract review": ("0.5-3 hours", "Note length and complexity in your description"),
    "client call": ("0.1-1 hour", "Bill in 0.1 increments; summarize in description"),
    "court appearance": ("varies", "Travel time, preparation, and appearance are separate entries"),
    "deposition": ("3-8 hours", "Prep, travel, and appearance typically billed separately"),
    "email": ("0.1-0.3 hours", "Substantive legal analysis emails may justify more"),
    "document review": ("1-8 hours", "Volume-based; note document count in description"),
    "filing": ("0.2-0.5 hours", "Preparation + filing + confirmation"),
    "scheduling": ("0.1", "Typically non-billable or billed at paralegal rate"),
}

# Model Rules most relevant to new attorneys
RELEVANT_MODEL_RULES = {
    "1.1": "Competence — duty to provide competent representation",
    "1.2": "Scope of representation and allocation of authority between client and lawyer",
    "1.3": "Diligence — act with reasonable diligence and promptness",
    "1.4": "Communication — keep client reasonably informed",
    "1.5": "Fees — must be reasonable; communicate basis in writing",
    "1.6": "Confidentiality — general duty; exceptions for preventing harm",
    "1.7": "Conflict of interest — current clients",
    "1.8": "Conflict of interest — specific prohibited transactions",
    "1.9": "Duties to former clients",
    "1.15": "Safekeeping property — IOLTA, trust accounts",
    "3.3": "Candor toward the tribunal",
    "3.4": "Fairness to opposing party and counsel",
    "5.1": "Supervisory responsibilities of partners/supervisors",
    "5.2": "Subordinate lawyer — following supervisor instructions",
    "8.3": "Reporting professional misconduct",
    "8.4": "Misconduct — the catch-all rule",
}


class Tools:
    class Valves(BaseModel):
        career_stage: str = "new_associate"  # "1l_intern", "new_associate", "paralegal", "2nd_year"
        practice_type: str = "general"  # "litigation", "transactional", "public_interest", "general"
        jurisdiction: str = "general"  # state or "general" for Model Rules

    def __init__(self):
        self.valves = self.Valves()

    async def billing_guidance(
        self,
        task: str,
        __event_emitter__=None,
    ) -> str:
        """
        Get guidance on how to bill a specific legal task.

        Explains how to record time for any legal task: appropriate time estimate,
        how to write a useful billing description, how to handle task splitting,
        and what billing ethics require. Also explains what write-offs are and when
        partners apply them.

        :param task: Describe the task you want billing guidance on (e.g., "I researched for 3 hours and drafted a 5-page memo on tortious interference", "I reviewed 200 emails for discovery", "I attended a 30-minute client call").
        :return: A billing guidance prompt for the LLM to generate.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Preparing billing guidance...", "done": False},
                }
            )

        # Look for task type hints in the description
        task_lower = task.lower()
        matched_reference = ""
        for task_key, (time_range, tip) in BILLABLE_TASK_REFERENCE.items():
            if task_key in task_lower:
                matched_reference = f"\nTypical time range for {task_key}: {time_range}. Note: {tip}"
                break

        stage_context = {
            "1l_intern": "a 1L law student working as a summer intern",
            "new_associate": "a first-year associate (0-12 months at the firm)",
            "paralegal": "a paralegal",
            "2nd_year": "a second or third-year associate",
        }.get(self.valves.career_stage, "a new associate")

        prompt = f"""Provide billing guidance for the following task, written for {stage_context}.

TASK TO BILL: {task}{matched_reference}

Address these questions:

**HOW TO RECORD THIS TIME**
1. What is a reasonable time entry for this task? What factors affect the appropriate duration?
2. How should the time be broken into components (research, drafting, review, calls, etc.)?
3. What billing increment is standard? (Most firms use 0.1 = 6 minutes)

**WRITING A GOOD BILLING DESCRIPTION**
Write 2-3 example time entries for this task:
- One that is too vague (and explain why it's a problem)
- One that is appropriate
- One that is overly specific (and when that might be acceptable)

A good billing description answers: What did I do? On what matter? What was the result or output?

**BILLING ETHICS**
- What does ABA Model Rule 1.5 require about fees?
- What does "billing judgment" mean and how does it apply here?
- What's the difference between padding, rounding up, and legitimate discretion?
- When should time NOT be billed (learning curve for new associates)?

**WRITE-OFFS AND WRITE-DOWNS**
- What is a write-off and when do partners apply them?
- Why do partners write off time from new associates, and what does that mean for how you should think about your entries?
- Should you bill time even if you think it might get written off?

**FIRM PRACTICES** (general guidance — follow your specific firm's policy)
- Who approves time entries?
- When should entries be submitted (end of day is best practice)?
- What matters need matter numbers?

**ONE KEY RULE**
What's the most important billing principle for a {stage_context} to internalize in their first year?

Tone: Direct, practical, non-judgmental. New attorneys often feel embarrassed asking about billing — normalize it."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Billing guidance ready", "done": True},
                }
            )

        return prompt

    async def client_communication(
        self,
        situation: str,
        communication_type: str = "email",
        __event_emitter__=None,
    ) -> str:
        """
        Get templates and guidance for client communications.

        Produces a draft communication plus coaching on tone, content, and professional
        norms for interacting with clients. Covers emails, call summaries, status updates,
        bad news delivery, and more.

        :param situation: Describe the client communication situation (e.g., "client is asking for a status update on their contract negotiation", "I need to deliver bad news that we lost the motion", "new client intake — setting expectations for a personal injury case").
        :param communication_type: The format: "email", "letter", "call_summary", "voicemail_script", or "in_person_guidance".
        :return: A client communication guidance prompt for the LLM to generate.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Drafting communication guidance...", "done": False},
                }
            )

        format_map = {
            "email": "a professional email",
            "letter": "a formal client letter",
            "call_summary": "a post-call summary email",
            "voicemail_script": "a voicemail script",
            "in_person_guidance": "an in-person meeting or conversation",
        }
        format_label = format_map.get(communication_type.lower(), "a professional email")

        prompt = f"""Help a {self.valves.career_stage.replace("_", " ")} draft {format_label} for the following situation, and explain the professional norms involved.

SITUATION: {situation}
FORMAT: {format_label}

Provide:

**DRAFT COMMUNICATION**
Write a complete, ready-to-use draft. Include subject line if it's an email.
Flag any placeholders in [BRACKETS] that need to be filled in.

**WHAT MAKES THIS COMMUNICATION EFFECTIVE**
Explain the specific choices made in the draft:
- Tone (why this level of formality?)
- Structure (why open with X, close with Y?)
- What was deliberately NOT included and why

**THE MODEL RULE 1.4 OBLIGATION**
How does this communication fulfill (or relate to) the duty to keep clients reasonably informed? What's the minimum a client should receive by way of communication, and when?

**PROFESSIONAL NORMS**
- Who should review this communication before it goes out? (Senior associate? Partner?)
- Is this the kind of thing a new associate sends on their own, or does it need approval?
- What's the turnaround time norm for client emails? Calls?

**WATCH-OUTS**
- What could go wrong with this type of communication?
- What information should NEVER be put in a client email?
- Attorney-client privilege: does this communication affect it?

**ADJUSTED VERSION FOR DIFFERENT AUDIENCES**
If the client is a sophisticated business client vs. an individual non-lawyer client, how would the tone and level of detail change? Show the adjustment.

Tone: Professional but approachable. The goal is to model what good attorney-client communication looks like."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Communication guidance ready", "done": True},
                }
            )

        return prompt

    async def professional_development(
        self,
        area: str = "general",
        __event_emitter__=None,
    ) -> str:
        """
        Get professional development guidance for building your legal career.

        Covers what skills to develop at each career stage, which CLEs to prioritize,
        how to get good work, how to build relationships in the firm, and how to think
        about career progression from associate to partner (or other paths).

        :param area: Focus area: "general" (first-year priorities), "skills" (specific skill development), "cle" (continuing legal education guidance), "relationships" (working with partners and colleagues), "career_paths" (associate to partner and alternatives), or "feedback" (how to get and use feedback).
        :return: A professional development guidance prompt for the LLM to generate.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Preparing professional development guidance...", "done": False},
                }
            )

        area_map = {
            "general": "a comprehensive overview of professional priorities for the first year",
            "skills": "the most important practical skills to develop and how to develop them",
            "cle": "continuing legal education — what CLEs matter, how to approach CLE requirements, and free/low-cost options",
            "relationships": "building relationships with partners, senior associates, and colleagues — the social architecture of a law firm",
            "career_paths": "career trajectory options (BigLaw to boutique, in-house, government, public interest, entrepreneurship) and how early decisions affect them",
            "feedback": "how to seek, receive, and act on feedback from supervisors — and why most new associates fail to do this well",
        }
        focus = area_map.get(area.lower(), area_map["general"])

        practice_context = {
            "litigation": "litigation practice (trial work, motion practice, discovery)",
            "transactional": "transactional practice (deals, contracts, corporate work)",
            "public_interest": "public interest or government practice",
            "general": "general legal practice",
        }.get(self.valves.practice_type, "general legal practice")

        prompt = f"""Provide professional development guidance focused on {focus}, for a {self.valves.career_stage.replace('_', ' ')} in {practice_context}.

Structure your guidance as:

**THE MOST IMPORTANT THING**
What's the single most important professional development priority for this person right now, and why?

**PRACTICAL SKILLS TO BUILD (First 12 Months)**
Specific, learnable skills — not vague advice like "communicate better." For each:
- What the skill is
- Why it matters at this career stage
- How to actually build it (concrete methods)
- How you'll know you're improving

**LEARNING ON THE JOB**
- How do you learn from every assignment? What habits separate the associates who develop fast from those who plateau?
- How do you turn feedback (even indirect feedback, like a heavily marked-up draft) into systematic improvement?
- When should you ask questions vs. figure it out yourself? How do you calibrate this?

**CLE AND FORMAL LEARNING**
- What CLE requirements apply (general guidance — check your state bar)?
- Which practice-area CLEs are worth prioritizing?
- Free and low-cost CLE options (bar association, law school alumni programs, webinars)
- Legal writing and research courses worth taking post-law-school

**RELATIONSHIPS AND REPUTATION**
- How do you build a reputation as someone who does good work?
- What does it mean to be a "reliable" associate? Why is reliability more valuable than brilliance early on?
- How do you build relationships with partners who give good mentorship and interesting work?
- What's the right way to ask for feedback?

**CAREER-STAGE REALISTIC ASSESSMENT**
- What does "success" look like at this stage? (Hint: it's not making partner — that's 8-10 years away)
- What decisions in the first 1-2 years have outsized impact on future options?
- Common mistakes that derail otherwise talented attorneys early in their careers

Tone: Honest and direct. This person is trying to build a career, not just get through the first year."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Guidance ready", "done": True},
                }
            )

        return prompt

    async def ethics_scenario(
        self,
        scenario: str,
        __event_emitter__=None,
    ) -> str:
        """
        Analyze an ethics scenario under the ABA Model Rules of Professional Conduct.

        Presents the competing obligations, identifies the applicable Model Rules,
        analyzes the required or permitted conduct, and notes when to seek formal ethics
        counsel. This is educational analysis — not a formal ethics opinion.

        :param scenario: Describe the ethics situation (e.g., "My supervising partner asked me to backdate a document", "A client told me they're planning to commit fraud — what do I do?", "I accidentally received opposing counsel's privileged documents by email").
        :return: An ethics analysis prompt for the LLM to execute.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Analyzing ethics scenario...", "done": False},
                }
            )

        rules_reference = "\n".join(
            [f"- Rule {num}: {desc}" for num, desc in RELEVANT_MODEL_RULES.items()]
        )

        prompt = f"""Analyze the following professional ethics scenario under the ABA Model Rules of Professional Conduct. This is for educational purposes for a {self.valves.career_stage.replace('_', ' ')}.

SCENARIO: {scenario}

APPLICABLE RULES REFERENCE:
{rules_reference}

Provide a thorough analysis:

**IMMEDIATE ISSUE IDENTIFICATION**
What are the core ethical concerns raised by this scenario? List them clearly before diving into analysis.

**APPLICABLE MODEL RULES**
For each relevant rule:
- Which rule applies and why
- What the rule requires, permits, or prohibits
- Any relevant exceptions or nuances
- If this is a jurisdiction-specific area, note that the analysis may differ from state rules

**THE TENSION (if any)**
Many ethics scenarios involve competing obligations (e.g., duty of confidentiality vs. duty of candor to court, duty to client vs. duty to report misconduct). Identify and analyze any such tension.

**WHAT MUST OR SHOULD YOU DO**
Break down the required and discretionary actions:
- What is REQUIRED (failure = rule violation)?
- What is PERMITTED (lawyer has discretion)?
- What is PROHIBITED?
- What is BEST PRACTICE beyond the minimum?

**THE SUBORDINATE ATTORNEY ISSUE** (Rule 5.2)
When a supervisor asks something ethically questionable:
- Under Rule 5.2, when can a subordinate follow a supervisor's instruction?
- When does "I was following orders" NOT protect a subordinate attorney?
- What should the subordinate do before simply complying?

**CONCRETE NEXT STEPS**
Given this scenario, what should the attorney do RIGHT NOW? In order:
1. Immediate action
2. Documentation
3. Escalation (who to tell, if anyone)
4. Formal resources to consult

**WHEN TO CALL THE STATE BAR ETHICS HOTLINE**
- Does this situation warrant a formal ethics inquiry?
- Most state bars offer free, confidential ethics guidance to attorneys — encourage use of this resource
- ABA Ethics Hotline: 1-800-285-2221

DISCLAIMER: This analysis is educational and not a formal ethics opinion. Ethics rules vary by jurisdiction. For actual ethics guidance, contact your state bar's ethics counsel or consult a legal ethics specialist. When in doubt, don't act until you've gotten proper guidance."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Ethics analysis ready", "done": True},
                }
            )

        return prompt

    async def courtroom_basics(
        self,
        proceeding_type: str = "first_hearing",
        __event_emitter__=None,
    ) -> str:
        """
        Get practical guidance for courtroom appearances and legal proceedings.

        Covers what to expect at your first hearing, deposition, trial, or other
        proceeding — protocol, preparation, common mistakes, and what nobody tells
        new attorneys before they walk through the courthouse doors.

        :param proceeding_type: Type of proceeding: "first_hearing" (any motion/status hearing), "deposition" (taking or defending), "jury_selection", "opening_statement", "direct_exam", "cross_exam", "closing_argument", "trial_day_one", or "bench_trial".
        :return: A courtroom preparation prompt for the LLM to generate.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Preparing courtroom guidance...", "done": False},
                }
            )

        proceeding_descriptions = {
            "first_hearing": "a first court appearance (status conference, scheduling conference, or motion hearing)",
            "deposition": "taking or defending a deposition",
            "jury_selection": "jury selection (voir dire)",
            "opening_statement": "delivering an opening statement",
            "direct_exam": "direct examination of a witness",
            "cross_exam": "cross-examination of an adverse witness",
            "closing_argument": "delivering a closing argument",
            "trial_day_one": "the first day of trial",
            "bench_trial": "a bench trial (trial before a judge without a jury)",
        }
        proceeding_label = proceeding_descriptions.get(
            proceeding_type.lower(), proceeding_type
        )

        prompt = f"""Prepare a new attorney ({self.valves.career_stage.replace('_', ' ')}, {self.valves.practice_type} practice) for {proceeding_label}.

Cover everything they need to know before walking in:

**BEFORE THE PROCEEDING — PREPARATION**
- What do you need to have done before walking in the door?
- What documents to bring, what to review, what to have memorized vs. what can be referenced
- What to wear, what to carry, how to arrive (how early?)
- Pre-proceeding logistics that new attorneys often miss (where is the courtroom? How do you check in? Who do you introduce yourself to?)

**THE PROTOCOL — WHAT ACTUALLY HAPPENS**
Walk through the proceeding step by step:
- Who speaks when?
- What is the correct way to address the judge? ("Your Honor," "the Court")
- How do you handle objections?
- What do court reporters and clerks need from you?
- What surprises commonly catch new attorneys off guard?

**THE SUBSTANCE**
What are you actually trying to accomplish in this proceeding? What does "success" look like? What's the most common way attorneys lose ground they shouldn't lose?

**WHAT NOBODY TELLS YOU**
The informal knowledge that isn't in any textbook:
- Local rules and local practices that differ from the federal/state rules
- Courtroom demeanor — what judges notice, what annoys them
- How to handle a moment when you don't know the answer
- What to do when opposing counsel does something surprising or improper
- The body language and presence norms of the courtroom

**REAL MISTAKES NEW ATTORNEYS MAKE**
Specific, common, avoidable mistakes. Be concrete — not "be prepared" but "don't walk in without having read the local rules on motion formatting."

**AFTER THE PROCEEDING**
- What needs to be documented immediately after?
- What do you communicate to the client?
- What follow-up actions are typically triggered?

**ONE THING TO REMEMBER**
The single most important mindset or principle for this proceeding type.

Tone: Like a good senior associate briefing you the night before. Practical, honest, no padding."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Courtroom guidance ready", "done": True},
                }
            )

        return prompt
