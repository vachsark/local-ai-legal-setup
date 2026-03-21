"""
title: First-Year Survival
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: The stuff law school doesn't teach. Practical tools for new attorneys
  navigating their first year: billing guidance, professional email drafting, research
  methodology, and (most importantly) how to handle mistakes without destroying your career.

  This is not about legal doctrine. It's about surviving — and eventually thriving —
  in the actual practice of law.

  Runs entirely locally — no API costs, no data leaves your machine.

  Import into Open WebUI: Workspace → Tools → + → paste this file.

  Recommended models:
  - legal-tutor: Interactive Q&A and Socratic coaching
  - qwen3.5:9b: Structured guides and email drafts
  - gemma3:12b: Longer scenario analysis

  NOTE: Firm practices vary significantly. The guidance here represents common practices —
  not universal rules. When in doubt, ask your supervising attorney. They know your firm's
  actual expectations; this tool doesn't.
"""

from pydantic import BaseModel


# Common billable task types with typical time ranges and billing norms
BILLING_TASK_PROFILES = {
    "research": {
        "description": "Legal research on a specific question",
        "typical_range": "1-6 hours (depending on complexity)",
        "billing_unit": "0.1 hour (6-minute) increments",
        "common_mistakes": [
            "Billing for learning the basics of an area you should already know",
            "Block billing all research time as one entry",
            "Not capturing time contemporaneously — reconstructing at end of week",
        ],
        "what_partners_expect": "A memo or summary of findings — not just 'research completed'",
    },
    "drafting": {
        "description": "Drafting a document (memo, brief, contract, motion)",
        "typical_range": "2-12 hours depending on document type and complexity",
        "billing_unit": "0.1 hour increments",
        "common_mistakes": [
            "Billing for time spent learning a document type you'll bill repeatedly",
            "Not separating drafting from review/revise in time entries",
            "Forgetting to bill for table of contents, exhibits assembly",
        ],
        "what_partners_expect": "Document with tracking, summary of major drafting choices, flags for partner review",
    },
    "review": {
        "description": "Reviewing documents (contracts, discovery, case files)",
        "typical_range": "0.5-8 hours depending on volume",
        "billing_unit": "0.1 hour increments; document review often in .5 increments per document",
        "common_mistakes": [
            "Billing 'document review' without specifying what was reviewed",
            "Double-billing — billing to review a document you drafted",
            "Not tracking documents reviewed for your log",
        ],
        "what_partners_expect": "Review summary or annotated document; flag issues found",
    },
    "client-call": {
        "description": "Call with a client",
        "typical_range": "0.3-2 hours",
        "billing_unit": "Round to nearest 0.1 — a 7-minute call is 0.2, not 0.1",
        "common_mistakes": [
            "Forgetting to bill call prep time (reviewing file before the call)",
            "Not billing for post-call note-taking and follow-up tasks",
            "Not opening a call log entry in the file",
        ],
        "what_partners_expect": "Call notes in the file; action items from the call tracked and assigned",
    },
    "court-appearance": {
        "description": "Appearing in court (hearing, argument, trial)",
        "typical_range": "Actual hearing time + 2-3 hours minimum for prep, travel, waiting",
        "billing_unit": "Bill actual time; some firms have a minimum court appearance charge — check policy",
        "common_mistakes": [
            "Forgetting to bill waiting time in court (it's still your time)",
            "Not billing for post-hearing debrief with client or partner",
            "Under-billing prep time because it 'feels like' it should have been faster",
        ],
        "what_partners_expect": "Post-hearing memo summarizing what happened and next steps",
    },
    "deposition": {
        "description": "Taking or defending a deposition",
        "typical_range": "4-10 hours (prep, travel, depo, debrief)",
        "billing_unit": "0.1 hour increments; prep, travel, and depo are separate entries",
        "common_mistakes": [
            "Combining prep and depo time into one block entry",
            "Forgetting travel time (verify firm policy — some bill it at a reduced rate)",
            "Not billing for depo outline preparation if you did it",
        ],
        "what_partners_expect": "Deposition summary within 48 hours; key admissions and issues flagged",
    },
    "email": {
        "description": "Drafting or reviewing significant emails",
        "typical_range": "0.2-1 hour per substantive email thread",
        "billing_unit": "Do NOT bill 0.1 for every email received — batch email review is acceptable",
        "common_mistakes": [
            "Not billing at all (a 40-minute email to opposing counsel is billable)",
            "Billing for administrative emails (scheduling, logistics) that aren't client work",
            "Billing separately for every email in a rapid-fire exchange that should be one entry",
        ],
        "what_partners_expect": "Key emails saved to matter file; no substantive client advice over personal email",
    },
}

EMAIL_SCENARIOS = {
    "status-update": {
        "description": "Status update to client",
        "key_elements": ["What has happened", "What is pending", "Next steps and timeline", "Any action needed from client"],
        "tone": "Reassuring and specific — 'I am working on it' is worse than no update",
        "pitfalls": ["Being so vague the client still doesn't know what's happening", "Making promises about timeline you can't keep", "Burying bad news in the middle"],
    },
    "extension-request": {
        "description": "Requesting an extension from opposing counsel or the court",
        "key_elements": ["Specific deadline you need extended", "The new deadline you're requesting", "Professional courtesy reciprocation offer (opposing counsel)", "Reason (brief — you don't owe a full explanation)"],
        "tone": "Professional, matter-of-fact — not apologetic or overly explanatory",
        "pitfalls": ["Waiting until the last minute", "Not confirming in writing after a phone agreement", "Forgetting to get court approval when required"],
    },
    "client-intake": {
        "description": "First substantive email to a new client",
        "key_elements": ["Welcome and confirmation of representation scope", "Next steps and what you need from them", "Timeline expectations", "Engagement letter reference"],
        "tone": "Professional but warm — first impressions set the relationship",
        "pitfalls": ["Over-promising on timeline", "Not including the engagement letter or conflict disclosure", "Legal jargon that the client won't understand"],
    },
    "opposing-counsel": {
        "description": "Correspondence with opposing counsel",
        "key_elements": ["Clear statement of your position or request", "Supporting basis (brief)", "Response requested / deadline", "Professional close"],
        "tone": "Firm and professional — adversarial in substance, not in tone",
        "pitfalls": ["Threatening language that sounds unprofessional", "Admissions about your client's position", "Not BCCing your supervising partner on first contact"],
    },
    "partner-update": {
        "description": "Status update to supervising partner",
        "key_elements": ["What you completed", "What you found / what the issue is", "Your recommendation / next step", "Any flags or questions"],
        "tone": "Efficient — partners are busy; bottom line up front",
        "pitfalls": ["Burying the important information in the middle", "Asking for guidance without attempting a recommendation first", "Making the partner read a wall of text for a simple update"],
    },
    "court-filing": {
        "description": "Notifying the court clerk or coordinating a filing",
        "key_elements": ["Case name and number", "What is being filed and why", "Service confirmation", "Request for confirmation of receipt"],
        "tone": "Formal and precise — courts have procedures and clerks have preferences",
        "pitfalls": ["Not confirming the filing was received", "Missing local rules about electronic vs. paper filing", "Not copying all required parties"],
    },
    "mistake": {
        "description": "Disclosing a professional mistake to a supervising attorney",
        "key_elements": ["What happened (factual, no editorializing)", "Potential impact (be honest)", "What you've already done to mitigate", "What you need help with"],
        "tone": "Direct and calm — do not bury the lead, do not be defensive",
        "pitfalls": ["Waiting to tell them", "Minimizing the impact", "Not having a proposed solution ready", "Sending this to anyone other than your immediate supervisor first"],
    },
}

MISTAKE_CATEGORIES = {
    "missed-deadline": {
        "severity": "Critical — potential malpractice",
        "first_call": "Supervising partner — immediately, not after business hours",
        "immediate_steps": [
            "Stop everything and assess whether the deadline is truly missed or if a same-day fix is possible",
            "Do not call the client, court, or opposing counsel before talking to the partner",
            "Check if there is any argument for tolling or extension (some deadlines are not as firm as they appear)",
            "Document exactly what happened — not to cover yourself, but because you'll need this for the partner conversation",
        ],
        "what_not_to_do": [
            "Do NOT try to fix it yourself without telling anyone",
            "Do NOT minimize the impact when reporting",
            "Do NOT draft any court filing without partner approval",
        ],
        "long_term": "Most missed deadline situations are recoverable if disclosed immediately. The cover-up is usually worse than the mistake.",
    },
    "wrong-filing": {
        "severity": "High — may require court correction",
        "first_call": "Supervising partner — within the hour",
        "immediate_steps": [
            "Pull up the filing and document exactly what was wrong",
            "Check if an amended filing can cure the error and how quickly",
            "Do not send any follow-up communications about the filing until partner is briefed",
        ],
        "what_not_to_do": [
            "Do NOT file an amended version without approval",
            "Do NOT tell opposing counsel before the partner knows",
        ],
        "long_term": "Courts generally allow corrections to procedural errors, especially when disclosed proactively.",
    },
    "email-wrong-person": {
        "severity": "Depends — potentially privilege issue",
        "first_call": "Supervising partner if it involves client confidences or opposing counsel's documents",
        "immediate_steps": [
            "Assess what was in the email and who received it",
            "If it contained client confidences and went to opposing counsel: call the partner now",
            "If it contained privileged information: do NOT follow up with the recipient without guidance",
            "Send a follow-up requesting they disregard the email only if partner approves",
        ],
        "what_not_to_do": [
            "Do NOT assume the recipient will disregard it without being asked",
            "Do NOT demand return or destruction without partner and ethics guidance",
            "Do NOT panic-call the recipient before assessing the situation",
        ],
        "long_term": "The ABA has guidance on inadvertent disclosure. Many states have specific rules. Get ethics guidance if client confidences were disclosed.",
    },
    "blown-privilege": {
        "severity": "High to Critical — depends on jurisdiction and what was disclosed",
        "first_call": "Supervising partner immediately — this may require ethics counsel",
        "immediate_steps": [
            "Document exactly what happened and to whom the privileged information was disclosed",
            "Do not communicate further about the subject matter until the partner and possibly ethics counsel weigh in",
            "Preserve everything — do not delete any related communications",
        ],
        "what_not_to_do": [
            "Do NOT try to claim privilege was maintained when it wasn't",
            "Do NOT communicate with the client about this without guidance",
        ],
        "long_term": "Some jurisdictions have cure procedures for inadvertent privilege waiver. Act quickly — delay makes it worse.",
    },
    "billing-error": {
        "severity": "Low to Medium — correctable",
        "first_call": "Billing partner or supervising attorney — within the billing cycle",
        "immediate_steps": [
            "Identify the error and calculate the correct amount",
            "Check if a bill has already gone to the client — if not, correction is straightforward",
            "If bill already sent: notify the billing partner and discuss how to correct",
        ],
        "what_not_to_do": [
            "Do NOT let a billing error go uncorrected",
            "Do NOT adjust your own time entries without telling anyone",
        ],
        "long_term": "Billing errors are common and almost always correctable. Concealment is the ethical problem, not the error itself.",
    },
}


class Tools:
    class Valves(BaseModel):
        firm_size: str = "midsize"  # "biglaw", "midsize", "small", "government", "nonprofit"
        practice_area: str = "general"  # e.g., "litigation", "transactional", "general"
        tone: str = "direct"  # "direct" or "gentle"

    def __init__(self):
        self.valves = self.Valves()

    async def billing_guide(
        self,
        task: str,
        __event_emitter__=None,
    ) -> str:
        """
        How to bill for a specific task — what to put in the time entry, how long it should
        take, what the partner is expecting as a deliverable, and the mistakes new associates
        make that get their time written off.

        Covers the actual craft of billing, not just the rule that you should bill.

        Common tasks: research, drafting, review, client-call, court-appearance,
                      deposition, email

        :param task: The type of task you're billing for (e.g., "research", "drafting", "client-call").
        :return: A prompt that generates specific billing guidance for this task type.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Loading billing guidance for {task}...",
                        "done": False,
                    },
                }
            )

        task_key = task.lower().strip().replace(" ", "-")
        profile = BILLING_TASK_PROFILES.get(task_key)

        if profile:
            profile_context = f"""
TASK TYPE: {profile['description']}
Typical time range: {profile['typical_range']}
Billing unit: {profile['billing_unit']}
Common mistakes: {'; '.join(profile['common_mistakes'])}
What partners expect: {profile['what_partners_expect']}"""
        else:
            profile_context = f"\nTask: {task} (general billing guidance applies)"

        prompt = f"""You are a senior associate coaching a first-year attorney on billing. The new associate needs guidance on how to bill for: **{task}**

{profile_context}

FIRM CONTEXT:
Firm size: {self.valves.firm_size}
Practice area: {self.valves.practice_area}

---

Provide complete billing guidance covering:

**1. WHAT TO BILL**
- What time is billable for this task type (be specific)
- What is not billable (the learning curve, setup time, interruptions)
- Common time that new associates forget to capture

**2. HOW TO WRITE THE TIME ENTRY**
Write 3 examples of time entries for this task:
- A weak entry (too vague — would get questioned or written off)
- An acceptable entry (passes review)
- A strong entry (what a senior associate writes — descriptive, task-connected, defensible)

Show the difference and explain why the strong entry is better.

**3. TIME ESTIMATES**
- What does this task reasonably take for a first-year attorney vs. a third-year?
- At what point does the time become non-billable because you're spinning your wheels?
- The rule: "If you've been stuck for 30 minutes, you need to ask someone — not bill another hour to figure it out yourself."

**4. WHAT THE PARTNER EXPECTS TO RECEIVE**
- What deliverable goes with this time entry?
- What level of polish does the partner expect?
- How do you communicate that you've completed it?

**5. WRITE-OFF RISK**
- Is this task type commonly written off? Why?
- What makes the time defensible if a client questions it?
- The 'would I be embarrassed if this client saw this entry?' test

**6. PRACTICAL EXAMPLE**
Walk through a concrete example: a first-year is working on [specific version of this task]. Step by step, what do they record, when, and how?

Close with the single most common billing mistake first-years make on this task type. Be specific — not "don't block bill" (too abstract) but "here's what block billing looks like for this task and why it's a problem." """

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Billing guidance ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def email_drafting(
        self,
        scenario: str,
        __event_emitter__=None,
    ) -> str:
        """
        Draft a professional email for common legal practice scenarios.

        Handles the emails that new attorneys find hardest to write: telling a client
        bad news, asking for an extension, disclosing a mistake, communicating with
        opposing counsel for the first time.

        scenario: status-update, extension-request, client-intake, opposing-counsel,
                  partner-update, court-filing, mistake

        :param scenario: The email scenario (see options above, or describe your situation).
        :return: A prompt that drafts a professional email with coaching notes.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Drafting email for scenario: {scenario}...",
                        "done": False,
                    },
                }
            )

        scenario_key = scenario.lower().strip().replace(" ", "-")
        profile = EMAIL_SCENARIOS.get(scenario_key)

        if profile:
            profile_context = f"""
Scenario: {profile['description']}
Key elements to include: {', '.join(profile['key_elements'])}
Tone: {profile['tone']}
Common pitfalls: {'; '.join(profile['pitfalls'])}"""
        else:
            # Free-form scenario
            profile_context = f"\nCustom scenario: {scenario}"

        prompt = f"""You are a senior attorney helping a first-year draft a professional email. The scenario is:
{profile_context}

FIRM CONTEXT:
Firm type: {self.valves.firm_size}
Practice area: {self.valves.practice_area}

---

**PART 1: THE EMAIL DRAFT**

Write a complete, send-ready email draft. Include:
- Subject line
- Salutation
- Body
- Professional close and signature block template

The email should be:
- Short (under 200 words unless the situation requires more)
- Bottom line up front — the key point in the first sentence
- Clear about any action required from the recipient
- Professional in tone without being stiff

**PART 2: WHAT MAKES THIS DRAFT WORK**

Explain 3 specific choices you made in the draft and why — what would be worse and what you were trying to achieve.

**PART 3: CUSTOMIZATION VARIABLES**

List every field the sender needs to fill in before sending, with a note on what to consider:
- Not just [NAME] and [DATE] — but any place where the sender needs to make a judgment call

**PART 4: THE ALTERNATIVE DRAFT**

Write a second version of the same email — shorter, more direct. Sometimes the 3-sentence email is better than the paragraph version. Show both options and explain when you'd choose each.

**PART 5: RED FLAGS TO AVOID**

For this scenario specifically, list 3 specific mistakes that could make the email worse — either legally, professionally, or in terms of client relationship. Not generic advice — specific to this email type.

Important: Do not use legal jargon unless it's genuinely appropriate. Many of these emails go to clients or opposing counsel — they should read like a professional, not a law review article."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Email draft ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def research_methodology(
        self,
        question: str,
        __event_emitter__=None,
    ) -> str:
        """
        Given a legal research question, generate a complete research strategy:
        where to start, what to search for, how to know when you're done, and how
        to present your findings to the assigning attorney.

        This is the skill that separates a first-year who spends 20 hours on research
        from one who spends 6 hours and finds the same answer.

        :param question: The legal research question you've been assigned.
        :return: A prompt that builds a complete research methodology for your question.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Building research strategy...",
                        "done": False,
                    },
                }
            )

        if not question or len(question.strip()) < 10:
            return (
                "Please describe your research question. The more specific, the better "
                "(e.g., 'Can an employer in California terminate an at-will employee for "
                "off-duty marijuana use?' rather than just 'employment law')."
            )

        if len(question) > 2000:
            question = question[:2000] + "..."

        prompt = f"""You are a research librarian and senior associate helping a first-year develop a research strategy. The research question is:

**QUESTION**: {question}

**FIRM CONTEXT**: {self.valves.firm_size} firm, {self.valves.practice_area} practice area

---

Provide a complete, actionable research methodology:

**STEP 1: ISSUE IDENTIFICATION**

Before you search anything:
- Break the question into its component legal issues (there may be more than one)
- Identify the likely jurisdiction (state, federal, or both)
- Identify what area(s) of law govern this question
- List the vocabulary you'll need: the legal terms of art, plain language variants, and related concepts
- Note any factual gaps that would affect the legal analysis — you may need to go back to the assigning attorney

**STEP 2: STARTING POINT (secondary sources first)**

- What secondary source should you start with for this type of question?
  (Specific: not "a treatise" — what type? What should you look for?)
- What will the secondary source give you that's worth having before you go to primary sources?
- Time allocation: 30-45 minutes in secondary sources is usually enough to orient

**STEP 3: PRIMARY SOURCE SEARCH STRATEGY**

For statutes:
- Where to look (which code(s))
- What to search for
- What to verify (is this current law? Any pending amendments?)

For cases:
- Suggested search terms (give 3-5 specific Boolean or natural language searches)
- How to filter: jurisdiction, date range, court level
- How to use citing references once you find a good case (KeyCite / Shepard's)

For regulations (if applicable):
- Which agencies would regulate this
- How to search the CFR and Federal Register

**STEP 4: HOW TO KNOW WHEN YOU'RE DONE**

The single biggest inefficiency in first-year research is not knowing when to stop. Describe:
- The saturation signal (what does it look like when you've found the key authorities?)
- The 3-source convergence test (same cases coming up in different searches)
- What to do when you find a direct answer vs. what to do when you find conflicting authority
- When to flag a gap (you've searched thoroughly and there's no controlling authority)

**STEP 5: PRESENTING YOUR FINDINGS**

The assigning attorney gave you this question because they need it answered, not because they want to read everything you read. Structure your deliverable:

- Recommended format (email summary vs. formal memo — which fits this question?)
- What goes first (the answer, not the journey)
- How to present uncertain or conflicting authority
- What to include about your methodology (they sometimes want to know what you searched)
- The one-sentence bottom line that goes at the very top

**STEP 6: TIME MANAGEMENT**

For this specific question:
- Estimated research time for a first-year (be honest about the range)
- Where the time sink is (what part of this research typically expands unexpectedly)
- At what point should you check in with the assigning attorney before continuing?

Close with the single most important piece of advice for a first-year tackling this type of question — the thing that separates efficient legal research from spinning your wheels."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Research strategy ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def mistake_recovery(
        self,
        situation: str,
        __event_emitter__=None,
    ) -> str:
        """
        How to handle a professional mistake — the guidance that every new attorney
        needs but nobody gives them.

        Covers: missed deadlines, wrong filings, emails sent to wrong people, blown
        privilege, billing errors, and more. Focus is on what to do in the next hour,
        not just abstract advice about being honest.

        If you're panicking right now: read this first.

        :param situation: Describe what happened (be specific — vague descriptions get generic advice).
        :return: A prompt that generates specific, actionable mistake recovery guidance.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Loading recovery guidance...",
                        "done": False,
                    },
                }
            )

        if not situation or len(situation.strip()) < 20:
            return (
                "Describe what happened in as much detail as you're comfortable sharing. "
                "The more specific, the more useful the guidance. This runs locally — "
                "nothing leaves your machine.\n\n"
                "Common scenarios include: missed deadline, wrong filing, email sent to wrong person, "
                "privileged document produced in discovery, billing error, incorrect legal advice, "
                "missed conflict check."
            )

        if len(situation) > 3000:
            situation = situation[:3000] + "..."

        # Try to categorize the situation
        sit_lower = situation.lower()
        category = None
        for key, profile in MISTAKE_CATEGORIES.items():
            if key.replace("-", " ") in sit_lower or key in sit_lower:
                category = key
                break

        category_context = ""
        if category:
            p = MISTAKE_CATEGORIES[category]
            category_context = f"""
SITUATION CATEGORY: {category.replace('-', ' ').title()}
Severity assessment: {p['severity']}
First call: {p['first_call']}
"""

        tone_instruction = (
            "Be direct and specific. This person needs to act, not read theory."
            if self.valves.tone == "direct"
            else "Be clear and supportive. This person is stressed and needs actionable guidance."
        )

        prompt = f"""You are a senior attorney helping a first-year navigate a professional mistake. {tone_instruction}

THE SITUATION:
{situation}
{category_context}

---

**SECTION 1: STOP AND BREATHE**

First: one sentence to normalize this. Every attorney has made serious mistakes. The response to the mistake determines the outcome far more than the mistake itself.

**SECTION 2: WHAT TO DO IN THE NEXT 60 MINUTES**

Step-by-step, concrete actions. Not "tell your supervisor" — but:
- Who exactly do you tell (supervising partner? associate? billing partner? all three?)
- How do you tell them (phone or in person — not email for serious matters)
- What do you say (give a script: 3-5 sentences that are factual, non-defensive, and include what you know and what you don't yet know)
- What documents or information to gather before you make that call
- What NOT to do before you've talked to the supervising attorney

**SECTION 3: THE CONVERSATION WITH YOUR SUPERVISOR**

- How to present what happened (factual summary, not an apology spiral)
- What the supervisor needs to know vs. what they don't
- What questions they'll likely ask — and how to answer them honestly
- What you should NOT say (minimize, speculate, blame others, promise outcomes you can't deliver)
- What to do if the supervisor's reaction is disproportionate

**SECTION 4: MITIGATION**

What can actually be done to fix this or reduce the damage? Be specific:
- Immediate steps (what can happen today)
- Near-term steps (what happens this week)
- What the best-case resolution looks like
- What you may not be able to fix, and how to accept that honestly

**SECTION 5: CLIENT AND COURT IMPLICATIONS**

If the mistake affects a client or court filing:
- Does the client need to be told? When and how?
- Are there any mandatory disclosure obligations?
- Are there regulatory, bar, or malpractice implications to assess?
- Who handles those conversations (it may not be you)

**SECTION 6: THE ETHICS LAYER**

Depending on the severity:
- Are there professional responsibility obligations triggered here? (candor, disclosure, etc.)
- Should firm ethics counsel be involved?
- Should the attorney consider seeking personal ethics advice?

Be direct: not every mistake has ethics implications, but some do, and downplaying them helps no one.

**SECTION 7: WHAT HAPPENS NEXT TO YOUR CAREER**

Be realistic and honest:
- Will this follow you? Under what circumstances does it become a serious career problem vs. a recoverable incident?
- How should the attorney think about the long-term impact?
- What's the actual rate at which first-year mistakes end careers vs. become stories people tell years later?

Close with the most important thing to remember right now — one sentence. Make it honest, not platitudinous."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Recovery guidance ready",
                        "done": True,
                    },
                }
            )

        return prompt
