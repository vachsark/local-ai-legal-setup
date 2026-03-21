"""
title: Legal Job Prep
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Job search and interview preparation for law school graduates. Drafts cover
  letters tailored to firm type, generates interview coaching with real talk about what
  interviewers are actually looking for, reviews writing samples, and provides salary
  negotiation guidance with current market data and actual scripts.

  Runs entirely locally — no API costs, no data leaves your machine.

  Import into Open WebUI: Workspace → Tools → + → paste this file.

  Recommended models:
  - legal-tutor: Interactive mock interview practice
  - qwen3.5:9b: Cover letter drafts and structured coaching
  - gemma3:12b: Writing sample feedback and longer analysis

  NOTE: Salary ranges are illustrative. Verify current market rates for your specific
  city and practice area using NALP, Above the Law salary surveys, or your law school's
  career services office before negotiating.
"""

from pydantic import BaseModel


FIRM_TYPE_PROFILES = {
    "biglaw": {
        "display": "BigLaw (Am Law 200 firm)",
        "values": "excellence, prestige, client service, billable hours, long-term associate pipeline",
        "culture": "hierarchical, demanding, high stakes, formal — partnership track starts now",
        "hours": "2,000-2,200 billable hours expected; actual hours often 10-20% higher",
        "salary_range": "$215,000-$225,000 (1st year Cravath scale) in major markets; $190,000-$215,000 in secondary markets",
        "what_they_want": "academic excellence, law review/moot court, firm-specific research, ability to handle pressure, no red flags",
        "interview_style": "formal, structured, behavioral questions + résumé deep dive; callbacks are multi-interview days with partners",
    },
    "midsize": {
        "display": "Mid-Size Firm (50-200 attorneys)",
        "values": "practical skills, client relationships, breadth of experience, collegiality",
        "culture": "more accessible partners, broader exposure to different matter types, less hierarchical",
        "hours": "1,800-2,000 billable hours; more flexibility on remote and schedule",
        "salary_range": "$100,000-$175,000 depending on city, practice area, and firm profitability",
        "what_they_want": "practical skills, interest in the practice area, personality fit, long-term commitment to the firm",
        "interview_style": "conversational, relationship-focused; likely 1-2 rounds with partners and associates",
    },
    "small-firm": {
        "display": "Small Firm (under 50 attorneys)",
        "values": "client relationships, practical skills from day one, entrepreneurial drive",
        "culture": "direct client contact immediately, generalist skills valued, tight-knit",
        "hours": "variable; often 1,600-1,900 with more control over your schedule",
        "salary_range": "$60,000-$120,000 depending on city, practice area, and firm",
        "what_they_want": "can you handle client calls and court appearances now, resourceful, no hand-holding needed",
        "interview_style": "informal, practical — often a writing sample review, may ask you to solve a real problem",
    },
    "government": {
        "display": "Government (federal or state agency, DOJ, DA, Public Defender)",
        "values": "public service mission, stability, policy impact, work-life balance",
        "culture": "mission-driven, bureaucratic, stable; advancement is structured but clear",
        "hours": "standard government hours (40-50/week); predictable schedule",
        "salary_range": "Federal GS-11 to GS-13 ($70,000-$110,000+); state varies widely; ADAs often $55,000-$80,000",
        "what_they_want": "commitment to the mission, writing skills, team player, long-term interest (not a resume stop)",
        "interview_style": "structured behavioral questions with scoring rubrics; often panel interviews",
    },
    "public-interest": {
        "display": "Public Interest / Nonprofit Legal Organization",
        "values": "passion for the cause, client empathy, resourcefulness with limited budgets",
        "culture": "high responsibility early, under-resourced but high-impact, collaborative",
        "hours": "variable; often 40-50 hours but some organizations demand more",
        "salary_range": "$45,000-$80,000; PSLF eligibility is a major compensation factor",
        "what_they_want": "genuine commitment (not checkboxing), community ties, ability to work independently under supervision",
        "interview_style": "informal but probing; they WILL ask hard questions about your commitment to the work",
    },
    "in-house": {
        "display": "In-House Counsel (corporate legal department)",
        "values": "business judgment, practical advice, risk management, communication",
        "culture": "business partner not service provider, cross-functional, faster-paced decisions",
        "hours": "often 40-55 hours; depends heavily on company and role",
        "salary_range": "junior in-house: $80,000-$160,000 + equity/bonus; highly variable",
        "what_they_want": "business sense, ability to give clear yes/no advice (not 'it depends'), communication skills with non-lawyers",
        "interview_style": "business-focused, case study sometimes, 'how would you handle this business situation?'",
    },
}

INTERVIEW_ROUNDS = {
    "screening": {
        "label": "Screening / Phone / First Round",
        "duration": "20-30 minutes",
        "purpose": "Cut the field to callbacks. They're checking: can you communicate clearly? Any red flags? Do you know the firm?",
        "format": "Phone or video; often with a recruiter or junior associate",
    },
    "callback": {
        "label": "Callback / In-Person Interview",
        "duration": "3-6 hours (multiple back-to-back interviews)",
        "purpose": "Decide if you're an offer. Partners evaluate fit, associates evaluate collegiality.",
        "format": "Series of 30-minute one-on-ones with partners and senior associates",
    },
    "partner-lunch": {
        "label": "Partner Lunch / Dinner",
        "duration": "1-2 hours",
        "purpose": "Social fit. They already like your qualifications — this is about whether they want to eat with you every day.",
        "format": "Meal with 2-3 partners; more conversational but still being evaluated",
    },
    "writing-sample": {
        "label": "Writing Sample Review",
        "duration": "15-30 minutes discussion",
        "purpose": "Verify you can write, and that the sample is actually yours.",
        "format": "Expect questions about your reasoning, choices you made, what you would do differently",
    },
}


class Tools:
    class Valves(BaseModel):
        years_experience: int = 0  # 0 = new grad, 1-3 = junior associate
        include_scripts: bool = True  # include word-for-word scripts for difficult questions
        tone: str = "direct"  # "direct" or "encouraging"

    def __init__(self):
        self.valves = self.Valves()

    async def cover_letter(
        self,
        firm_type: str,
        position: str,
        experience: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Draft a cover letter for a legal position — tailored to the specific firm type.

        Covers the critical things legal cover letters get wrong: starting with "I am
        writing to apply," generic praise, not knowing anything about the firm, and
        failing to make a specific connection between your experience and their work.

        firm_type: biglaw, midsize, small-firm, government, public-interest, in-house

        :param firm_type: The type of employer (biglaw, midsize, small-firm, government, public-interest, in-house).
        :param position: The specific position title (e.g., "first-year associate", "summer associate", "staff attorney").
        :param experience: Brief description of your most relevant experience to highlight (optional but makes the letter better).
        :return: A prompt that drafts a tailored cover letter with coaching notes.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Drafting cover letter for {firm_type}...",
                        "done": False,
                    },
                }
            )

        ft_key = firm_type.lower().strip().replace(" ", "-")
        profile = FIRM_TYPE_PROFILES.get(ft_key, FIRM_TYPE_PROFILES["midsize"])

        experience_section = ""
        if experience.strip():
            experience_section = f"\nStudent's relevant experience to highlight:\n{experience.strip()}"

        year_note = ""
        if self.valves.years_experience == 0:
            year_note = "This is a new law school graduate or current student — they have no attorney experience yet. Highlight academics, clinics, internships, and transferable skills."
        elif self.valves.years_experience <= 3:
            year_note = f"This is a junior attorney with approximately {self.valves.years_experience} year(s) of experience. Lead with practice area accomplishments."

        prompt = f"""You are a legal career coach. Draft a strong cover letter for a {position} position at a {profile['display']}.

{year_note}
{experience_section}

WHAT THIS EMPLOYER ACTUALLY VALUES:
{profile['what_they_want']}

COVER LETTER RULES (these are the ones that get letters tossed):

1. **Do NOT start with "I am writing to apply for..."** — every letter does this. It wastes the first sentence.
2. **Do NOT write generic praise** — "Your firm's excellent reputation" tells them nothing. Research-specific praise or skip it.
3. **First sentence must earn the reader's attention** — start with your strongest fact, a specific connection, or a direct statement of what you bring.
4. **Three paragraphs maximum** — partners do not read long cover letters. If it doesn't fit in three tight paragraphs, cut it.
5. **Be specific** — "I am interested in corporate law" is weak. "My work on [specific type of transaction/case] during [clinic/internship] showed me that..." is strong.
6. **Show you know the firm** — one specific, accurate thing (a practice group, a notable matter if public, a stated value). If you can't find anything specific, say you researched the group and ask to hear more about it.

STRUCTURE:
- Paragraph 1 (3-4 sentences): Who you are, the position, your strongest hook. Why you specifically?
- Paragraph 2 (4-5 sentences): Relevant experience — apply it to what they need. What can you do for them on day one?
- Paragraph 3 (2-3 sentences): Why this employer specifically. Professional close.

DRAFT THE LETTER, then add a section called "COACHING NOTES" with:
- The 2 strongest things about this letter
- The 2 things you'd change if you knew more about the specific firm
- One sentence the student should personalize with specific firm research before sending

Tone: Professional but not stiff. Legal cover letters often sound like they were written by a committee. Write like a person.

Important: Do NOT add [brackets] for every field — draft real language where possible. Only bracket genuinely unknown specifics (firm name, date, student's name)."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Cover letter ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def interview_prep(
        self,
        firm_type: str,
        round: str = "screening",
        __event_emitter__=None,
    ) -> str:
        """
        Full interview coaching for a specific firm type and interview round.

        Goes beyond "tell me about yourself" prep. Covers what interviewers are actually
        evaluating (which they won't tell you), what questions they're legally not supposed
        to ask but sometimes do, and what separates candidates who get offers from those
        who don't.

        firm_type: biglaw, midsize, small-firm, government, public-interest, in-house
        round: screening, callback, partner-lunch, writing-sample

        :param firm_type: The type of employer (biglaw, midsize, small-firm, government, public-interest, in-house).
        :param round: The interview round (screening, callback, partner-lunch, writing-sample).
        :return: A prompt that generates complete interview coaching for this employer and round.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Preparing coaching for {firm_type} {round} interview...",
                        "done": False,
                    },
                }
            )

        ft_key = firm_type.lower().strip().replace(" ", "-")
        profile = FIRM_TYPE_PROFILES.get(ft_key, FIRM_TYPE_PROFILES["midsize"])

        round_key = round.lower().strip().replace(" ", "-")
        round_info = INTERVIEW_ROUNDS.get(round_key, INTERVIEW_ROUNDS["callback"])

        scripts_note = ""
        if self.valves.include_scripts:
            scripts_note = "For difficult questions, provide word-for-word example responses at strong, average, and weak levels — so the candidate understands what 'good' sounds like."

        prompt = f"""You are a legal career coach who has worked inside law firm hiring committees. Prepare a candidate for:

EMPLOYER TYPE: {profile['display']}
INTERVIEW ROUND: {round_info['label']}
Duration: {round_info['duration']}
What they're really evaluating: {round_info['purpose']}
Format: {round_info['format']}

WHAT THIS EMPLOYER ACTUALLY VALUES (don't be generic):
{profile['what_they_want']}

FIRM CULTURE TO UNDERSTAND:
{profile['culture']}

---

**SECTION 1: WHAT THEY'RE REALLY EVALUATING**

Describe what the interviewer is actually thinking during this round. Be honest about:
- The 3 things they're looking for that they'll never say out loud
- The red flags that immediately kill a candidate
- What "cultural fit" actually means for this type of employer (be specific)
- What separates the candidates who get offers from those who get polite rejections

**SECTION 2: THE 8 MOST LIKELY QUESTIONS**

For each question:
- **The question**: [exact phrasing or close variant]
- **What they're really asking**: [the underlying thing they want to learn]
- **Strong answer structure**: [not a script, but the key moves a strong answer makes]
- **What tanks the answer**: [the mistakes candidates make on this specific question]
{scripts_note}

Include:
- 2-3 standard behavioral questions ("Tell me about a time when...")
- 2-3 firm/employer-specific questions ("Why public interest?" / "Why BigLaw?" / etc.)
- 1-2 difficult questions (résumé gap, grade concern, why you left, etc.)
- 1-2 questions about the specific practice area

**SECTION 3: QUESTIONS TO ASK THEM**

Provide 5 questions the candidate should ask. For each:
- The question
- Why it's smart to ask this (what it signals about you)
- How to follow up intelligently when they answer

**SECTION 4: THE LOGISTICS**

- What to wear (be specific — not "business professional")
- What to research before walking in (5 specific things)
- What to bring
- What to do in the first 2 minutes (arrival, handshake, setup)
- How to recover if you blank on a question
- What to do immediately after (within 24 hours)

**SECTION 5: THE THINGS THEY WON'T TELL YOU**

The real advice. What's the difference between the candidate who walks in and the candidate who walks out with an offer? Be direct. If there are implicit biases or unwritten rules at this type of employer, name them — candidates who know the rules can navigate them; candidates who don't get surprised.

Close with one sentence of genuine encouragement. This is a stressful process and the candidate is doing the work."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Interview prep ready",
                        "done": True,
                    },
                }
            )

        return prompt

    async def writing_sample_review(
        self,
        sample: str,
        __event_emitter__=None,
    ) -> str:
        """
        Review a legal writing sample for job applications.

        Legal employers read your writing sample looking for very specific things.
        This review tells you whether your sample is helping or hurting you — and
        what to fix before you submit it.

        :param sample: The full text of your writing sample (paste it in).
        :return: A prompt that provides a complete writing sample review for job applications.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Reviewing writing sample...",
                        "done": False,
                    },
                }
            )

        if not sample or len(sample.strip()) < 100:
            return (
                "Please paste your writing sample. A writing sample should be at least "
                "one page (300+ words) — a brief, memo, or research paper. The longer "
                "the better for this review."
            )

        if len(sample) > 15000:
            sample = sample[:15000] + "\n\n[Sample truncated at 15,000 characters for review]"

        prompt = f"""You are a hiring partner reviewing a writing sample for a legal associate position. Give direct, honest feedback.

THE WRITING SAMPLE:
{sample}

---

Evaluate the sample across these categories:

**FIRST IMPRESSION (what a partner thinks in the first 60 seconds)**
- What type of document is this and is it appropriate as a writing sample?
- What is the first impression of the writing quality?
- Is the formatting professional and consistent?
- Does the opening make you want to keep reading?

**LEGAL ANALYSIS QUALITY**
- Is the legal analysis sound — does the writer understand the law?
- Are rules stated accurately and completely?
- Is the application to facts concrete (uses the facts) or conclusory (just states conclusions)?
- Are counterarguments addressed, or does the writer only argue one side?
- Does the writer reach definite conclusions, or hedge everything?

**WRITING MECHANICS**
- Sentence clarity — are there long sentences that should be broken up?
- Active vs. passive voice — is passive voice used where active would be stronger?
- Paragraph structure — does each paragraph have a clear point?
- Word choice — any jargon, redundancy, or vague language?
- Grammar and mechanics issues (flag specific examples)

**SUITABILITY AS A WRITING SAMPLE**
- Is this the right length? (Most firms want 5-15 pages)
- Is the subject matter appropriate? (Controversial subjects can create implicit bias)
- Does this show the skills needed for the target employer?
- Should this be redacted (client names, case numbers) — is it currently redacted properly?
- Is there a stronger piece the candidate might use instead?

**OVERALL VERDICT**
- Numerical rating: X/10 as a writing sample
- Would you advance this candidate based on the writing sample alone? Why or why not?
- The single most important thing to fix before submitting this sample
- The single strongest element of the sample

**REVISION SUGGESTIONS**
Pick the weakest paragraph and rewrite it at a strong associate standard. Show the before and after side-by-side.

Be direct. If the sample would hurt more than help, say so and explain why. If the candidate should find a different sample, say that too."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Writing sample review complete",
                        "done": True,
                    },
                }
            )

        return prompt

    async def salary_negotiation(
        self,
        market: str = "midlaw",
        city: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Salary negotiation guidance for new attorneys — including what's actually negotiable
        and word-for-word scripts for the conversation.

        Most new attorneys don't negotiate because they don't know what's negotiable or
        are afraid of losing the offer. This guide covers what you can ask for, what you
        can't, how to ask, and what to say when they say no.

        market: biglaw, midlaw, smalllaw, government, public-interest, in-house

        :param market: The market segment (biglaw, midlaw, smalllaw, government, public-interest, in-house).
        :param city: City or metro area for market rate context (optional but helpful).
        :return: A prompt that generates complete salary negotiation guidance.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Building salary negotiation guide...",
                        "done": False,
                    },
                }
            )

        market_key = market.lower().strip().replace(" ", "")
        city_context = f" in {city}" if city.strip() else ""

        market_profiles = {
            "biglaw": {
                "display": "BigLaw",
                "salary_structure": "Lockstep (Cravath scale) — salary is fixed by class year at most firms. Non-negotiable at associate level.",
                "what_is_negotiable": "Signing bonus, start date, bar review reimbursement, bar loan, relocation assistance, practice group placement",
                "leverage": "Competing offers from other BigLaw firms, lateral experience",
                "red_line": "Do not ask for more than the lockstep salary — you will come across as not understanding how BigLaw works",
            },
            "midlaw": {
                "display": "Mid-Size Firm",
                "salary_structure": "Usually set but with more flexibility than BigLaw. Often has bands rather than lockstep.",
                "what_is_negotiable": "Base salary (often 5-15% room), signing bonus, start date, benefits, bar loan, remote policy",
                "leverage": "Competing offers, specialized skills, lateral experience, specific client relationships",
                "red_line": "Aggressive negotiation can sour relationships at smaller firms — read the room",
            },
            "smalllaw": {
                "display": "Small Firm",
                "salary_structure": "Often individually negotiated — more flexibility but also less money to negotiate",
                "what_is_negotiable": "Salary, bonus structure, billable hour expectations, remote work, title, benefits",
                "leverage": "Specialized skills that directly serve their clients, competing offers, trial/hearing experience",
                "red_line": "Asking for more than the market will make you look out of touch — research local rates first",
            },
            "government": {
                "display": "Government",
                "salary_structure": "Pay scale is set by law (GS for federal; similar scales for state). Usually not negotiable.",
                "what_is_negotiable": "Grade level (sometimes), step within grade (for experience), benefits, student loan repayment programs",
                "leverage": "Directly relevant experience, security clearances, competing private sector offers",
                "red_line": "Government HR often literally cannot deviate from the pay scale — pushing hard wastes goodwill",
            },
            "publicinterest": {
                "display": "Public Interest / Nonprofit",
                "salary_structure": "Usually set by pay scale. Very limited flexibility.",
                "what_is_negotiable": "Sometimes step within salary band, flexible work arrangements, professional development budget",
                "leverage": "PSLF eligibility is a key tool — calculate your actual compensation with forgiveness factored in",
                "red_line": "Pushing hard on salary at public interest orgs signals misalignment with their mission",
            },
            "inhouse": {
                "display": "In-House",
                "salary_structure": "Highly variable. Often base + bonus + equity at companies. More room to negotiate than law firms.",
                "what_is_negotiable": "Base salary, signing bonus, equity, annual bonus target, remote work, title",
                "leverage": "Competing offers are the single strongest tool. Practice area expertise that directly benefits the company.",
                "red_line": "Startups with equity — be careful negotiating equity without understanding dilution, cliff vesting, etc.",
            },
        }

        profile = market_profiles.get(market_key, market_profiles["midlaw"])

        prompt = f"""You are a legal career coach helping a new attorney negotiate their first job offer at a {profile['display']} organization{city_context}.

MARKET CONTEXT:
Salary structure: {profile['salary_structure']}
What IS negotiable: {profile['what_is_negotiable']}
Your leverage: {profile['leverage']}
What NOT to do: {profile['red_line']}

---

**SECTION 1: UNDERSTAND YOUR MARKET POSITION**

Be direct and realistic about:
- What the current salary range looks like for a new attorney in this market{city_context}
- How to verify this independently (NALP, Above the Law salary surveys, your law school career office)
- What factors affect where you land in the range (grades, clerkship, law review, specialized experience)
- How competing offers change the math

**SECTION 2: WHAT YOU CAN ACTUALLY ASK FOR**

Walk through every negotiable element at this type of employer:
- What it is
- Whether it's worth asking for
- How to ask for it
- What a reasonable ask looks like (don't ask for $10,000 signing bonus at a non-profit)

**SECTION 3: THE TIMING**

- When to negotiate (after the offer, before you accept — not before)
- How long you can wait before responding without it being awkward
- What to do if they give you a deadline that feels too short

**SECTION 4: THE SCRIPTS**

This is the most important section. Provide word-for-word scripts for:

1. **The initial counteroffer** (when you have a competing offer)
   - Phone/email version
   - How to respond if they push back
   - How to respond if they say no and hold firm

2. **Asking about negotiable items without a competing offer**
   - How to ask about signing bonus / benefits without seeming greedy
   - How to handle "our salary is set" (does that mean everything is set, or just salary?)

3. **The ask you're afraid to make**
   - Remote work
   - Start date flexibility (bar exam prep time)
   - Bar loan reimbursement

4. **When they say no**
   - How to accept gracefully without burning the relationship
   - How to make one more ask before accepting
   - When to walk away

**SECTION 5: STUDENT LOANS AND PSLF**

If this employer qualifies for Public Service Loan Forgiveness:
- How to calculate your real compensation with PSLF factored in
- How to use that calculation in your decision-making (not in the negotiation itself)
- What PSLF requires and the common mistakes that disqualify applicants

**SECTION 6: THE MINDSET**

The biggest obstacle is fear — fear of losing the offer, seeming greedy, or being rude. Address this directly:
- Do employers rescind offers for salary negotiation? (Be honest about when it happens and when it doesn't)
- How to tell the difference between an employer who has flexibility and one who doesn't
- Why not negotiating has real costs beyond this job

Close with a brief note on making the decision if they can't match your ask. Money isn't everything, but it's not nothing either."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Salary negotiation guide ready",
                        "done": True,
                    },
                }
            )

        return prompt
