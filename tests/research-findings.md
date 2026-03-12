# Legal Writing Error Patterns — Research Findings

# For Fine-Tuning Grammar Checker AI Models

**Research date**: 2026-03-11
**Scope**: 5 categories, 20+ examples each
**Sources**: Bryan Garner / LawProse, Ken Adams / MSCD, BriefCatch, court opinions, bar association guides, legal writing scholarship
**Purpose**: Fine-tuning training data — BAD text with specific error annotations

---

## Category: email

### Example 1

**Bad text:** "Hi Tom, I don't think we should file the motion until we've reviewed the deposition transcripts, the expert reports and the interrogatory responses. FYI the deadline is next Friday so we need to move ASAP. Let me know what you think. Thanks, Mike"
**Error types:** Contraction in professional correspondence (don't), informal register (FYI, ASAP, Hi), missing Oxford comma (transcripts, reports and), buried action item (no clear deliverable with owner), no deadline confirmation loop
**Corrections:** Remove contractions; replace FYI/ASAP with formal equivalents; add Oxford comma before "and"; make action item explicit ("Please confirm by Wednesday whether you will complete the review"); use "Dear Tom" salutation
**Source/inspiration:** Garner LawProse email clarity guidance; ABA Journal "Clarity and Context in Legal Emails"

### Example 2

**Bad text:** "We've reviewed your client's demand and our client is willing to pay $75,000 to resolve this matter. Please confirm if your client accepts this offer."
**Error types:** Omission of "without prejudice" / FRE 408 protection label, no "subject to formal written agreement" caveat, "please confirm if" (ambiguous — "if" vs "whether"), no expiration date on offer
**Corrections:** Add "Without Prejudice / Subject to FRE 408" header; add "This offer is contingent upon execution of a formal written settlement agreement"; change "confirm if" to "advise whether"; add offer expiration ("This offer expires at 5:00 p.m. EST on [date]")
**Source/inspiration:** Inadvertent contract formation case law (Kloian v. Domino's Pizza); LSU Law Review "Email and the Threat of Inadvertent Settlement"

### Example 3

**Bad text:** "Per our conversation, I agree to the settlement terms discussed — $150,000 payment within 30 days, full release of all claims, dismissal with prejudice."
**Error types:** Email may constitute binding settlement agreement under UETA/E-SIGN; typed name in signature block is an electronic signature; "I agree" + essential terms = enforceable contract; no "subject to client approval" qualifier; no "formal written agreement required" caveat
**Corrections:** Add "Subject to client approval and execution of a formal written settlement agreement, I am authorized to confirm the following terms for discussion purposes only:"; never include "I agree" in a substantive email without these qualifiers
**Source/inspiration:** Kloian v. Domino's Pizza (Mich. App. 2006); Alessina v. El Gauchito II Corp.; MBM Law "Before You Hit Send"

### Example 4

**Bad text:** "As we discussed on the call, the client's records clearly show that your client breached the contract. We expect your client to remedy this immediately or we will proceed accordingly."
**Error types:** "clearly show" is overconfident without attaching evidence; "remedy this" is undefined (no specific cure); "immediately" is vague; "proceed accordingly" is a hollow threat with no specified action; tone is adversarial without substance
**Corrections:** Specify what the records show and cite them; define the required remedy; give a deadline with a date certain; identify the specific legal action contemplated if uncured (e.g., "file suit in [jurisdiction] for breach of contract")
**Source/inspiration:** Garner, "The Winning Brief" — on vague threats; BriefCatch on overconfident language

### Example 5

**Bad text:** "Please be advised that pursuant to our client's rights under the agreement, they hereby demand that you cease and desist from the continued violation of Section 4.2. Govern yourself accordingly."
**Error types:** "Please be advised that" (throat-clearing); "pursuant to" (legalese — use "under"); "they hereby demand" (archaic "hereby"); "cease and desist" (legal doublet — pick one); "continued violation" (states conclusion without facts); "Govern yourself accordingly" (universally mocked cliché, no specific instruction)
**Corrections:** Delete "Please be advised that"; replace "pursuant to" with "under"; delete "hereby"; use "stop" or "cease" alone; specify which conduct constitutes the violation; replace "Govern yourself accordingly" with specific instruction or deadline
**Source/inspiration:** Garner LawProse on legalese; SFBA "Govern yourself accordingly" critique; Bryan Garner "Modern American Usage" on doublets

### Example 6

**Bad text:** "I am writing to follow up on my previous email of March 3rd regarding the outstanding invoices. As I mentioned in that email, payment is overdue. Please remit payment at your earliest convenience."
**Error types:** "I am writing to" (throat-clearing — delete entirely); "as I mentioned in that email" (redundant reference); "at your earliest convenience" (non-binding — gives recipient unlimited discretion, no obligation)
**Corrections:** Delete "I am writing to follow up on my previous email of March 3rd regarding the outstanding invoices"; begin "Payment of $X on Invoice Nos. [X, Y, Z] remains overdue"; replace "at your earliest convenience" with "by [specific date]"
**Source/inspiration:** WordRake "Throat-Clearing Phrases in Legal Writing"; Garner "The Redbook" on sentence openings

### Example 7

**Bad text:** "PRIVILEGED AND CONFIDENTIAL — ATTORNEY-CLIENT COMMUNICATION\n\nTo: John Smith (CEO), Mary Jones (CFO), Bob Lee (VP Operations), outside_vendor@contractor.com\n\nHere is my legal advice regarding the pending regulatory matter..."
**Error types:** Privilege label is ineffective when non-client third parties are copied; CC to outside vendor (outside_vendor@contractor.com) destroys attorney-client privilege for this communication; disclosure to third parties = voluntary waiver; label cannot create privilege that distribution has already destroyed
**Corrections:** Remove all non-client recipients before sending privileged communications; if vendor input is needed, obtain it separately before seeking legal advice; the privilege label does not protect communications that have been disclosed to third parties
**Source/inspiration:** Fieldfisher "What You Need to Know About Privilege Waivers"; GWU Law "Waiver of Privilege — Voluntary Disclosure"

### Example 8

**Bad text:** "On advice of counsel, our client has decided not to respond to your discovery requests at this time."
**Error types:** "On advice of counsel" may waive the attorney-client privilege as to the substance of that advice (subject-matter waiver doctrine); if party relies on advice of counsel as a defense, they waive privilege as to all communications on that subject
**Corrections:** Simply state "Our client objects to the following requests on the grounds of [privilege/overbreadth/etc.]" without referencing that counsel advised the objection; if advice-of-counsel defense is intended, consult about the scope of resulting waiver before asserting it
**Source/inspiration:** GWU Law "Waiver of Privilege"; Federal common law subject-matter waiver doctrine

### Example 9

**Bad text:** "Dear Opposing Counsel, this letter is to confirm that our client will not be available for the deposition scheduled for next Thursday. We need to reschedule. Please let me know your availability."
**Error types:** "this letter is to confirm" (throat-clearing nominalization); "will not be available" (vague reason — may trigger sanctions if no good cause); "next Thursday" (no date certain — ambiguous); no proposed alternative dates offered
**Corrections:** Delete "this letter is to confirm that"; state specific reason for unavailability; use date certain; propose at least two alternative dates to show good faith compliance with scheduling obligations
**Source/inspiration:** FRCP 26(f) meet-and-confer requirements; local court rules on deposition scheduling

### Example 10

**Bad text:** "We write to memorialize our understanding of the agreement reached between the parties during the phone call on February 14. The parties agreed that Plaintiff will dismiss the case with prejudice, that Defendant will pay $50,000 within 60 days, and that both parties will exchange mutual releases. Please sign below to confirm."
**Error types:** Memorialization email without "subject to formal written agreement" = possible binding contract; "sign below" in an email may constitute execution; no attorney signature authorization stated; no governing law; no confidentiality provision for settlement terms
**Corrections:** Add "This is a non-binding summary for discussion purposes only. No settlement shall be binding until both parties execute a formal, written Settlement Agreement and Release."; do not include signature lines in a memorialization email
**Source/inspiration:** UETA/E-SIGN contract formation risk; LSU Law Review "Email and the Threat of Inadvertent Settlement"

### Example 11

**Bad text:** "The client wanted me to let you know that they are not happy with how this is going and thinks you should do something about it ASAP because the deadline is this week."
**Error types:** "the client wanted me to let you know" (multiple layers of indirection; attorney should communicate directly and professionally); "not happy" (unprofessional register); "thinks you should do something about it" (no specific request); ASAP (informal); "this week" (no date certain)
**Corrections:** "Our client has expressed concern about [specific issue]. Please advise by [date] what steps you are taking to address [specific action needed] before the [specific date] deadline."
**Source/inspiration:** Garner "The Winning Brief" professional tone guidance; LawProse email clarity seminar

### Example 12

**Bad text:** "I wanted to reach out to touch base about the status of the matter. Hoping to hear from you soon!"
**Error types:** "I wanted to reach out" (unnecessary throat-clearing past tense — just do it); "touch base" (business cliché inappropriate for legal correspondence); "Hoping to hear from you soon!" (exclamation point unprofessional in legal correspondence; no action requested; no deadline)
**Corrections:** "Please provide a status update on [specific matter] by [date]."; use period not exclamation point
**Source/inspiration:** Garner on avoiding clichés; bar association professional correspondence guides

### Example 13

**Bad text:** "Without Prejudice\n\nDear Counsel, our client is open to settling this matter for the right number. We think somewhere in the $200,000 range would be appropriate. Let us know if this works."
**Error types:** "Without Prejudice" label alone is not a complete FRE 408 protection invocation in all jurisdictions; "the right number" (vague — no specific figure makes this ambiguous); "somewhere in the $200,000 range" (unclear whether this is $200,000 or approximately that amount); "Let us know if this works" vs "advise whether this proposal is acceptable"; no offer expiration
**Corrections:** Use "Without Prejudice and Subject to Federal Rule of Evidence 408"; specify a precise dollar amount; use "advise whether your client accepts this offer" rather than "let us know if this works"; include expiration date
**Source/inspiration:** FRE 408; bar ethics opinions on settlement communications

### Example 14

**Bad text:** "Please find attached herewith the documents responsive to your request dated March 1, 2026, for your review and consideration. Do not hesitate to contact the undersigned if you have any questions or concerns regarding same."
**Error types:** "Please find attached herewith" (archaic "herewith" + "find attached" construction); "for your review and consideration" (empty filler); "Do not hesitate to contact" (throat-clearing cliché); "the undersigned" (refers to self in third person — archaic); "regarding same" ("same" as pronoun — archaic legalese)
**Corrections:** "Attached are the documents responsive to your March 1, 2026 request. Please contact me with any questions."
**Source/inspiration:** Garner's Dictionary of Legal Usage on "herewith," "same," "the undersigned"; SFBA plain language guides

### Example 15

**Bad text:** "This e-mail is intended only for the use of the individual or entity to which it is addressed and may contain information that is privileged, confidential, and exempt from disclosure under applicable law. If you are not the intended recipient, any use, dissemination, distribution, or copying of this communication is strictly prohibited."
**Error types:** This boilerplate disclaimer does not create attorney-client privilege for non-privileged communications; does not prevent inadvertent waiver if already disclosed; courts have held these disclaimers have limited legal effect; appears on ALL emails (including non-privileged ones) diluting any protective value
**Corrections:** Restrict this disclaimer to genuinely privileged communications only; understand it provides limited protection and does not substitute for careful distribution practices; a disclaimer cannot retroactively create privilege
**Source/inspiration:** GWU Law "Voluntary Disclosure Waiver"; court rulings on ineffectiveness of boilerplate disclaimers

### Example 16

**Bad text:** "My client rejects your settlement offer and we are prepared to go to trial on this matter. However, if you are willing to reconsider and come to the table with a more reasonable offer, we would be open to continuing settlement discussions."
**Error types:** Simultaneous rejection and conditional counter-invitation creates ambiguity about whether the original offer remains open; "go to trial" threat without basis in procedural posture weakens leverage; "come to the table" (business cliché); "more reasonable offer" (no anchor number)
**Corrections:** State clearly whether the offer is rejected with or without counter; if countering, state a specific figure; avoid mixed messages that blur negotiating position
**Source/inspiration:** Contract negotiation communication strategy; Garner on precise legal correspondence

### Example 17

**Bad text:** "We apologize for any confusion that may have been caused by our previous correspondence."
**Error types:** "Any confusion that may have been caused" (passive construction distances author from the error); "apologize for any" (hedges — "any" suggests there may have been no confusion); mealy-mouthed non-apology that acknowledges nothing specific; in litigation context, may be read as admitting error while adding nothing to the record
**Corrections:** Either own the specific error ("Our March 3 letter incorrectly stated [X]. The correct information is [Y].") or do not apologize if no error occurred. Passive non-apologies create risk without providing clarity.
**Source/inspiration:** Garner on professional correspondence; risk management in attorney communications

### Example 18

**Bad text:** "Kindly be informed that the above-captioned matter has been scheduled for a conference before the Honorable [Judge Name] on the 15th day of March, 2026, at the hour of 10:00 a.m., in Courtroom 4B."
**Error types:** "Kindly be informed" (archaic throat-clearing); "above-captioned matter" (legalese — use the case name); "the 15th day of March, 2026" (archaic date format); "at the hour of 10:00 a.m." (archaic "at the hour of" — say "at 10:00 a.m."); "the Honorable [Judge Name]" acceptable in formal pleadings but excessive in routine correspondence
**Corrections:** "The [Case Name] conference is scheduled before Judge [Name] on March 15, 2026, at 10:00 a.m., in Courtroom 4B."
**Source/inspiration:** Garner "The Redbook" on plain language in legal correspondence

### Example 19

**Bad text:** "In the event that you fail to respond to this letter within ten (10) days of the date hereof, our client will have no choice but to pursue all available legal remedies."
**Error types:** "In the event that" (wordy — use "if"); "ten (10)" (numeral + spelled-out redundancy — unnecessary unless in a formal contract); "date hereof" (archaic "hereof" — say "this letter's date" or state the date); "will have no choice but to" (fatalistic phrasing that sounds hollow); "all available legal remedies" (vague threat with no specificity)
**Corrections:** "If you do not respond by [specific date], our client will file suit in [jurisdiction] for [specific cause of action]."
**Source/inspiration:** Garner on redundant numeral+word pairs; SFBA plain language guidance

### Example 20

**Bad text:** "Please be guided accordingly."
**Error types:** Vague instruction with no content; variant of the mocked "govern yourself accordingly"; gives recipient no information about what action to take or what the guidance is; creates illusion of a clear directive while communicating nothing
**Corrections:** Delete entirely, or replace with a specific instruction: "Please confirm by [date] that you will comply with [specific requirement]."
**Source/inspiration:** SFBA blog critique of "govern yourself accordingly"; Garner on empty legal formulas

### Example 21

**Bad text:** "Our client strongly denies all allegations contained in your demand letter and reserves all rights."
**Error types:** "strongly denies" adds no legal weight (denial is a denial); "all allegations contained in" (wordier than "the allegations in"); "reserves all rights" (vague boilerplate — which rights? under what agreement or law?); no substantive response to specific allegations
**Corrections:** Either address specific allegations individually or state a general denial with specificity about the basis; "reserves all rights" is acceptable but should identify what rights are reserved if any specific reservation matters
**Source/inspiration:** Garner on empty legalese; professional correspondence practice guidance

---

## Category: brief

### Example 1

**Bad text:** "It is well-established that summary judgment is appropriate when there is no genuine dispute of material fact. Clearly, the facts here establish that no such dispute exists, as Defendant's own documents obviously confirm."
**Error types:** "It is well-established that" (throat-clearing — the rule doesn't need to be introduced this way); "Clearly" (overconfident booster that irritates judges when disputed facts follow); "obviously" (same problem — if it were obvious you wouldn't need to argue it); two boosters in one sentence signals weak argument
**Corrections:** Delete "It is well-established that"; state the rule directly; delete "Clearly" and "obviously"; let the facts establish themselves without announcing they are obvious
**Source/inspiration:** BriefCatch "Legal Writing Mistakes That Undermine Credibility"; SFBA brief writing tips; Garner "The Winning Brief"

### Example 2

**Bad text:** "Plaintiff respectfully submits that the motion should be denied for the following reasons. First, it is important to note that Defendant has failed to meet its burden. It bears emphasizing that the standard of review favors Plaintiff here."
**Error types:** "respectfully submits" (throat-clearing opener — courts know this is advocacy); "it is important to note that" (throat-clearing — tell them the thing, don't announce you're about to); "It bears emphasizing that" (another throat-clearer); three consecutive sentences with dummy-it introductions; buried subjects and verbs
**Corrections:** "The Court should deny the motion for three reasons. Defendant has not met its burden. The deferential standard of review confirms this result."
**Source/inspiration:** BriefCatch throat-clearing flagging system; WordRake "Throat-Clearing Phrases in Legal Writing"

### Example 3

**Bad text:** "Smith v. Jones, 123 F.3d 456, 459 (2nd Cir. 2001)."
**Error types:** "2nd Cir." — Bluebook abbreviates Second Circuit as "2d Cir." not "2nd Cir."; page pinpoint format is correct; full case citation format otherwise acceptable; "2nd" is the most common circuit abbreviation error
**Corrections:** "Smith v. Jones, 123 F.3d 456, 459 (2d Cir. 2001)."
**Source/inspiration:** Bluebook Rule 10.4; Fordham Law "Fifteen Common Bluebooking Errors"

### Example 4

**Bad text:** "Id. at 459. The court further explained that... Id. at 461. However, Smith, 123 F.3d at 459, holds that..."
**Error types:** Using "Id." and then switching to full short-form cite ("Smith, 123 F.3d at 459") after an intervening cite — correct; BUT: using "Id." when there is an intervening citation to a different source between the two uses is incorrect; "Id." must refer to the immediately preceding cited authority with no intervening cites
**Corrections:** If any other authority appears between two cites to the same source, do not use "Id." — use the full short form instead: "Smith, 123 F.3d at 461."
**Source/inspiration:** Bluebook Rule 10.9; Fordham "Fifteen Common Bluebooking Errors" #3

### Example 5

**Bad text:** "The motion was filed by Defendant. The brief was reviewed by the court. The standard was applied incorrectly by Plaintiff's counsel."
**Error types:** Three consecutive passive-voice sentences; subjects are obscured; actions are buried; who did what to whom is unclear; monotonous sentence structure; passive constructions inflate word count
**Corrections:** "Defendant filed the motion. The court reviewed the brief. Plaintiff's counsel misapplied the standard."
**Source/inspiration:** BriefCatch passive voice lessons; Columbia Law "Clear and Active Legal Writing" handout; Loyola Law passive voice guidance

### Example 6

**Bad text:** "The Plaintiff, who is the party that brought this action against the Defendant, alleges that the Defendant, who is the corporate entity named in the caption, breached the contract, which was entered into on January 1, 2024, by failing to make payment."
**Error types:** "who is the party that brought this action" (define parties in a fact section and use defined terms throughout — do not re-explain every reference); "who is the corporate entity named in the caption" (same problem); embedded relative clauses stack to create 50-word sentence; sentence structure buries the key allegation (breach)
**Corrections:** After introducing parties once ("Plaintiff ABC Corp. ('ABC') and Defendant XYZ LLC ('XYZ')"), use the defined terms: "ABC alleges that XYZ breached the January 1, 2024 contract by failing to make payment."
**Source/inspiration:** Garner "The Winning Brief" on party identification; BriefCatch sentence complexity analysis

### Example 7

**Bad text:** "Defendant argues that the contract is unambiguous, and therefore extrinsic evidence should not be admitted, but Plaintiff contends that the contract is ambiguous, and therefore the court should admit extrinsic evidence to interpret the parties' intent."
**Error types:** String of clauses connected by "and therefore" creates a run-on; argument structure is not IRAC — it presents both sides without taking a position; "the parties' intent" (vague — whose intent, on what specific term?); brief should argue, not summarize both positions neutrally
**Corrections:** Structure as argument: "The contract is unambiguous on its face, and extrinsic evidence is inadmissible. [Rule.] [Application to specific contract language.] Defendant's argument that extrinsic evidence should be excluded therefore controls."
**Source/inspiration:** CREAC/IRAC structure guidance; Garner "The Winning Brief" ch. 4

### Example 8

**Bad text:** "In Smith v. Jones, supra, the court held that..."
**Error types:** "supra" should not be used for cases; Bluebook Rule 10.9 limits "supra" to secondary sources (books, articles); for cases, use the short-form case citation instead
**Corrections:** "In Smith, 123 F.3d at 459, the court held that..."
**Source/inspiration:** Bluebook Rule 10.9; Tarlton Law Library short-form citations guide; Fordham Bluebook tips

### Example 9

**Bad text:** "This case is about a breach of contract. The plaintiff is a company. The defendant is also a company. They entered into an agreement. The defendant did not fulfill its obligations."
**Error types:** All sentences are simple declaratives of identical length; "this case is about" (weakest possible opener — no framing of the dispute); "is a company" / "is also a company" (irrelevant without context); "did not fulfill its obligations" (vague — what obligations, when, how?); zero persuasive framing
**Corrections:** Lead with the theory of recovery and the key fact: "XYZ LLC promised to deliver $2 million in software by December 1, 2023. It delivered nothing. ABC Corp. now seeks damages for that breach."
**Source/inspiration:** Garner "The Winning Brief" on compelling statement of facts; Posner "Reflections on Judging" on opening statements

### Example 10

**Bad text:** "The Court should also consider the fact that the Plaintiff made multiple attempts to resolve this dispute through informal negotiations, mediation, and had also proposed arbitration as an alternative, each of which was rejected by the Defendant without explanation."
**Error types:** "The Court should also consider the fact that" (throat-clearing + nominalization of "consider"); faulty parallel structure ("informal negotiations, mediation, and had also proposed arbitration" — first two are nouns, third is a verb phrase); "each of which was rejected" (passive + dangling — what is "each of which" modifying?); comma before "each" creates ambiguity
**Corrections:** "The Plaintiff attempted to resolve this dispute through informal negotiations, mediation, and arbitration. Defendant rejected each without explanation."
**Source/inspiration:** Garner on parallel structure; Columbia Law "Clear and Active Legal Writing"

### Example 11

**Bad text:** "The data collected during the investigation show that Defendant's conduct, which constituted a material breach of the covenant of good faith and fair dealing which the parties agreed to uphold, was in direct violation of the agreement."
**Error types:** Two "which" clauses in a single sentence ("which constituted," "which the parties") — the second "which" is ambiguous (does it modify "dealing" or "covenant"?); squinting modifier (the first which-clause modifies "conduct" but is buried after "conduct"); sentence is 38 words — violates readability guidelines for legal prose
**Corrections:** Split into two sentences: "Defendant's conduct violated the agreement. Specifically, Defendant breached the covenant of good faith and fair dealing."
**Source/inspiration:** SFBA "Don't Misplace Your Modifiers"; RWU Law misplaced modifier handout; Garner on sentence length

### Example 12

**Bad text:** "In conclusion, for all the foregoing reasons and for any additional reasons as the Court may determine, Plaintiff respectfully requests that this Honorable Court grant the instant motion."
**Error types:** "In conclusion" (unnecessary transition — the conclusion section heading signals this); "for all the foregoing reasons" (vague back-reference); "and for any additional reasons as the Court may determine" (adds nothing and sounds uncertain); "the instant motion" (legalese — say "this motion"); "respectfully requests" (acceptable but "requests" alone suffices)
**Corrections:** "For the reasons stated above, Plaintiff requests that the Court grant the motion."
**Source/inspiration:** Garner "The Winning Brief" on conclusions; SFBA brief writing tips

### Example 13

**Bad text:** "Plaintiff's damages, which includes lost profits, consequential damages, and mitigation costs, was substantial."
**Error types:** Subject-verb agreement error: "damages" (plural subject) requires "were," not "was"; relative clause "which includes" also wrong — should be "which include" (agreeing with plural "damages"); "substantial" is conclusory without a dollar amount
**Corrections:** "Plaintiff's damages — including lost profits, consequential damages, and mitigation costs — were substantial. [State the amount.]"
**Source/inspiration:** Loyola Law subject-verb agreement guide; Garner on agreement errors

### Example 14

**Bad text:** "Being beyond any doubt insane at the time of the offense, the court ordered the defendant committed."
**Error types:** Classic dangling participial phrase — "Being beyond any doubt insane" must modify the subject that follows the comma, but the subject is "the court" — this says the court was insane; dangling modifier is a serious logic error that changes meaning
**Corrections:** "Because the defendant was beyond any doubt insane at the time of the offense, the court ordered commitment." OR: "The court, finding the defendant beyond any doubt insane at the time of the offense, ordered commitment."
**Source/inspiration:** RWU Law misplaced modifiers handout (this example appears verbatim); SFBA modifier placement guide

### Example 15

**Bad text:** "Pursuant to Rule 56 of the Federal Rules of Civil Procedure, the defendant hereby moves this Court for an order granting summary judgment in favor of defendant and against plaintiff on all claims set forth in the complaint, and in support thereof respectfully shows the Court as follows..."
**Error types:** "Pursuant to" (use "Under"); "hereby moves" ("hereby" is archaic — delete); "in favor of defendant and against plaintiff" (redundant — summary judgment for one side is by definition against the other); "in support thereof" (archaic "thereof" — say "In support"); "respectfully shows the Court as follows" (archaic construction)
**Corrections:** "Under Federal Rule of Civil Procedure 56, Defendant moves for summary judgment on all claims. In support, Defendant states:"
**Source/inspiration:** Garner on "pursuant to," "hereby," "thereof"; SFBA plain language guide; Federal Plain Language Guidelines

### Example 16

**Bad text:** "Defendant's argument lacks merit. Plaintiff has thoroughly demonstrated, through extensive evidence and careful legal analysis, that the undisputed facts—which speak for themselves—clearly establish liability."
**Error types:** "lacks merit" (conclusory without explanation — what specific element fails?); "thoroughly demonstrated" + "extensive evidence" + "careful legal analysis" (self-congratulatory padding); "undisputed facts—which speak for themselves" (if facts spoke for themselves, you wouldn't need a brief); "clearly establish" (booster — if clearly, why argue it?)
**Corrections:** Delete all self-congratulatory modifiers; state specifically which element of the claim is satisfied and by what evidence; let the argument establish liability rather than asserting it is established
**Source/inspiration:** BriefCatch credibility-undermining patterns; Garner "The Winning Brief" on argument quality

### Example 17

**Bad text:** "The Plaintiff argues that he was terminated based on race. The Defendant argues that the termination was performance-based. The Plaintiff has presented statistical evidence. The Defendant disputes this evidence."
**Error types:** Brief presents both sides' arguments without taking a position (pure neutrality — appropriate for a memo, not a brief); no IRAC/CREAC structure; writer is summarizing the dispute rather than advocating; each sentence is a simple declarative with no persuasive framing
**Corrections:** Adopt a clear position: "Plaintiff was terminated because of his race, not his performance. The statistical evidence shows that [X]: of the [N] employees terminated in the same period, [Y]% were [race]. Defendant's performance justification is pretextual because [specific reason]."
**Source/inspiration:** Garner "The Winning Brief" on argumentation; IRAC structure guidance

### Example 18

**Bad text:** "See, e.g., Smith v. Jones, 123 F.3d 456 (2d Cir. 2001); accord Brown v. Green, 234 F.3d 567 (9th Cir. 2002); but see White v. Black, 345 F.3d 678 (1st Cir. 2003)."
**Error types:** Misuse of "accord" — "accord" means a case that agrees with the cited case under a different but analogous rule; it is not interchangeable with "see also"; here, using "accord" for a case that simply agrees on the same point; "but see" requires a citation that contradicts the proposition, not merely states a different holding
**Corrections:** Use "see also" for cases agreeing on the same proposition; use "accord" only for a different legal basis reaching the same result; verify the signal before using it — Bluebook Rule 1.2 governs signal meanings
**Source/inspiration:** Bluebook Rule 1.2 (signal meanings); Fordham "Fifteen Common Bluebooking Errors"

### Example 19

**Bad text:** "The defendant was arrested for fornicating under a little-used statute."
**Error types:** Squinting modifier — "under a little-used statute" modifies "fornicating" but is placed where it reads as modifying "arrested" (i.e., the arrest was under the statute, or the fornicating was under the statute?); ambiguity changes the meaning; this classic legal writing example appears in modifier-placement guides
**Corrections:** "Under a little-used statute, the defendant was arrested for fornication." OR "The defendant was arrested for violating a little-used statute against fornication."
**Source/inspiration:** RWU Law modifier placement handout; LC Law "Modifiers: Misplaced, Squinting and Dangling"

### Example 20

**Bad text:** "It is arguable that the evidence will demonstrate that Defendant's actions were intentional and that they perhaps knew about the consequences before the breach occurred."
**Error types:** "It is arguable that" (double hedge — "arguable" + "it is" construction); "perhaps knew" (further hedge on top of "arguable"); "they knew" when subject is "Defendant's actions" (antecedent agreement — "they" refers to "actions" not "Defendant"); hedging here where the writer should be asserting damages undermines the argument entirely
**Corrections:** "The evidence demonstrates that Defendant acted intentionally. [Cite specific evidence.] Defendant knew of the likely consequences before the breach occurred. [Cite specific document or testimony.]"
**Source/inspiration:** BriefCatch credibility guidance; Garner on hedging language in advocacy

### Example 21

**Bad text:** "My client has discussed your proposal to fill the drainage ditch with his partners."
**Error types:** Classic misplaced modifier — "with his partners" is placed where it modifies "fill the drainage ditch" (saying the ditch will be filled with his partners) rather than "discussed" (the client discussed with partners); changes meaning to absurd result
**Corrections:** "With his partners, my client has discussed your proposal to fill the drainage ditch." OR: "My client has discussed your drainage-ditch proposal with his partners."
**Source/inspiration:** RWU Law misplaced modifiers handout (this example appears verbatim); SFBA modifier guide

### Example 22

**Bad text:** "[A brief filed with the court contained the note:] PROBABLY NOT WORTH ARGUING???"
**Error types:** Draft comment not removed before filing; demonstrates failure to proofread before submitting to court; unprofessional content admitted to court record; courts have cited this type of error as basis for sanctions and reduced fees
**Corrections:** Implement a pre-filing checklist including search for Track Changes comments, draft notes, and revision marks; use a separate working draft and a clean filing copy
**Source/inspiration:** RESEARCH-SUMMARY.md agent 1 citation; court opinions on brief quality; Seventh Circuit writing standards

---

## Category: contract

### Example 1

**Bad text:** "The Vendor shall promptly notify the Client and/or its designated representative of any security breach."
**Error types:** "and/or" is logically ambiguous — does it mean "A or B or both"? Courts have interpreted "and/or" differently across jurisdictions; Ken Adams (MSCD) counsels eliminating "and/or" entirely; "promptly" is undefined and courts have applied it variously from 24 hours to 30 days; "shall" applied to Vendor is correct per Adams but only if "shall" is used exclusively for obligations on the subject
**Corrections:** Replace "and/or" with "or" (if either suffices) or "and" (if both are required); define "promptly" with a specific timeframe: "within 72 hours of discovery"; keep "shall" for obligations
**Source/inspiration:** Ken Adams MSCD §3.6 (and/or); contract drafting ambiguity guidance; Washington State Bar News

### Example 2

**Bad text:** "The Vendor shall take commercially reasonable efforts to mitigate the impact of such breach within a reasonable time after discovery."
**Error types:** "Commercially reasonable efforts" is the effort standard; "efforts" should follow directly: "shall use commercially reasonable efforts" (not "shall take"); "within a reasonable time" stacks a second undefined standard on top of the first — double vagueness; courts in different jurisdictions interpret "commercially reasonable efforts" differently (some equate it with "best efforts")
**Corrections:** "The Vendor shall use commercially reasonable efforts to mitigate the impact of such breach within [X] business days after discovery." Define "commercially reasonable efforts" with specific benchmarks if the obligations are material
**Source/inspiration:** Ken Adams "Interpreting and Drafting Efforts Provisions" (Texas Business Law Journal); Adams on Contract Drafting blog

### Example 3

**Bad text:** "Having been notified of the breach, remediation efforts shall commence immediately."
**Error types:** Dangling participial phrase — "Having been notified of the breach" modifies the subject that follows, but the subject is "remediation efforts" (remediation was not notified); "shall" applied to "remediation efforts" (an inanimate object) is incorrect — "shall" should impose obligation on a capable actor; "immediately" is undefined
**Corrections:** "Upon receiving notice of the breach, the Vendor shall commence remediation efforts within [X] hours." Rework so "shall" governs the Vendor, not an abstract noun
**Source/inspiration:** Ken Adams MSCD on "shall" usage; Oregon Bar Bulletin on dangling modifiers in contracts

### Example 4

**Bad text:** "Interest Rate shall mean a rate per annum of 9 percent."
**Error types:** Using "shall" in a definition clause; definitions are declarations, not obligations; "shall mean" creates a false imperative obligating the Interest Rate to mean something; Ken Adams identifies this as a classic misuse of "shall" in definitions
**Corrections:** "'Interest Rate' means a rate of 9% per annum." Use "means" not "shall mean" in definitions
**Source/inspiration:** Ken Adams MSCD §2.21; Michigan Bar Journal "Using Shall or Will to Create Obligations"

### Example 5

**Bad text:** "The Company may not assign this Agreement without the prior written consent of the other Party, which consent shall not be unreasonably withheld."
**Error types:** "May not" is ambiguous — some courts read it as "is not permitted to" (prohibition) while others read it as "has the option not to" (discretion); Ken Adams recommends "must not" for prohibitions; "which consent shall not be unreasonably withheld" — the antecedent of "which" is "consent" but the clause is structured awkwardly; "unreasonably withheld" is not defined
**Corrections:** "The Company must not assign this Agreement without the prior written consent of the other Party. The other Party must not unreasonably withhold, condition, or delay its consent." Separate the prohibition from the obligation on the non-assigning party
**Source/inspiration:** Ken Adams MSCD on "may not" vs "must not"; Adams on Contract Drafting "'Shall Not ... Unless' vs 'May ... Only If'"

### Example 6

**Bad text:** "WHEREAS, Party A is a Delaware corporation engaged in the business of software development; WHEREAS, Party B desires to license certain software from Party A; WHEREAS, the parties desire to set forth their respective rights and obligations herein; NOW THEREFORE, in consideration of the mutual promises and covenants contained herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the parties agree as follows:"
**Error types:** "WHEREAS" recitals in all-caps archaic format; "WHEREAS" used for pure background (acceptable) and purpose (less useful); "herein" is ambiguous (does "herein" mean in this definition, this section, this article, or this agreement?); "other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged" (archaic boilerplate that adds no legal value in most jurisdictions); "parties agree as follows:" (the recitals themselves are not operative — this transition is unnecessary)
**Corrections:** Replace "WHEREAS" recitals with plain "Background" section in sentence form; delete archaic consideration boilerplate; "herein" → specify the instrument; simplify transition
**Source/inspiration:** Attorney at Work "Whereas, I Keep Telling Lawyers to Stop"; Ken Adams on recitals; Weagree contract drafting guides

### Example 7

**Bad text:** "The Client shall provide written notice of any breach within thirty (30) days of the occurrence of such breach, failing which the Client's right to claim breach shall be deemed waived."
**Error types:** "thirty (30)" — the numeral + spelled-out redundancy is unnecessary in contracts unless required by court rule; "occurrence of such breach" — if breach is disputed, when does the clock start? "failing which" (archaic construction); "shall be deemed waived" (Ken Adams — "deemed" creates constructive fiction; prefer "will be waived"); notice provision lacks specification of how notice must be delivered
**Corrections:** "The Client must provide written notice of any alleged breach within 30 days after the Client discovers it. If the Client fails to provide timely notice, the Client waives its right to claim that breach." Add: "Notice must be sent by [method] to [address]."
**Source/inspiration:** Ken Adams MSCD on "deemed"; weagree.com definitions best practices

### Example 8

**Bad text:** "The Licensor hereby grants to the Licensee a non-exclusive, non-transferable, limited, revocable license to use the Software."
**Error types:** "hereby grants" — "hereby" is archaic and redundant (the granting happens by virtue of the contract, not by the word "hereby"); stacked adjective string ("non-exclusive, non-transferable, limited, revocable") — "limited" is redundant when "non-exclusive" and "non-transferable" already limit scope; no scope of use stated (use for what purpose? in what territory?); no duration specified
**Corrections:** "The Licensor grants the Licensee a non-exclusive, non-transferable, revocable license to [use the Software for X purpose] in [territory] during the Term." Delete "hereby" and "limited"
**Source/inspiration:** Ken Adams MSCD on "hereby"; Adams on Contract Drafting blog

### Example 9

**Bad text:** "The parties agree that this Agreement shall be governed by and construed in accordance with the laws of the State of New York, without giving effect to any choice of law or conflict of law rules or provisions."
**Error types:** "shall be governed by and construed in accordance with" (doublet — "governed by" and "construed in accordance with" are redundant); "without giving effect to any choice of law or conflict of law rules or provisions" — this carve-out is intended to prevent application of New York's own choice-of-law rules pointing to another state's law, but "any ... rules or provisions" is overbroad and could be read to exclude New York contract law itself
**Corrections:** "This Agreement is governed by New York law, excluding its conflict-of-laws principles." Delete the doublet; simplify the carve-out
**Source/inspiration:** MSCD on governing law clauses; contract drafting best practices guides

### Example 10

**Bad text:** "Vendor agrees to indemnify Client for all losses, damages, costs and expenses arising from or related to any breach of this Section, including attorney's fees."
**Error types:** "arising from or related to" — "related to" is extremely broad and courts interpret it variably; no cap on indemnity; "attorney's fees" placed as an afterthought in "including" list (should be a separate obligation to avoid ejusdem generis limiting it to the type of items in the list); missing: notice requirement for indemnification claims, right to control defense, limitation on settlement without consent
**Corrections:** Separate the attorney's fees into its own sentence; define the scope of "arising from"; add cap; add indemnification procedure provisions
**Source/inspiration:** Ken Adams on indemnification clauses; MSCD; Goulston & Storrs "Efforts Clauses — Drafter Beware"

### Example 11

**Bad text:** "The Confidential Information shall be used solely and exclusively for the purposes set forth herein and for no other purpose whatsoever."
**Error types:** "solely and exclusively" (doublet — one word does the job); "for no other purpose whatsoever" (tautological — "solely for X" already means no other purpose; "whatsoever" is padding); "herein" is ambiguous; triple redundancy in a single clause
**Corrections:** "The Receiving Party may use Confidential Information only for [specific purpose stated in Section X]."
**Source/inspiration:** Ken Adams on redundant doublets; MSCD ch. 1 (words that courts have found ambiguous)

### Example 12

**Bad text:** "The term 'Systems' includes all hardware, software, and network infrastructure provided by Vendor to client pursuant to this agreement, including any third-party components."
**Error types:** Inconsistent capitalization — "Client" capitalized earlier but "client" lowercase here (breaks the defined-term rule from Clinton Assoc. v. Monadnock); "pursuant to this agreement" (use "under this Agreement"); "includes" in a definition is problematic — does it mean the list is exhaustive or exemplary? Should use "means" (exhaustive) or "means ... including" (non-exhaustive)
**Corrections:** Capitalize "Client" consistently; replace "pursuant to" with "under"; clarify scope: "'Systems' means all hardware, software, and network infrastructure that Vendor provides to Client under this Agreement, including any third-party components incorporated therein."
**Source/inspiration:** Clinton Assoc. v. Monadnock Construction (defined term capitalization case); Ken Adams "When the Definition Is the Same as the Defined Term"

### Example 13

**Bad text:** "Either party may terminate this Agreement for convenience upon reasonable notice."
**Error types:** "Reasonable notice" is undefined — courts have applied it as anywhere from 30 days to one year depending on the industry and circumstances; "for convenience" is correct usage but the notice period vagueness creates uncertainty; no specification of what "notice" means (written? oral? what delivery method?)
**Corrections:** "Either Party may terminate this Agreement for any reason upon [30 days'] prior written notice to the other Party."
**Source/inspiration:** Contract ambiguity guidance; Washington State Bar News on drafting for certainty

### Example 14

**Bad text:** "The parties shall use their best efforts to obtain all necessary approvals, consents, and permits required in connection with the transactions contemplated by this Agreement."
**Error types:** "Best efforts" in New York may be interpreted as more demanding than "reasonable efforts" or as equivalent — courts are split; stacking "approvals, consents, and permits" without specifying who obtains which and from whom; "required in connection with" is broader than necessary; "transactions contemplated by this Agreement" is the standard boilerplate catch-all that may sweep in unintended obligations
**Corrections:** Specify each approval/consent/permit; allocate responsibility (Buyer vs Seller); use "commercially reasonable efforts" or define the standard; specify the deadline
**Source/inspiration:** Ken Adams "Interpreting and Drafting Efforts Provisions"; Adams on Contract Drafting "What the Heck Does 'Best Efforts' Mean?"; Georgetown Law Journal "Is This Really the Best We Can Do?"

### Example 15

**Bad text:** "WHEREAS, the Company shall provide quarterly financial reports to Investor by the 15th of each month following the calendar quarter."
**Error types:** Recitals (WHEREAS clauses) should not contain operative obligations; obligations belong in the operative provisions of the agreement; an obligation in a recital creates ambiguity about enforceability; additionally "15th of each month following the calendar quarter" is ambiguous — does "month following" mean the first month after quarter-end or any month?
**Corrections:** Move this obligation to an operative section: "No later than 45 days after each calendar quarter, the Company must deliver to Investor quarterly financial reports prepared in accordance with [GAAP/the specifications in Exhibit A]." Delete the WHEREAS version
**Source/inspiration:** Weagree "Recitals" guide; CEB "9 Best Practices for Drafting Useful Recitals"; Florida Bar "Fifty Tips for Writing the 21st Century Contract"

### Example 16

**Bad text:** "The Agreement may not be modified or amended except by a writing signed by both parties, provided, however, that the parties may, by mutual agreement, waive this requirement."
**Error types:** The proviso immediately defeats the amendment clause — "provided, however, that parties may by mutual agreement waive this requirement" allows any oral agreement to modify the contract, making the written amendment requirement meaningless; this self-defeating proviso pattern is extremely common in boilerplate and has been litigated
**Corrections:** Delete the self-defeating proviso, OR: "The Agreement may be modified only by a written amendment signed by authorized representatives of both Parties. No oral agreement or course of dealing shall constitute a modification." The parties cannot validly agree to orally waive a written-modification requirement in many jurisdictions anyway
**Source/inspiration:** Florida Bar "Fifty Tips for Writing the 21st Century Contract"; contract drafting guidance on anti-oral-modification clauses

### Example 17

**Bad text:** "The Contractor represents and warrants that it has the full right, power, authority, and capacity to enter into this Agreement."
**Error types:** "represents and warrants" — Ken Adams argues these are distinct: "represents" is a statement of past or present fact; "warrants" is a promise that something is true with indemnification as the remedy for breach; stacking them conflates the remedial schemes; "right, power, authority, and capacity" — "right" and "authority" are largely synonymous; "power" and "capacity" overlap; four-word string adds no precision
**Corrections:** Determine whether a representation (looking backward to current facts, damages remedy) or a warranty (promise, indemnification remedy) is intended. "The Contractor represents that it has full authority to enter into this Agreement." OR use separate provisions for each.
**Source/inspiration:** Ken Adams on "represents and warrants"; MSCD ch. 12; IP Draughts "10 Things I Hate to See in Contracts"

### Example 18

**Bad text:** "Time is of the essence with respect to all dates and deadlines set forth in or referred to in this Agreement."
**Error types:** Blanket "time is of the essence" applied to every date and deadline is overbroad; makes breach of any deadline a material breach triggering termination rights; courts have found this catches parties who miss trivial dates; should be applied selectively to the dates that actually matter (closing date, expiration date) not to notice periods or administrative deadlines
**Corrections:** "Time is of the essence with respect to the Closing Date set forth in Section 3.1." Apply specifically, not globally
**Source/inspiration:** Contract drafting practice; IP Draughts blog; Florida Bar "Fifty Tips"

### Example 19

**Bad text:** "In the event of any dispute, controversy, or claim arising out of or relating to this Agreement, or the breach, termination, or invalidity thereof, the parties shall negotiate in good faith to resolve such dispute for a period of thirty (30) days."
**Error types:** "dispute, controversy, or claim" (triple synonym — pick one or two meaningful terms); "breach, termination, or invalidity thereof" ("thereof" is archaic); "thirty (30) days" (redundant numeral format); no consequence stated if negotiation fails; "negotiate in good faith" is difficult to enforce and courts rarely compel it
**Corrections:** "If a dispute arises under this Agreement, the parties will attempt to resolve it through good-faith negotiation for 30 days. If unresolved after 30 days, either party may submit the dispute to [arbitration/mediation/litigation] under Section X."
**Source/inspiration:** MSCD on dispute resolution provisions; Ken Adams on archaic language

### Example 20

**Bad text:** "Notwithstanding anything herein to the contrary, the provisions of Sections 5, 7, and 14 shall survive the termination or expiration of this Agreement."
**Error types:** "Notwithstanding anything herein to the contrary" (Garner and Adams both criticize this as the most overused and often meaningless phrase in contracts — it signals that the drafter couldn't figure out how to reconcile conflicting provisions); "herein" is ambiguous; "termination or expiration" — the survival clause should also address what happens upon material breach; the listed sections may not be the only ones that should survive
**Corrections:** Eliminate the "notwithstanding" boilerplate if there is no actual conflict; do a conflict analysis first. "Sections 5 (Confidentiality), 7 (Indemnification), and 14 (Limitation of Liability) survive any termination, expiration, or other ending of this Agreement." Add other survivor sections after reviewing the whole contract
**Source/inspiration:** Ken Adams on "notwithstanding" boilerplate; MSCD; Florida Bar "Fifty Tips"

---

## Category: plain

### Example 1

**Bad text:** "Witnesseth: THAT the party of the first part, hereinafter referred to as 'Lessor,' for and in consideration of the covenants and agreements herein contained and the payment of rent as herein provided, does hereby lease unto the party of the second part, hereinafter referred to as 'Lessee'..."
**Error types:** "Witnesseth" (archaic verb form, no modern legal purpose); "party of the first part/second part" (Dickensian — use real names or defined terms); "for and in consideration of" (legalistic doublet preamble); "herein contained" ("herein" ambiguous); "does hereby lease" ("does hereby" is archaic ceremonial padding); "lease unto" ("unto" archaic)
**Corrections:** "Lessor leases the Premises to Lessee on the following terms:" — the entire recitation can be replaced with one sentence using defined terms
**Source/inspiration:** Garner "Garner's Usage Tip of the Day: Legalese"; Attorney at Work "Whereas, I Keep Telling Lawyers"; Marie Buckley legal writing blog

### Example 2

**Bad text:** "The aforementioned party (hereinafter 'Defendant') did theretofore engage in conduct violative of the abovementioned statute."
**Error types:** "Aforementioned" (use the party's name or the defined term); "hereinafter" (if you're using a defined term, introduce it once and use it — "hereinafter" is unnecessary); "theretofore" (archaic — means "before that time"; almost never necessary); "violative of" (awkward adjective construction — use "violated"); "abovementioned" (archaic — use "the" or cite the section)
**Corrections:** "Defendant violated the statute." If context requires more: "The Defendant violated Section 12(b) of the Act."
**Source/inspiration:** SFBA "Banish These Words and Phrases"; Garner "Dictionary of Legal Usage" on archaic compounds

### Example 3

**Bad text:** "The lessee shall make payment of rent in the sum of Two Thousand Dollars ($2,000.00) on the first day of each calendar month pursuant to the terms and conditions of this lease agreement."
**Error types:** "Make payment of" (nominalization of "pay"); "in the sum of" (legalese — just use the number); "Two Thousand Dollars ($2,000.00)" (double-statement of amount — only necessary in checks and formal instruments, not in contracts according to Garner); "on the first day of each calendar month" (wordy — "on the first of each month"); "pursuant to" (use "under"); "terms and conditions" (doublet — use "terms")
**Corrections:** "The Lessee must pay $2,000 in rent on the first of each month."
**Source/inspiration:** Garner on "make payment of"; SFBA plain language guide; Texas Bar Practice blog on legalese

### Example 4

**Bad text:** "Be it known to all men by these presents that..."
**Error types:** Archaic opening formula with no modern legal function; "all men" (non-inclusive); "by these presents" (archaic — "these presents" refers to this document, completely unnecessary); entire phrase is ceremonial throat-clearing with zero legal content
**Corrections:** Delete entirely. The contract is self-evident as a document.
**Source/inspiration:** Garner on archaic legal formulas; evolution of legal language guides

### Example 5

**Bad text:** "In the event that the lessee fails to make timely payment of rent, the lessor shall have the right to exercise any and all remedies available under applicable law."
**Error types:** "In the event that" (5 words → 1 word: "if"); "make timely payment of" (nominalization — "pay rent on time"); "shall have the right to" (pompous — use "may"); "any and all" (classic doublet with zero added meaning — "any" and "all" overlap completely); "available under applicable law" (vague — specify the remedies or remove this qualifying phrase)
**Corrections:** "If the Lessee fails to pay rent on time, the Lessor may pursue any remedy available under this Agreement or applicable law."
**Source/inspiration:** Garner on "any and all"; Federal Plain Language Guidelines "In the Event That"; Texas Bar Practice blog

### Example 6

**Bad text:** "Prior to the commencement of the work, the Contractor shall obtain all necessary permits."
**Error types:** "Prior to" (legalese — use "before"); "commencement of the work" (nominalization — "the work commences" or "beginning the work"); "obtain all necessary permits" is acceptable but "all necessary" is vague
**Corrections:** "Before beginning the work, the Contractor must obtain all permits required by applicable law."
**Source/inspiration:** Garner "The Redbook" on "prior to"; Federal Plain Language Guidelines; SFBA word substitution guide

### Example 7

**Bad text:** "The parties desire to set forth herein their mutual understanding with respect to the subject matter hereof."
**Error types:** "Desire to set forth" (recital purpose statement that adds nothing); "herein" (ambiguous); "their mutual understanding with respect to" (nominalization + preposition string — use "about"); "subject matter hereof" (archaic "hereof" — use "this Agreement")
**Corrections:** Delete the clause entirely if it's in recitals. If needed: "The parties agree to the following terms."
**Source/inspiration:** Attorney at Work on recital language; Weagree contract drafting guide

### Example 8

**Bad text:** "The undersigned hereby acknowledges receipt of the foregoing and agrees to be bound by the terms and conditions set forth hereinabove."
**Error types:** "The undersigned" (refers to self in third person — archaic); "hereby acknowledges" ("hereby" archaic filler); "the foregoing" (what foregoing? ambiguous pronoun); "set forth hereinabove" ("hereinabove" = archaic — say "above" or cite the section)
**Corrections:** "I have read and agree to the terms in Sections [X-Y] above." (for individual) or "[Company Name] acknowledges receipt and agrees to the terms in this Agreement."
**Source/inspiration:** Garner on "the undersigned," "hereby," "hereinabove"; SFBA archaic compound words list

### Example 9

**Bad text:** "Null and void" / "cease and desist" / "terms and conditions" / "any and all" / "due and payable" / "full and complete" / "true and correct"
**Error types:** All are legal doublets — pairs of synonyms or near-synonyms that add no precision; each pair means the same as either word alone; originated as bilingual bridging (Anglo-Saxon + Latin/French) in post-Norman England; none of these pairings are required terms of art in modern drafting
**Corrections:** "void" alone; "cease" OR "desist" (pick one); "terms" alone; "any" OR "all" depending on meaning; "due"; "complete" or "full"; "correct" or "accurate." Ken Adams recommends using the one word that best expresses the intended meaning
**Source/inspiration:** Legal Doublet Wikipedia; WordRake "Trimming Legal Doublets"; Garner "Dictionary of Legal Usage"; Ken Adams MSCD on redundant pairs

### Example 10

**Bad text:** "Said agreement" / "said party" / "said document"
**Error types:** "Said" used as adjective meaning "the previously mentioned" — pure archaic legalese with no modern equivalent function; Garner calls this usage a "signal that the writer is stuck in the 18th century"; courts have found "said" to mean "the aforementioned" which can create ambiguity when multiple agreements/parties have been mentioned
**Corrections:** Use "the Agreement," "the Party," or "this document" — or better, the defined term that was introduced earlier
**Source/inspiration:** Garner "Dictionary of Legal Usage" entry on "said"; SFBA plain language guide

### Example 11

**Bad text:** "The Employer reserves the right, at its sole and exclusive discretion, to modify, alter, change, or amend these policies at any time, with or without notice, for any reason or no reason whatsoever."
**Error types:** "Reserves the right" (pompous — use "may"); "sole and exclusive" (doublet — use "sole"); "modify, alter, change, or amend" (four near-synonyms where one word — "change" or "amend" — suffices); "at any time, with or without notice" is legitimate but "for any reason or no reason whatsoever" is verbose padding
**Corrections:** "The Employer may change these policies at any time with or without notice." If at-will employment caveat needed, add it separately.
**Source/inspiration:** Federal Plain Language Guidelines; Garner on "reserves the right"; legal doublets guidance

### Example 12

**Bad text:** "In witness whereof, the parties hereto have executed this Agreement as of the day and year first above written."
**Error types:** "In witness whereof" (archaic ceremonial phrase — no legal function); "the parties hereto" ("hereto" archaic — use "the parties" or their names); "as of the day and year first above written" (archaic back-reference — use the actual date); this traditional closing adds no legal content and mystifies non-lawyers
**Corrections:** "The parties have signed this Agreement as of [Date]." or use a signature block with date lines
**Source/inspiration:** Garner on archaic ceremonial closings; Attorney at Work "Stop Writing Like a Lawyer from 1850"

### Example 13

**Bad text:** "It is the intention of the parties that the provisions hereof be interpreted in a manner consistent with the intent of the parties."
**Error types:** "It is the intention of the parties that" (throat-clearing nominalization — parties should just state the rule); "provisions hereof" ("hereof" archaic); "in a manner consistent with" (wordy — use "to"); circular: "interpreted consistent with intent of parties" — every contract should be; adds no content
**Corrections:** Delete if in recitals — this is pure boilerplate noise. If a genuine interpretation rule is needed, state it specifically: "Ambiguous terms in this Agreement are to be interpreted in favor of the obligations the parties explicitly undertook."
**Source/inspiration:** Florida Bar "Fifty Tips"; Garner on circular provisions

### Example 14

**Bad text:** "Notwithstanding the foregoing, and without limiting the generality of the provisions contained hereinabove or hereinbelow..."
**Error types:** "Notwithstanding the foregoing" (most overused phrase in contract drafting — signals unresolved conflict in the document); "without limiting the generality of" (courts have held this phrase can either expand or restrict the clause that precedes it — creates ambiguity); "hereinabove or hereinbelow" (both archaic — say "above" or "below" or cite sections)
**Corrections:** Do a structural edit to resolve the conflict that made "notwithstanding" necessary; cite specific sections; delete "without limiting the generality of" entirely
**Source/inspiration:** Ken Adams "Notwithstanding" usage; Adams on Contract Drafting blog; MSCD

### Example 15

**Bad text:** "Each Party shall have the obligation to indemnify, defend, save and hold harmless the other Party from and against any and all claims..."
**Error types:** "Shall have the obligation to" (nominalization — use "must"); "indemnify, defend, save and hold harmless" (four-word string; "save and hold harmless" is itself a doublet embedded in the string; "indemnify" and "hold harmless" overlap significantly; "defend" is the distinct operative duty); "from and against" (doublet — use "against"); "any and all" (doublet)
**Corrections:** "Each Party must indemnify and defend the other Party against any claims..." Then define what "indemnify" covers vs what "defend" covers as separate obligations
**Source/inspiration:** Ken Adams on indemnification language; MSCD ch. 13; WordRake doublets guide

### Example 16

**Bad text:** "The Contractor agrees to perform the work in a good and workmanlike manner."
**Error types:** "Good and workmanlike" is a legal doublet; "good" adds nothing to "workmanlike"; the phrase itself is a legal term of art in some jurisdictions (construction contracts) but its content is undefined; courts have interpreted it differently; if a standard matters, specify it
**Corrections:** If using as term of art in a construction contract, keep it but add: "consistent with the standards of the [specific trade] profession in [jurisdiction]." In other contracts, use a specific performance standard
**Source/inspiration:** Ken Adams on doublets; contract drafting quality standards

### Example 17

**Bad text:** "To the extent permitted by applicable law, and subject to the limitations set forth herein, including without limitation those set forth in Section 12..."
**Error types:** "To the extent permitted by applicable law" — this phrase is used to limit a provision but courts have found it so vague as to be unenforceable in some contexts; "subject to the limitations set forth herein" is circular (the limitations are in the contract); "including without limitation" — "including" in a list under ejusdem generis already implies non-exhaustive; "without limitation" is meant to prevent ejusdem generis but its effect is disputed
**Corrections:** State the specific limitation that applies; cite Section 12 directly; remove the circular "herein" reference; decide whether the list is exhaustive or non-exhaustive and draft accordingly
**Source/inspiration:** Washington State Bar News on ambiguity; Ken Adams on "to the extent" and "including without limitation"

### Example 18

**Bad text:** "The parties acknowledge and agree that time is of the essence with respect to each and every obligation, date, deadline, term, condition, and requirement set forth in this Agreement."
**Error types:** "acknowledge and agree" (doublet — use one or the other); "each and every" (doublet — use "each" or "every"); "obligation, date, deadline, term, condition, and requirement" (five-word string where "obligation" already covers the others if drafted properly); blanket time-is-of-the-essence as noted above creates trap for trivial deadlines
**Corrections:** "Time is of the essence with respect to the Closing Date in Section 3.1." Apply specifically, not with a noun avalanche
**Source/inspiration:** IP Draughts blog; Florida Bar "Fifty Tips"; Ken Adams on doublets and noun strings

### Example 19

**Bad text:** "Nothing in this Agreement shall be construed to limit or restrict in any way the rights, remedies, or other recourse of any party under applicable law."
**Error types:** "Nothing in this Agreement shall be construed" (passive throat-clearing); "limit or restrict" (doublet); "in any way" (redundant qualifier); "rights, remedies, or other recourse" (string where "remedies" encompasses most recourse); "under applicable law" (which law? this is non-specific)
**Corrections:** "This Agreement does not limit any party's rights under applicable law." Or be specific about what rights are preserved and under what law
**Source/inspiration:** Ken Adams on boilerplate; MSCD ch. 16 (miscellaneous provisions)

### Example 20

**Bad text:** "The parties hereto agree that, pursuant to and in accordance with the terms, conditions, and provisions of this Agreement and applicable law, Vendor shall effectuate delivery of the goods."
**Error types:** "parties hereto" (archaic "hereto"); "pursuant to and in accordance with" (doublet phrase — use "under"); "terms, conditions, and provisions" (three-way near-synonym string); "applicable law" without specificity; "shall effectuate delivery of" (nominalization — "shall deliver")
**Corrections:** "Under this Agreement, Vendor must deliver the goods."
**Source/inspiration:** Garner on "effectuate" and nominalizations; SFBA plain language guide; Federal Plain Language Guidelines

---

## Category: grammar

### Example 1

**Bad text:** "The prosecutor's expectation was that defense counsel would make an objection to the evidence."
**Error types:** Nominalization chain — "expectation" (expect), "make an objection" (object); verb "expected" and verb "objected" are each buried in noun forms; sentence is 16 words; active version is 9 words
**Corrections:** "The prosecutor expected defense counsel to object to the evidence."
**Source/inspiration:** Legal Writing Editor "On Nominalizations"; UT Austin legal writing blog

### Example 2

**Bad text:** "There is an agreement between the two parties for a settlement of $1 million."
**Error types:** Existential "there is" construction delays the real subject; "is an agreement" buries the verb "agreed"; "for a settlement of" (three prepositions leading to the amount); passive/existential construction obscures who the actors are
**Corrections:** "The parties agreed to a $1 million settlement."
**Source/inspiration:** UT Austin "When Verbs Become Nouns"; Columbia Law "Clear and Active Legal Writing"

### Example 3

**Bad text:** "The plaintiff made a determination that the defendant's conduct was in violation of the contract."
**Error types:** "Made a determination" buries "determined"; "was in violation of" buries "violated"; two nominalizations in a single sentence; 18 words become 8 words after revision
**Corrections:** "The plaintiff determined that the defendant violated the contract."
**Source/inspiration:** Marquette Law "Controlling Passive Voice and Nominalizations"; common legal writing nominalization list

### Example 4

**Bad text:** "It is the position of the plaintiff that the defendant's failure to make payment constitutes a breach."
**Error types:** "It is the position of" (existential dummy-subject construction); "failure to make payment" buries "failure to pay" and further buries "did not pay"; "constitutes a breach" → "is a breach"; three layers of nominalization
**Corrections:** "The plaintiff argues that the defendant's failure to pay constitutes a breach." Better: "The defendant did not pay. That is a breach."
**Source/inspiration:** AZ Attorney magazine "Legal Word"; legal writing nominalization guides

### Example 5

**Bad text:** "The company conducted an investigation of the incident and made a recommendation for the implementation of new safety procedures."
**Error types:** "Conducted an investigation" → "investigated"; "made a recommendation" → "recommended"; "for the implementation of" → "to implement"; three nominalizations in one sentence; 22 words become 10
**Corrections:** "The company investigated the incident and recommended implementing new safety procedures."
**Source/inspiration:** WordRake "How to Spot Nominalizations"; LawProse Lesson #188

### Example 6

**Bad text:** "Plaintiff's damages, which includes lost profits, consequential damages, and the costs of mitigation, was substantial."
**Error types:** Subject-verb agreement: "damages" is plural → "include" and "were"; compound subject in the which-clause also requires "include" not "includes"; the predicate "was" must agree with "damages" (plural) → "were"
**Corrections:** "Plaintiff's damages — including lost profits, consequential damages, and mitigation costs — were substantial."
**Source/inspiration:** Loyola Law subject-verb agreement guide; grammar-test-samples.md Sample 2

### Example 7

**Bad text:** "Each of the defendants were found liable by the jury."
**Error types:** "Each" is always singular — requires singular verb; "each of the defendants" → "each ... was"; "were found" is incorrect; "by the jury" is passive voice (though sometimes appropriate in this context)
**Corrections:** "Each defendant was found liable." OR: "The jury found each defendant liable." (active)
**Source/inspiration:** Garner "Garner's Modern American Usage" on "each"; University of Toronto Writing Advice

### Example 8

**Bad text:** "The court's holding in Smith v. Jones, which was decided in 2001, which established a new standard for causation, which has since been applied in over 50 cases..."
**Error types:** Triple "which" relative clause stack — each clause modifies an unclear antecedent; "which was decided in 2001" (modifies "holding" or "Smith v. Jones"?); "which established" (same ambiguity); "which has since been applied" (now modifying what?); sentence never completes a predicate
**Corrections:** "In Smith v. Jones (2001), the court established a new standard for causation that has since been applied in over 50 cases."
**Source/inspiration:** Garner on relative clause stacking; Columbia Law "Clear and Active Legal Writing"

### Example 9

**Bad text:** "Having reviewed the complaint, the motion to dismiss was filed."
**Error types:** Dangling participial phrase — "Having reviewed the complaint" must modify the subject immediately following it; the subject is "the motion to dismiss" (the motion didn't review the complaint); this is the most common dangling modifier in legal writing
**Corrections:** "Having reviewed the complaint, defense counsel filed the motion to dismiss." OR: "After reviewing the complaint, defense counsel filed the motion to dismiss."
**Source/inspiration:** Purdue OWL "Dangling Modifiers"; RWU Law handout; Loyola Law grammar guide

### Example 10

**Bad text:** "The attorney, after filing the brief, reviewing the record, and having conducted three client interviews, prepared the motion."
**Error types:** Faulty parallel structure — the series "filing the brief, reviewing the record, and having conducted" mixes gerunds (filing, reviewing) with perfect participle (having conducted); all three must use the same grammatical form
**Corrections:** "After filing the brief, reviewing the record, and conducting three client interviews, the attorney prepared the motion."
**Source/inspiration:** Garner on parallel structure; Columbia Law writing handout

### Example 11

**Bad text:** "The judge stated that the defendant's conduct was inappropriate, citing numerous violations, that had alarmed the court, and recommending enhanced sentencing."
**Error types:** The "that" clause ("that had alarmed the court") breaks the flow of the parallel participial series (citing, recommending); "citing ... that ... and recommending" is not parallel; the relative clause interrupts the participle chain with a different construction
**Corrections:** "The judge stated that the defendant's conduct was inappropriate. She cited numerous violations that had alarmed the court and recommended enhanced sentencing."
**Source/inspiration:** Garner on parallel structure and restrictive relative clauses

### Example 12

**Bad text:** "The plaintiff only relied on three cases in its brief."
**Error types:** Misplaced "only" — "only" should modify the word it logically limits; here "only three" is the intended meaning, but "only" placed before "relied" means "did nothing but rely"; placement of "only" changes meaning: "The plaintiff relied only on three cases" = correct
**Corrections:** "The plaintiff relied on only three cases in its brief." OR: "In its brief, the plaintiff cited only three cases."
**Source/inspiration:** Garner "Garner's Modern American Usage" on "only"; SFBA writing tips

### Example 13

**Bad text:** "The evidence is clear: the defendant drove recklessly, ran a red light, and had been drinking alcoholic beverages prior to the accident."
**Error types:** Faulty parallel structure — "drove recklessly," "ran a red light," and "had been drinking" mix tenses and aspects; the first two are simple past, the third is past perfect progressive; the third element is also longer and more complex than the first two, disturbing rhythm
**Corrections:** "The evidence is clear: the defendant drove recklessly, ran a red light, and drank alcoholic beverages before the accident."
**Source/inspiration:** Garner on parallel structure in lists; legal writing style guides

### Example 14

**Bad text:** "Pursuant to our discussions, it is our understanding that your client may possibly be willing to consider the potential option of settling."
**Error types:** "May possibly" (double modal — "may" already indicates possibility); "be willing to consider" (three hedges: may + willing + consider); "potential option" (redundant — an option is by definition potential); "of settling" (nominalization — use "a settlement"); five hedging words to say "might settle"
**Corrections:** "We understand your client may be willing to settle." Or if drafting a settlement inquiry: "Please advise whether your client will settle on the following terms."
**Source/inspiration:** Garner on redundant modifiers; BriefCatch hedging language patterns

### Example 15

**Bad text:** "The data shows that defendant's conduct was in violation of the statute."
**Error types:** "Data" is plural in formal writing — requires "show" not "shows" (though "data shows" is accepted in informal usage, formal legal writing should use "show"); "was in violation of" buries "violated"
**Corrections:** "The data show that the defendant violated the statute." (formal) OR "The data shows..." (if jurisdictions/court accepts data as collective singular)
**Source/inspiration:** Garner "Garner's Modern American Usage" on "data"; Loyola Law subject-verb agreement

### Example 16

**Bad text:** "The court will hear argument on Monday concerning whether Plaintiff's filing was timely, which was submitted last Tuesday."
**Error types:** Squinting modifier — "which was submitted last Tuesday" appears to modify either "filing" (Plaintiff's filing was submitted Tuesday) or "Monday's argument" (the argument was submitted Tuesday); both readings are possible; the court will hear argument "concerning the filing" not the argument itself that was submitted
**Corrections:** "On Monday, the court will hear argument on whether Plaintiff's filing, submitted last Tuesday, was timely."
**Source/inspiration:** SFBA "Don't Let Your Modifiers Squint"; Lewis & Clark "Modifiers: Misplaced, Squinting and Dangling"

### Example 17

**Bad text:** "The defendant was sentenced to five years in prison under the statute providing for enhanced penalties for repeat offenders who have committed prior offenses."
**Error types:** "Repeat offenders who have committed prior offenses" is tautological — "repeat offender" by definition has committed prior offenses; "prior offenses" is redundant in this context; the sentence structure buries the key fact (five years, enhanced penalties) in a long trailing clause
**Corrections:** "Under the enhanced-penalty statute for repeat offenders, the defendant was sentenced to five years in prison." Or lead with the sentence and then state the statutory basis.
**Source/inspiration:** Garner on redundant modifiers; legal writing clarity guides

### Example 18

**Bad text:** "The issue before this Court is whether or not the statute's application to these facts constitutes a violation of the plaintiff's due process rights."
**Error types:** "Whether or not" — in most contexts "whether" alone suffices; "or not" is implicit in "whether" unless the "not" case needs specific emphasis; "constitutes a violation of" buries "violates"; "plaintiff's" — in brief writing, always identify the party by name or role
**Corrections:** "The issue is whether applying the statute to these facts violates the plaintiff's due process rights."
**Source/inspiration:** Garner "The Redbook" on "whether or not"; legal writing clarity principles

### Example 19

**Bad text:** "The contract, which the parties entered into in January, which required monthly payments, which were due on the first of the month, was breached."
**Error types:** Three stacked "which" clauses all modifying "contract" — each interrupts the sentence before a predicate is reached; the actual predicate ("was breached") is 28 words away from the subject; by the time the reader reaches "was breached," the context of what was breached is buried; passive voice adds further distance
**Corrections:** "The parties entered a contract in January requiring monthly payments due on the first. The defendant breached the contract by failing to pay."
**Source/inspiration:** Garner on sentence length; Columbia Law "Clear and Active Legal Writing"

### Example 20

**Bad text:** "The firm represents clients in matters involving disputes related to issues concerning employment law."
**Error types:** Preposition string — "in matters involving disputes related to issues concerning" is five consecutive preposition/participle phrases each adding a layer before reaching the actual subject "employment law"; this is sometimes called a "noun stacking" or "of-of-of" problem; the meaning is simply "employment disputes"
**Corrections:** "The firm represents clients in employment disputes."
**Source/inspiration:** Garner on preposition strings; plain language guidance; legal writing clarity principles

### Example 21

**Bad text:** "It is arguable that the evidence perhaps demonstrates that the defendant may have known about the possible consequences of their alleged actions."
**Error types:** Quintuple hedge: "it is arguable" + "perhaps" + "may have known" + "possible" + "alleged"; all five hedges on a single factual claim destroys any persuasive force; appropriate in an objective memo but catastrophic in advocacy; "their" with singular "defendant" (number agreement, though "they/their" for singular is increasingly accepted)
**Corrections:** For a brief: "The evidence demonstrates that the defendant knew the consequences of the breach. [Cite evidence.]" Use hedges only when truly uncertain about a specific point, not as a general writing style
**Source/inspiration:** BriefCatch on hedging; grammar-test-samples.md Sample 2; Garner on overmodified prose

---

## Source Index

| Category | Primary Sources Consulted                                                                                                                                                                                                                                                                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Email    | LawProse/Garner email clarity; ABA Journal email articles; LSU Law Review "Email and the Threat of Inadvertent Settlement"; MBM Law on inadvertent contracts; Kloian v. Domino's Pizza (Mich. App. 2006); GWU Law on privilege waiver; Fieldfisher privilege guide                                                                                                        |
| Brief    | BriefCatch "Legal Writing Mistakes That Undermine Credibility"; Fordham Law "Fifteen Common Bluebooking Errors"; Georgetown "Some Common and Obscure Bluebook Errors"; Columbia Law "Clear and Active Legal Writing"; Garner "The Winning Brief"; Court opinions (Seventh Circuit, Second Circuit)                                                                        |
| Contract | Ken Adams "A Manual of Style for Contract Drafting" (MSCD, 5th ed.); Adams on Contract Drafting blog; Clinton Assoc. v. Monadnock; Kloian v. Domino's; Georgetown Law Journal on efforts clauses; Adams "Interpreting and Drafting Efforts Provisions" (Texas BLJ 2019); Weagree contract drafting guides; Florida Bar "Fifty Tips for Writing the 21st Century Contract" |
| Plain    | SFBA "Banish These Words and Phrases"; Federal Plain Language Guidelines; Garner "Dictionary of Legal Usage"; Attorney at Work "Whereas" article; Legal Doublet (Wikipedia/WordRake); Garner "The Redbook"; Texas Bar Practice legalese guide                                                                                                                             |
| Grammar  | Marquette Law "Controlling Passive Voice and Nominalizations"; Loyola Law subject-verb agreement + passive voice guides; Legal Writing Editor nominalization piece; Purdue OWL dangling modifiers; RWU Law modifier handout; Columbia Law "Clear and Active Legal Writing"; UT Austin legal writing blog; Garner "Garner's Modern American Usage"                         |

## Error Type Frequency Matrix

| Error Type                                     | Email | Brief | Contract | Plain | Grammar | Total |
| ---------------------------------------------- | ----- | ----- | -------- | ----- | ------- | ----- |
| Throat-clearing / dummy-it                     | 6     | 4     | 2        | 5     | 3       | 20    |
| Legalese / archaic words                       | 7     | 3     | 6        | 12    | 1       | 29    |
| Nominalization / buried verb                   | 2     | 2     | 4        | 6     | 8       | 22    |
| Passive voice                                  | 2     | 4     | 1        | 1     | 4       | 12    |
| Doublets / redundancy                          | 3     | 2     | 7        | 10    | 2       | 24    |
| Modifier errors (dangling/squinting/misplaced) | 0     | 4     | 2        | 0     | 5       | 11    |
| Binding language / privilege risk              | 8     | 0     | 3        | 0     | 0       | 11    |
| Citation errors                                | 0     | 5     | 0        | 0     | 0       | 5     |
| Overconfidence / inappropriate hedging         | 3     | 4     | 1        | 0     | 4       | 12    |
| Subject-verb agreement                         | 0     | 2     | 0        | 0     | 3       | 5     |
| Parallel structure                             | 0     | 2     | 0        | 0     | 3       | 5     |
| Vague standards (reasonable, promptly, etc.)   | 1     | 0     | 8        | 3     | 0       | 12    |
| Modal verb misuse (shall/must/may/will)        | 0     | 1     | 6        | 1     | 1       | 9     |

## Notes for Fine-Tuning Use

1. **Preserve terms of art**: The model should NOT flag "material breach," "good faith," "specific performance," "mens rea," "pro rata," "force majeure," "indemnify," "waiver," "estoppel," or other genuine legal terms of art as errors. These have specific legal meanings that plain-language substitutions would destroy.

2. **Context sensitivity**: Some errors (e.g., passive voice) are appropriate in specific legal contexts. Passive voice is intentional when the actor is unknown or deliberately de-emphasized ("The motion was filed" in a procedural history). Flag passive voice as a suggestion, not an error.

3. **Document type matters**: "Clearly" in a brief is a style error; "clearly" in a demand letter carries different risk. The model should weight errors by document type.

4. **Privilege errors are high-stakes**: Email privilege/binding-language errors have real legal consequences and should be flagged at high severity. These are not mere style issues.

5. **Doublets in terms of art**: Some doublets ARE terms of art: "attorney's fees and costs" (both are recoverable and legally distinct), "search and seizure" (Fourth Amendment term), "cruel and unusual punishment" (Eighth Amendment). Do not flag these.
