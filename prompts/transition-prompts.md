# Bar-to-Practice Transition Prompts

For law school graduates moving through bar prep and into their first associate position.
Recommended model: **legal-tutor** for interactive sessions, **qwen3.5:9b** for structured output.

These prompts pair with the tools in `tools/bar-exam-simulator.py`, `tools/job-prep.py`, and `tools/first-year-survival.py`. Use the prompts for quick interactive sessions; use the tools for structured, reproducible output.

---

## Bar Exam Prep (6 prompts)

---

### 1. 10-Week Bar Study Plan

**Model**: qwen3.5:9b | **Expect**: Week-by-week schedule with daily tasks and subject allocation

```
I'm studying for the bar exam and need a realistic 10-week study plan for [state / UBE].

Exam date: [date]
Hours per day I can commit: [number]
Subjects I feel weakest in: [list — or "unknown, start from scratch"]
Bar prep course I'm using (if any): [BarBri / Themis / Kaplan / self-study]

Build me:
1. A weekly calendar with subject rotation (not the same subject two days in a row)
2. When to take full practice MBE tests vs. drilling individual subjects
3. How to allocate time between MBE, MEE, and MPT
4. Rest day schedule (mandatory — burnout is real)
5. The final week structure (what to do days 7, 6, 5, 4, 3, 2, 1 before the exam)

Be realistic about what's achievable — don't build a schedule nobody can keep.
```

---

### 2. Explain an MBE Topic

**Model**: legal-tutor | **Expect**: Plain-language explanation + 5 practice questions with full answer keys

```
Explain [MBE topic] in a way that actually makes it stick, then give me 5 practice questions.

Topic: [e.g., "hearsay exceptions under FRE 803 and 804", "adverse possession elements",
        "personal jurisdiction after Pennoyer and International Shoe", "res ipsa loquitur"]

Format:
1. Plain-language version: what is this rule actually doing?
2. The formal rule with all elements
3. The most common exam traps / what students get wrong
4. Majority vs. minority rule split (if any)
5. Five MBE-style questions — increasing difficulty
   After each question, give me the correct answer with a full explanation
   AND explain why each wrong answer is wrong

Don't give me the answers until I ask — or, if you prefer: put the answer key after a clear break.
```

---

### 3. Callback Interview Prep

**Model**: legal-tutor | **Expect**: Role-specific coaching + likely questions + what interviewers won't tell you

```
I have a callback interview at [firm type] and I need to prepare.

Firm type: [e.g., "BigLaw M&A practice group", "mid-size litigation boutique",
           "public defender's office", "state AG office", "in-house at a tech company"]
Position: [e.g., "first-year associate", "summer associate"]
Round: [screening / callback / partner lunch]

Tell me:
1. What this type of employer is actually looking for (not the generic stuff)
2. The 8 most likely questions I'll be asked, with notes on what a strong answer demonstrates
3. Questions I should ask them — and why those specific questions are smart
4. What "culture fit" means for this employer and how to demonstrate it
5. The things they're evaluating that they'll never say out loud
6. What mistakes kill candidates at this stage

I want honest coaching, not cheerleading.
```

---

### 4. Recovering from a Professional Mistake

**Model**: legal-tutor | **Expect**: Immediate action plan + scripts for the conversation + honest career assessment

```
I made my first professional mistake and I need help figuring out what to do.

Here's what happened:
[Describe the situation as specifically as you're comfortable. The more detail, the better the guidance.]

I need to know:
1. What to do in the next 60 minutes (step-by-step, concrete)
2. How to tell my supervising attorney — give me actual words to say
3. What I should NOT do before I talk to them
4. Whether there are ethics implications I should know about
5. Honestly: how bad is this? Will it follow me?

Be direct. I need to act, not read theory.
```

---

### 5. Billing Time Entry Review

**Model**: qwen3.5:9b | **Expect**: Entry-by-entry feedback + what would get written off + corrected examples

```
Review my time entries for this week and tell me if I'm billing correctly.

My time entries:
[Paste your week's time entries — can be in any format]

For each entry, tell me:
1. Is this entry appropriately described? Would a client question it?
2. Is the time amount reasonable for this task?
3. Is this block billing? (If so, how to separate it)
4. What would a partner write off and why?
5. Any missing time I likely forgot to capture?

Also give me 2-3 corrected versions of my weakest entries — show me what they should look like.

Firm type: [BigLaw / mid-size / small / government]
Practice area: [litigation / transactional / general]
```

---

### 6. Professional Email Draft

**Model**: qwen3.5:9b | **Expect**: Send-ready draft + coaching notes + an alternative shorter version

```
Draft a professional email for this situation:

Scenario: [e.g., "telling a client their case has a problem we didn't see before",
           "asking opposing counsel for a 2-week extension",
           "updating my partner on a research project that's taking longer than expected",
           "following up with a partner who hasn't responded to my work in 10 days",
           "writing my first email to a new client after signing the engagement letter"]

Context:
[Any relevant details — who the recipient is, what the relationship is, what happened before this email]

I need:
1. The full email (subject line, body, close) — write it, don't template it
2. What you did well in this draft and why
3. What I should customize before sending
4. A shorter alternative version (sometimes 3 sentences is better)
5. What to avoid for this specific email type
```

---

## First Year at the Firm (4 prompts)

---

### 7. Research Strategy

**Model**: qwen3.5:9b | **Expect**: Complete research methodology from start to finish

```
I've been assigned a legal research question and I need a complete research strategy.

The question:
[State the research question as the partner gave it to you — or your best reconstruction]

My jurisdiction: [state / federal / both]
My practice area: [litigation / transactional / regulatory / etc.]
Deadline: [how much time do I have]

Give me:
1. The component legal issues (I may be missing some)
2. What secondary sources to start with for this type of question
3. Specific search terms to use in Westlaw/Lexis
4. How to know when I'm done (the saturation signal)
5. How to structure my memo or summary to the partner
6. How much time this should realistically take for a first-year

I want a methodology, not a lecture about research.
```

---

### 8. What Does This Mean in Practice?

**Model**: legal-tutor | **Expect**: Plain-English explanation of how a rule or doctrine plays out in actual practice

```
Walk me through how [legal doctrine or procedure] actually works in practice.

I understand the law — I need to understand what actually happens.

Doctrine/Procedure:
[e.g., "attorney-client privilege in a corporate setting",
 "summary judgment briefing schedule and what goes in the brief",
 "how a deal closes in M&A (from signing to closing)",
 "how a complaint actually gets filed in federal court (not the theory — the steps)",
 "what a deposition actually looks like — who's in the room, what happens, what I need to prepare"]

Tell me:
1. What actually happens at each step
2. What I need to do / prepare
3. What mistakes first-years make
4. What I should double-check before each step
5. What the partner is expecting from me
```

---

### 9. First-Year Priorities by Practice Area

**Model**: legal-tutor | **Expect**: Honest, specific guide to what matters in your first year

```
I just started as a [role] at a [firm type]. Tell me honestly what I should be focused on.

Role: [first-year associate / summer associate / staff attorney / public defender / ADA]
Firm/employer type: [BigLaw / mid-size / small firm / government / public interest]
Practice area: [litigation / M&A / real estate / criminal / family law / general]
Time into the job: [first week / first month / first 90 days / 6 months]

Be specific and honest about:
1. The 5 skills that will matter most for my career in this setting
2. What "being reliable" actually means in practice here (not the platitude — the specifics)
3. The mistakes first-years make that follow them for years
4. How to get good work and good mentorship
5. What success looks like at 3 months, 6 months, and 12 months in this specific context

I want the advice you'd give a younger version of yourself, not what goes in the orientation packet.
```

---

### 10. Ethics Situation Walkthrough

**Model**: legal-tutor | **Expect**: Model Rules analysis + concrete next steps + what to ask your supervisor

```
Help me think through this ethics situation at work.

I'm not looking for a formal opinion — I want to understand the analysis and know
what to do next.

Situation:
[Describe what's happening. Be as specific as you're comfortable. This runs locally — nothing leaves your machine.]

Questions I have:
1. What does the Model Rules say applies here?
2. What am I required to do vs. what am I permitted to do?
3. Is this something I handle myself, or does it require escalating to someone?
4. What should I say to my supervising attorney about this?
5. Are there bar discipline implications if I handle this wrong?

My jurisdiction: [state — or "I don't know, assume majority rule"]
```

---

## Usage Notes

- **Use legal-tutor** for interactive back-and-forth (Socratic sessions, mock interviews, working through an analysis step-by-step)
- **Use qwen3.5:9b** when you want a complete answer in one shot (study plans, email drafts, research strategies)
- **Use gemma3:12b** for longer document analysis (reviewing a writing sample, analyzing a full fact pattern)
- **Combine tools + prompts**: Use `bar-exam-simulator.py` to generate structured MBE sessions, then paste questions here for interactive drilling
- **Verify everything**: These prompts are practice tools. Verify all rules against current bar prep materials and primary sources before relying on them
