#!/usr/bin/env python3
"""
Generate training data batches for legal grammar fine-tuning.

Creates 250+ diverse legal text samples with realistic errors across 10 document
types and 60+ error patterns. Claude Sonnet then reviews each sample, producing
gold-standard grammar corrections for SFT training.

Research basis:
  - Bryan Garner (The Redbook, Elements of Legal Style, LawProse lessons)
  - Ken Adams (A Manual of Style for Contract Drafting)
  - Federal Plain Language Guidelines
  - O'Connor v. Oakhurst Dairy (Oxford comma), Rogers v. Bell Aliant (comma placement)
  - BriefCatch, WordRake, PerfectIt error categories
  - Bluebook citation rules, FRAP formatting standards
  - ABA, state bar, and court-published writing guides
"""

import json
import uuid
import argparse
import random
import sys
from pathlib import Path

# Import research-generated templates
sys.path.insert(0, str(Path(__file__).parent))
try:
    from research_templates import RESEARCH_TEMPLATES
except ImportError:
    RESEARCH_TEMPLATES = []

# ============================================================================
# ERROR INJECTION FUNCTIONS
# Each function takes clean text and injects a specific error pattern
# ============================================================================

def inject_contraction(text):
    """Replace formal language with contractions."""
    replacements = [
        ("do not", "don't"), ("does not", "doesn't"), ("did not", "didn't"),
        ("cannot", "can't"), ("will not", "won't"), ("would not", "wouldn't"),
        ("should not", "shouldn't"), ("is not", "isn't"), ("are not", "aren't"),
        ("has not", "hasn't"), ("have not", "haven't"), ("was not", "wasn't"),
        ("we would", "we'd"), ("we will", "we'll"), ("I will", "I'll"),
        ("it is", "it's"), ("that is", "that's"),
    ]
    r = random.choice(replacements)
    return text.replace(r[0], r[1], 1) if r[0] in text else text

def inject_passive_voice(text):
    """Convert active voice to passive."""
    swaps = [
        ("The court granted", "The motion was granted by the court regarding"),
        ("The defendant filed", "The motion was filed by the defendant"),
        ("Plaintiff alleges", "It is alleged by Plaintiff"),
        ("We reviewed", "The documents were reviewed by us"),
        ("The parties executed", "The agreement was executed by the parties"),
        ("Counsel submitted", "The brief was submitted by counsel"),
        ("The judge denied", "The motion was denied by the judge"),
        ("The witness testified", "Testimony was given by the witness"),
    ]
    for old, new in swaps:
        if old in text:
            return text.replace(old, new, 1)
    return text

def inject_nominalization(text):
    """Replace strong verbs with weak noun phrases."""
    swaps = [
        ("determined", "made a determination"),
        ("decided", "reached a decision"),
        ("concluded", "came to the conclusion"),
        ("considered", "gave consideration to"),
        ("investigated", "conducted an investigation into"),
        ("analyzed", "performed an analysis of"),
        ("violated", "was in violation of"),
        ("complied", "was in compliance with"),
        ("recommended", "made a recommendation"),
        ("agreed", "reached an agreement"),
        ("refused", "made a refusal to"),
        ("contributed", "made a contribution to"),
        ("resolved", "reached a resolution of"),
    ]
    for old, new in swaps:
        if old in text:
            return text.replace(old, new, 1)
    return text


# ============================================================================
# DOCUMENT TEMPLATES — organized by type
# Each has: text, category, error_types (what's wrong), doc_subtype
# ============================================================================

TEMPLATES = []

# ---------------------------------------------------------------------------
# EMAILS (40 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "email",
        "doc_subtype": "client_update",
        "text": """Subject: RE: Morrison v. Springfield Properties — Discovery Update

Hi Jane,

I wanted to give you a quick update on your case. We received the defendant's interrogatory responses last Friday and they weren't great — several answers were incomplete and evasive. We're going to file a motion to compel more detailed responses.

Also, I don't think we should wait much longer to depose their shift supervisor. The court's discovery deadline is coming up fast and we can't afford to miss it. FYI, I talked to opposing counsel yesterday and he said they might agree to an extension but I wouldn't count on it.

One more thing — the expert we discussed, Dr. Williams, is available but she's expensive. Her rate is $450/hour for review and $3,500/day for testimony. Let me know if you want to retain her or if we should look at other options.

I'll keep you posted. Let me know if you have any questions or if you want to set up a call to discuss.

Best,
Mike""",
        "error_types": ["contraction", "informal_language", "missing_oxford_comma", "vague_timeline", "tone_too_casual"],
    },
    {
        "category": "email",
        "doc_subtype": "opposing_counsel",
        "text": """Subject: RE: Discovery Dispute — Chen v. Meridian Corp.

Dear Mr. Patterson,

Your client's discovery responses are totally inadequate and we both know it. The interrogatory answers are nothing but boilerplate objections followed by non-responsive drivel. Frankly, I'm shocked that an attorney of your experience would allow such deficient responses to be served.

We need the following supplemented ASAP:
- Interrogatory Nos. 3, 7, and 12 which your client basically refused to answer
- Request for Production No. 5 which your client claims is "overly broad" even though it asks for documents your client referenced in it's own counterclaim
- The corporate representative deposition which has been rescheduled three times now due to your client's foot-dragging

If we don't receive adequate responses by Friday, we will have no choice but to seek sanctions and attorneys fees. I think Judge Martinez will be very interested to hear about your client's pattern of obstruction.

Regards,
Sarah Mitchell""",
        "error_types": ["tone_unprofessional", "its_vs_its", "informal_language", "threatening_tone", "personal_attack"],
    },
    {
        "category": "email",
        "doc_subtype": "client_advisory",
        "text": """Subject: Update on Settlement Negotiations

Dear Mr. Chen,

Per our conversation this morning, I wanted to memorialize the key points. The other side has made a settlement offer of $175,000, which represents a significant reduction from their initial demand of $350,000.

While this offer is lower than what we originally anticipated, there are several factors we need to consider, including the judge's recent ruling on the motion in limine, the strength of their expert witness and the risk of an adverse jury verdict.

I believe we should counter at $225,000, which splits the difference between our last offer and their's. However, I want to discuss this with you before we respond. We also need to consider the tax implications of any settlement — specifically whether the payment will be characterized as compensatory damages, punitive damages or attorneys fees, as each has different tax treatment.

Please let me know when you're available to discuss. I'd like to respond to opposing counsel by end of week if possible.

Very truly yours,
Patricia Chen""",
        "error_types": ["missing_oxford_comma", "theirs_error", "pursuant_overuse", "privilege_risk"],
    },
    {
        "category": "email",
        "doc_subtype": "scheduling",
        "text": """Subject: Deposition Schedule Change — Rodriguez Matter

Dear Counsel,

Per our conversation this morning, I am writing to confirm that the deposition of Dr. Martinez has been rescheduled to March 15th at 10:00am. Please note that the location has also been changed to our offices at 500 Main Street, Suite 200.

We will be providing the witness with the following exhibits: Exhibit A (the employment agreement), Exhibit B (the performance reviews) and Exhibit C (the termination letter). Please advise if your client has any objections to this arrangment and we will try to accomodate them.

Additionally, please be advised that we intend to take the deposition of your client's supervisor on March 22nd. A formal notice of deposition will follow but I wanted to give you advance notice so you can make the neccessary arrangements.

Regards,
Patricia Chen""",
        "error_types": ["spelling_error", "missing_oxford_comma", "tone_inconsistency"],
    },
    {
        "category": "email",
        "doc_subtype": "internal",
        "text": """Subject: Quick question about the Harrison matter

Hey Tom,

Can you take a look at the summary judgment brief when you get a chance? I think the argument re: estoppel needs work — it's a little wishy-washy and I'm not sure the cases we cited really support our position. Also, the section on damages is way too long and I think we should probably cut it down.

Sarah reviewed it yesterday and she thought the statement of facts was good but said the legal standard section could be stronger. She suggested we add the Twombly/Iqbal framework even though it's technically a 12(b)(6) standard, not SJ. I wasn't sure about that — what do you think?

Oh and don't forget we need to file by Thursday. The court's ECF system closes at midnight but lets not cut it that close again lol.

Thx,
James""",
        "error_types": ["contraction", "informal_language", "abbreviation_unclear", "missing_apostrophe", "tone_too_casual", "hedging"],
    },
    {
        "category": "email",
        "doc_subtype": "meet_and_confer",
        "text": """Subject: Deficient Discovery Responses — Williams v. Apex Corp.

Dear Ms. Rodriguez,

Your client's responses to our First Set of Interrogatories are deficient. Supplement them immediately or we will file a motion to compel.

Specifically, Interrogatory No. 4 asked for the names of all employees who witnessed the incident, and your client responded with a blanket objection that the request was "overly broad, unduly burdensome, and not reasonably calculated to lead to the discovery of admissible evidence." This boilerplate objection is insufficient under Rule 33.

We expect supplemental responses within 10 days. Govern yourself accordingly.

Regards,
James Mitchell""",
        "error_types": ["tone_aggressive", "govern_yourself", "missing_good_faith_effort", "no_proposed_resolution"],
    },
    {
        "category": "email",
        "doc_subtype": "engagement",
        "text": """Subject: Engagement Confirmation — Employment Matter

Dear Ms. Rodriguez,

Thank you for meeting with us yesterday. This email confirms that our firm will represent you in connection with your employment discrimination claim against Meridian Corporation.

Our hourly rates are: Partners $450/hour, Associates $275/hour, Paralegals $150/hour. We will require an initial retainer of $10,000 which will be applied against fees as they are incurred.

We will keep you informed of all significant developments and will not take any major action without your approval. Please don't hesitate to reach out if you have questions.

We look forward to working with you.

Best regards,
Carter & Associates""",
        "error_types": ["contraction", "missing_scope_limitation", "missing_no_guarantee", "vague_retainer_terms"],
    },
    {
        "category": "email",
        "doc_subtype": "settlement_offer",
        "text": """Subject: Settlement Proposal — Morrison v. Springfield

Dear Counsel,

After careful consideration, our client is prepared to offer $125,000 in full and final settlement of all claims asserted in the above-referenced matter. This offer is contingent upon execution of a mutual release and confidentiality agreement.

We believe this offer is fair and reasonable given the strengths and weaknesses of both side's positions. The offer will remain open for 14 days from the date of this email.

We agree that this represents a reasonable resolution and look forward to finalizing the terms.

Please let me know if your client is interested in discussing this further.

Regards,
Robert Kim""",
        "error_types": ["sides_possessive_error", "binding_commitment_risk", "missing_without_prejudice", "missing_subject_to_contract"],
    },
])

# ---------------------------------------------------------------------------
# BRIEFS (40 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "brief",
        "doc_subtype": "summary_judgment",
        "text": """ARGUMENT

I. The Court Should Grant Summary Judgment Because Plaintiff Cannot Establish The Elements Of Their Claim.

The evidence in the record clearly demonstrates that the Defendant did not breach the contract as alleged. The data collected during discovery shows that Defendant's performance, which was in substantial compliance with the terms of the Agreement that was executed on January 15, 2024, met or exceeded all benchmarks established by the parties.

Plaintiffs damages, which includes lost profits, consequential damages, and costs of mitigation, was not adequately supported by the evidence. The plaintiff's expert, Dr. Williams, provided testimony that was based on speculative assumptions and methodologies that has been rejected by courts in this jurisdiction. See Smith v. Jones, 456 F.3d 789 (8th Cir. 2022); Johnson v. Corp., Inc., 123 F. Supp. 2d 456 (D. Minn. 2021).

Furthermore, the undisputed facts demonstrate that the plaintiff failed to mitigate their damages. Despite being aware of the alleged breach for over six months, the Plaintiff took no steps to find alternative suppliers, reduce their losses, or had even attempted to invoke the cure provisions in the Agreement. This failure to mitigate bars recovery of consequential damages as a matter of law. Id. at 463-64.""",
        "error_types": ["subject_verb_agreement", "possessive_error", "parallel_structure", "passive_voice", "sentence_length", "hedging", "all_caps_heading"],
    },
    {
        "category": "brief",
        "doc_subtype": "motion_to_dismiss",
        "text": """II. Defendants Motion to Dismiss Should Be Denied Because the Complaint States a Plausible Claim.

Under the standard set forth in Bell Atlantic Corp. v. Twombly, 550 U.S. 544 (2007) and Ashcroft v. Iqbal, 556 U.S. 662 (2009), a complaint must contain sufficient factual matter, accepted as true, to state a claim for relief that is plausible on it's face. The court must draw all reasonable inferences in favor of the non-moving party. Reviewing the complaint as a whole, which sets forth detailed allegations of fraud, breach of fiduciary duty, and unjust enrichment against each of the individual defendants by name, the plaintiff has clearly met this threshold.

The defendant argues that the complaint is "conclusory" but this characterization ignores the fact that the complaint contains over 50 paragraphs of factual allegations, identifies specific transactions, and names specific individuals who participated in the alleged scheme. This level of detail goes well beyond the requirements of notice pleading and arguably surpasses even the heightened pleading standard applicable to fraud claims under Fed. R. Civ. P. 9(b).""",
        "error_types": ["possessive_error", "its_vs_its", "hedging", "missing_comma_before_conjunction", "sentence_length"],
    },
    {
        "category": "brief",
        "doc_subtype": "motion_in_limine",
        "text": """DEFENDANT'S MOTION IN LIMINE TO EXCLUDE SUBSEQUENT REMEDIAL MEASURES

Defendant respectfully moves this Court for an order precluding Plaintiff from introducing any evidence, testimony, or argument regarding changes made to Defendant's safety protocols subsequent to the incident that is the subject of this litigation.

Federal Rule of Evidence 407 provides that evidence of measures taken after an injury or harm that, if taken previously, would have made the injury or harm less likely to occur is not admissible to prove negligence, culpable conduct, a defect in a product, a defect in a product's design, or a need for a warning or instruction. The rationale behind this rule is well-established: admitting such evidence would discourage parties from taking steps to improve safety, the rule serves important policy goals that this Court should enforce.

In this case, Plaintiff has indicated its intention to introduce evidence that Defendant installed additional safety barriers and warning signage in the weeks following the incident. This evidence is precisely the type of subsequent remedial measure that Rule 407 was designed to exclude. While Plaintiff may argue that the evidence is admissible for another purpose, such as proving ownership, control, or feasibility, the probative value of such evidence is substantially outweighed by the danger of unfair prejudice under Rule 403. The jury would inevitably use this evidence to infer that Defendant's pre-incident safety measures were inadequate, which is exactly the inference Rule 407 prohibits.""",
        "error_types": ["comma_splice", "sentence_length", "parallel_structure"],
    },
    {
        "category": "brief",
        "doc_subtype": "appellate",
        "text": """STATEMENT OF THE CASE

The Appellant, John Morrison, was convicted of second-degree assault following a jury trial in the Circuit Court of Cook County. Prior to trial, Appellant moved to suppress statements he made to law enforcement officers on the grounds that he was not properly advised of his Miranda rights prior to questioning. The trial court denied the motion, finding that the officers' testimony was credible and that Appellant had been adequately Mirandized.

At trial, the prosecution introduced the challenged statements, which included admissions that Appellant was present at the scene and that he had a prior altercation with the complainant. The defense objected and moved for a mistrial, arguing that the statements were obtained in violation of Appellant's Fifth Amendment rights, that they were involuntary, and the admission was prejudicial. The trial court overruled the objection.

The jury returned a verdict of guilty on March 15, 2025. Appellant was sentenced to 36 months imprisonment. This appeal followed.

ARGUMENT

I. The Trial Court Erred In Denying The Motion To Suppress Because The Officers Failed To Provide A Complete Miranda Warning Prior To Custodial Interrogation.

The constitutional protection against compelled self-incrimination requires that prior to any custodial interrogation, law enforcement officers must clearly inform a suspect of their right to remain silent, that any statement they make may be used against them, and of their right to an attorney. Miranda v. Arizona, 384 U.S. 436, 444 (1966). These warnings must be delivered in their entirety; a partial or incomplete warning is constitutionally insufficient. See Berghuis v. Thompkins, 560 U.S. 370, 380 (2010).""",
        "error_types": ["parallel_structure", "tense_inconsistency", "passive_voice", "prior_to_usage"],
    },
    {
        "category": "brief",
        "doc_subtype": "opposition",
        "text": """PLAINTIFF'S OPPOSITION TO DEFENDANT'S MOTION FOR SUMMARY JUDGMENT

I. Material Disputes Of Fact Preclude Summary Judgment.

Defendant's motion should be denied because genuine disputes of material fact exist as to every element of Plaintiff's claims. Defendant cherry-picks favorable testimony while ignoring the substantial body of evidence that supports Plaintiff's case.

With respect to the question of notice, Defendant asserts that it had no knowledge of the dangerous condition. This assertion is flatly contradicted by the testimony of three witnesses who observed maintenance personnel inspecting the area just days before the incident. See Morrison Dep. 45:3-12; Harris Dep. 22:14-24:9; Santos Dep. 31:7-15. Defendant's own incident reports, which was produced in discovery, contain entries documenting prior complaints about the same condition. See Exh. D, Bates Nos. DEF000145-DEF000162.

Due to the fact that Defendant cannot establish the absence of a genuine dispute on the issue of notice, it's motion must be denied. The credibility of witnesses and the weight of the evidence are quintessentially matters for the jury, not for resolution on summary judgment. Anderson v. Liberty Lobby, Inc., 477 U.S. 242, 255 (1986).""",
        "error_types": ["subject_verb_agreement", "its_vs_its", "wordy_phrase", "with_respect_to", "cherry_picks_informal"],
    },
    {
        "category": "brief",
        "doc_subtype": "sentencing_memo",
        "text": """DEFENDANT'S SENTENCING MEMORANDUM

I. Background and Personal History

Mr. Rodriguez is a 34-year-old father of two young children who has been a productive member of his community for his entire adult life. Prior to this conviction, he had no criminal history whatsoever. He has been employed continuously since graduating from high school, most recently as a warehouse supervisor at Pacific Logistics where he has worked for the past seven years. His supervisor, Robert Chen, describes him as "one of the most reliable and hardworking employees I have ever had the pleasure of managing." See Ex. A.

Mr. Rodriguez's actions on the night in question were completely out of character and were the result of circumstances that, while they do not excuse his conduct, help explain it. His mother had recently been diagnosed with terminal cancer, and he was struggling to cope with the emotional and financial burden of her care while supporting his own family. He had began drinking heavily for the first time in his life, which lead to the poor judgment that resulted in this offense.

II. The Advisory Guidelines Range Overstates the Seriousness of the Offense.

The Presentence Investigation Report calculates an advisory Guidelines range of 37 to 46 months. However, this calculation does not adequately account for the unique circumstances of this case. The defendant respectfully submits that a sentence of probation with conditions, including alcohol treatment and community service, would be sufficient but not greater than necessary to comply with the purposes of sentencing set forth in 18 U.S.C. § 3553(a).""",
        "error_types": ["began_vs_begun", "lead_vs_led", "tense_inconsistency", "sentence_length"],
    },
    {
        "category": "brief",
        "doc_subtype": "reply_brief",
        "text": """DEFENDANT'S REPLY IN SUPPORT OF MOTION TO DISMISS

Plaintiff's Opposition confirms what was evident from the Complaint itself: Plaintiff cannot state a plausible claim for relief.

Rather than addressing the fundamental deficiency identified in Defendant's Motion — namely, that the Complaint fails to allege any facts supporting scienter — Plaintiff devotes the majority of their Opposition to a recitation of legal standards and conclusory assertions that the Complaint "speaks for itself." But it does not. A complaint must do more than recite elements; it must plead facts that, taken as true, state a claim that is plausible on its face. Iqbal, 556 U.S. at 678.

Plaintiff argues that "the temporal proximity between Defendant's stock sales and the earnings announcement creates a strong inference of scienter." Opp. at 12. This is simply wrong. Temporal proximity alone, without more, has never been held sufficient to establish the heightened scienter requirement of the PSLRA. See Tellabs, Inc. v. Makor Issues & Rights, Ltd., 127 S. Ct. 2499, 2504-05 (2007). Not only must the inference of scienter be reasonable, it must be "cogent and at least as compelling as any opposing inference one could draw from the facts alleged." Id at 2510.

Plaintiffs remaining arguments fair no better. The assertion that Defendant had access to "material nonpublic information" is based entirely on the unremarkable fact that Defendant was a corporate officer — a fact that, standing alone, is insufficient to plead scienter in any circuit.""",
        "error_types": ["fair_vs_fare", "missing_period_in_id", "pronoun_number_inconsistency", "sct_citation_format"],
    },
])

# ---------------------------------------------------------------------------
# CONTRACT CLAUSES (40 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "contract",
        "doc_subtype": "indemnification",
        "text": """8.1 Indemnification. The Vendor shall indemnify, defend and hold harmless the Client, its officers, directors, employees and agents (collectively, the "Indemnified Parties") from and against any and all claims, losses, damages, liabilities, costs and expenses (including reasonable attorney's fees) arising from or related to: (a) any breach of this agreement by Vendor; (b) any negligent or willful misconduct of Vendor and/or its employees, agents or subcontractors; (c) any violation of applicable laws, rules or regulations by Vendor; and (d) any infringement or misappropriation of third-party intellectual property rights.

8.2 Notice. The Client shall promptly notify the Vendor of any claim for which indemnification is sought. Failure to provide timely notice shall not relieve the vendor of its indemnification obligations except to the extent that Vendor is materially prejudiced by such failure.

8.3 Limitation of Liability. IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, INCLUDING LOST PROFITS. THE TOTAL AGGREGATE LIABILITY OF EITHER PARTY UNDER THIS AGREEMENT SHALL NOT EXCEED THE FEES PAID BY CLIENT TO VENDOR IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM. The foregoing limitations shall not apply to Vendor's indemnification obligations under Section 8.1.""",
        "error_types": ["and_or_usage", "defined_term_inconsistency", "missing_oxford_comma", "cap_conflict_with_indemnity", "attorneys_fees_apostrophe"],
    },
    {
        "category": "contract",
        "doc_subtype": "confidentiality",
        "text": """5.1 Confidentiality. Each party (the "Receiving Party") agrees to hold in confidence all Confidential Information disclosed by the other party (the "disclosing party") and to use such Confidential Information only for the purposes contemplated by this Agreement. The receiving party shall protect the Confidential Information with the same degree of care it uses to protect its own confidential information, but in no event less than reasonable care.

5.2 Exclusions. Confidential Information does not include information that: (a) is or becomes publicly available through no fault of the receiving party; (b) was known to the Receiving Party prior to disclosure; (c) is independently developed by the receiving Party without use of or reference to the Confidential Information; or (d) is rightfully received from a third party without restriction.

5.3 Required Disclosure. If the Receiving Party is required by law, regulation, or court order to disclose Confidential Information, it shall provide the Disclosing Party with prompt notice of such requirement so that the disclosing party may seek a protective order. The Receiving Party shall disclose only that portion of the confidential information that is legally required to be disclosed.""",
        "error_types": ["defined_term_inconsistency", "capitalization_inconsistency"],
    },
    {
        "category": "contract",
        "doc_subtype": "force_majeure",
        "text": """12.1 Force Majeure. Neither party shall be liable for any failure or delay in performing its obligations under this Agreement if such failure or delay results from circumstances beyond the reasonable control of that party, including but not limited to acts of God, war, terrorism, civil unrest, labor disputes, fire, flood, earthquake, or governmental action.

The party claiming force majeure shall notify the other party of the event as soon as practicable and shall use reasonable efforts to mitigate the impact of the event. If the force majeure event continues for a period exceeding ninety (90) days, either party may terminate this Agreement upon thirty (30) days written notice to the other party.

During a force majeure event, the affected party's obligations under this Agreement shall be suspended, provided however that the party's payment obligations shall not be suspended unless the force majeure event directly prevents such payment.""",
        "error_types": ["missing_without_limitation", "vague_timeframe", "provided_however", "missing_pandemic_cyber", "shall_for_condition"],
    },
    {
        "category": "contract",
        "doc_subtype": "termination",
        "text": """10.1 Term. This Agreement shall continue in force for a period of three (3) years from the Effective Date, and thereafter for successive one (1) year terms, unless and until terminated by either party upon not less than ninety (90) days prior written notice.

10.2 Termination for Cause. Either party may terminate this Agreement immediately upon written notice if the other party: (a) materially breaches this Agreement and fails to cure such breach within thirty (30) days after written notice; (b) becomes insolvent, files for bankruptcy, or makes an assignment for the benefit of creditors; or (c) is subject to a change of control.

10.3 Effect of Termination. Upon termination of this Agreement for any reason, each party shall promptly return or destroy all Confidential Information of the other party and shall certify in writing that such return or destruction has been completed. The following provisions shall survive termination: Sections 5 (Confidentiality), 8 (Indemnification), and 14 (Governing Law).

10.4 Transition Services. For a period of sixty (60) days following termination (the "Transition Period"), Vendor will continue to provide the Services at the rates set forth in Exhibit A. Client shall pay for such services within 30 days of invoice.""",
        "error_types": ["comma_ambiguity", "shall_vs_will_inconsistency", "missing_survival_provisions", "change_of_control_undefined"],
    },
    {
        "category": "contract",
        "doc_subtype": "best_efforts",
        "text": """3.1 Performance Standard. The Vendor shall use best efforts to deliver the Deliverables in accordance with the timeline set forth in Exhibit B. In the event that Vendor anticipates a delay in delivery, Vendor shall promptly notify Client and shall use reasonable efforts to minimize the impact of such delay.

3.2 Acceptance. Client shall have fifteen (15) business days following delivery to inspect and test the Deliverables. In the event that the Deliverables do not conform to the specifications set forth in Exhibit A, Client shall notify Vendor in writing, and Vendor shall use commercially reasonable efforts to correct any nonconformities within ten (10) business days.

3.3 Warranty. Vendor represents and warrants that the Deliverables will conform to the specifications set forth in Exhibit A, will be free from material defects, and will not infringe any third-party intellectual property rights. Vendor further warrants that all services will be performed in a professional and workmanlike manner consistent with industry standards.""",
        "error_types": ["inconsistent_efforts_standard", "in_the_event_that", "represents_and_warrants_undifferentiated", "shall_for_future"],
    },
    {
        "category": "contract",
        "doc_subtype": "assignment",
        "text": """15.1 Assignment. Neither party may assign this Agreement or any of its rights or obligations hereunder without the prior written consent of the other party, which consent shall not be unreasonably withheld. Any attempted assignment in violation of this Section shall be null and void.

15.2 Subcontracting. Vendor may subcontract any of its obligations under this Agreement to qualified third parties, provided that Vendor shall remain fully responsible for the performance of any subcontractor. Vendor shall ensure that each subcontractor is bound by confidentiality obligations no less restrictive than those set forth in Section 5.

15.3 Binding Effect. This Agreement shall be binding upon and inure to the benefit of the parties hereto and their respective successors and permitted assigns.""",
        "error_types": ["missing_affiliate_carveout", "missing_operation_of_law", "archaic_hereto", "null_and_void_doublet"],
    },
    {
        "category": "contract",
        "doc_subtype": "ambiguous_scope",
        "text": """2.1 Scope of Services. The Vendor shall provide consulting services to the Client in connection with the Client's enterprise resource planning implementation project (the "Project"). The scope of the Services includes system design, configuration, testing and deployment of the ERP System, including training for Client's personnel.

2.2 Change Orders. Any changes to the scope of Services described in this Agreement and/or the applicable Statement of Work must be documented in a written change order signed by authorized representatives of both parties. The Vendor shall not perform any work outside the scope of this Agreement without a duly executed change order.

2.3 Client Responsibilities. Client shall provide Vendor with reasonable access to Client's facilities, systems, and personnel as reasonably necessary for Vendor to perform the Services. Client shall designate a project manager who will serve as the primary point of contact for all communications related to the Project. The Client's project manager shall have the authority to make decisions on behalf of Client with respect to the Services, provided that such decisions do not materially alter the scope, timeline, or budget of the Project.""",
        "error_types": ["and_or_usage", "missing_oxford_comma", "vague_authority", "with_respect_to"],
    },
    {
        "category": "contract",
        "doc_subtype": "data_protection",
        "text": """7.1 Data Protection. The Vendor shall implement and maintain appropriate technical and organizational measures to protect Client Data against unauthorized access, use, disclosure, alteration, or destruction. Such measures shall be no less protective than industry-standard practices for the type of data being processed.

7.2 Data Breach Notification. In the event of a Security Incident involving Client Data, Vendor shall notify Client within seventy-two (72) hours of becoming aware of the incident. The notification shall include: (a) a description of the nature of the Security Incident; (b) the categories and approximate number of data subjects affected; (c) the likely consequences of the incident; and (d) measures taken or proposed to address the incident.

7.3 Data Processing. The vendor agrees that it will process Client Data only in accordance with Client's documented instructions and applicable data protection laws. Vendor shall not transfer Client data to any third party or to any country outside the United States without Client's prior written consent. Upon termination of this agreement, Vendor shall, at Client's election, return or securely destroy all client data in its possession within thirty (30) days.""",
        "error_types": ["defined_term_inconsistency", "shall_vs_will", "capitalization_inconsistency", "security_incident_undefined"],
    },
])

# ---------------------------------------------------------------------------
# MEMOS (30 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "memo",
        "doc_subtype": "internal_analysis",
        "text": """MEMORANDUM

TO: Partner Smith
FROM: Associate Rodriguez
RE: Wrongful Termination Analysis — Martinez Matter

QUESTION PRESENTED

Whether the employer will be liable for wrongful termination in violation of public policy where the employee was terminated fourteen days after filing a workers' compensation claim, and the employer asserts that the termination was based on pre-existing performance issues.

SHORT ANSWER

Probably yes. The temporal proximity between the filing of the workers' compensation claim and the subsequent termination gives rise to a strong inference of retaliatory intent. While the employer's asserted justification provides a facially legitimate reason, the circumstantial evidence undermines its credibility.

DISCUSSION

To the extent that the employee filed a workers' compensation claim, the employer made the determination to terminate her employment. The termination was effectuated approximately fourteen days after the claim was filed by Ms. Martinez. Under the applicable statute, employers shall not retaliate against employees who exercises their right to file workers' compensation claims.

The Company argues that the decision to terminate Rodriguez was based on poor performance evaluations that were conducted prior to the filing of the claim by the employee. However, this argument is undermined by several factors. First, the temporal proximity between the filing and the termination — only fourteen days — creates a presumption of retaliatory intent. Second, the employer has failed to produce any contemporaneous documentation of the performance issues. Third, a replacement for Ms. Martinez was hired within two weeks, suggesting the position was not eliminated for legitimate reasons.""",
        "error_types": ["to_the_extent_misuse", "nominalization", "passive_voice", "shall_in_memo", "subject_verb_agreement", "inconsistent_party_reference", "prior_to_usage"],
    },
    {
        "category": "memo",
        "doc_subtype": "research_memo",
        "text": """MEMORANDUM

TO: Sarah Mitchell, Partner
FROM: David Park, Associate
DATE: March 10, 2026
RE: Enforceability of Non-Competition Agreement — Harrison Matter

QUESTION PRESENTED

Under Illinois law, whether a non-competition agreement executed by a mid-level sales manager is enforceable where the agreement restricts all competitive activity within a 200-mile radius for a period of three years, and where the employee received no additional consideration beyond continued employment.

SHORT ANSWER

Probably not. Illinois courts apply a three-part test for enforceability of restrictive covenants: (1) whether the restriction is necessary to protect a legitimate business interest; (2) whether the restriction is reasonable in time, territory, and scope; and (3) whether adequate consideration supports the agreement. The 200-mile geographic restriction and three-year duration will likely be found unreasonable for a mid-level employee, and continued employment alone may not constitute adequate consideration under recent Illinois precedent.

DISCUSSION

I. The Geographic and Temporal Restrictions Are Likely Unreasonable.

Illinois courts have consistently held that the reasonableness of a non-compete must be evaluated in light of the employee's position and access to confidential information. See Reliable Fire Equipment Co. v. Arredondo, 2011 IL 111871. A 200-mile restriction effectively prohibits Mr. Harrison from working in his industry anywhere in the greater Chicago metropolitan area and surrounding states. For a mid-level sales manager whose territory covered only the northern suburbs, this restriction is arguably overbroad.

Courts in this jurisdiction have upheld geographic restrictions of 50-75 miles for similar positions. See, e.g., Arcor, Inc. v. Haas, 842 N.E.2d 265, 274 (Ill. App. 1st Dist. 2005). A three-year duration also exceeds the one-to-two year range that courts typically find reasonable for employees at this level. Id at 276.

II. Continued Employment May Not Constitute Adequate Consideration.

This issue has evolved significantly in recent years. In Fifield v. Premier Dealer Services, Inc., the Illinois Appellate Court held that continued employment for less then two years does not constitute adequate consideration for a restrictive covenant. 2013 IL App (1st) 120327. Mr. Harrison signed the non-compete upon promotion to sales manager and was terminated approximately eighteen months later, falling below the Fifield threshold.""",
        "error_types": ["missing_period_in_id", "then_vs_than", "hedging", "sentence_length", "passive_voice"],
    },
    {
        "category": "memo",
        "doc_subtype": "due_diligence",
        "text": """MEMORANDUM

TO: Transaction Team
FROM: Corporate Due Diligence Group
DATE: March 8, 2026
RE: Due Diligence Findings — Target Corp. Acquisition

SUMMARY OF KEY FINDINGS

1. Material Contracts. Target Corp. has 47 material contracts, of which 12 contain change-of-control provisions that could be triggered by the proposed acquisition. The most significant are: the Master Supply Agreement with Pacific Manufacturing (representing 35% of revenue), the exclusive distribution agreement with Continental Brands, and the technology license agreement with Innovate Labs. Each of these agreements requires the counter-party's consent to assignment, and in the case of the Pacific Manufacturing agreement, consent may be withheld in the counter-party's sole discretion.

2. Litigation. Target is currently a defendant in three pending lawsuits. The most significant is Rodriguez v. Target Corp., a class action employment discrimination suit with a putative class of approximately 500 current and former employees. Target's outside counsel estimates the potential exposure at between $5 million and $15 million, however this estimate was prepared prior to the certification of the class and may not reflect current risk.

3. Intellectual Property. Target owns 23 registered patents, 45 registered trademarks, and 12 registered copyrights. Our review identified three potential issues: (a) two patents that may be subject to prior art challenges; (b) a trademark opposition proceeding filed by a competitor that remains pending, and (c) an open source software licensing issue in Target's primary software product that could effect Target's ability to distribute the product commercially.

4. Environmental. Phase I environmental assessments were conducted at all four of Targets manufacturing facilities. Two facilities showed evidence of historical contamination that may require further investigation. Target's management represents that all known environmental liabilities have been disclosed, but we recommend conducting Phase II assessments at the two flagged facilities prior to closing.""",
        "error_types": ["counterparty_hyphenation", "comma_splice", "effect_vs_affect", "possessive_error", "prior_to_usage", "missing_oxford_comma"],
    },
])

# ---------------------------------------------------------------------------
# DEMAND LETTERS (20 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "letter",
        "doc_subtype": "demand",
        "text": """March 5, 2026

VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED

Mr. Robert Chen, Esq.
Chen & Associates, LLC
1200 Commerce Drive, Suite 400
Chicago, IL 60601

Re: Demand for Payment — Invoice Nos. 2024-1055, 2024-1089, and 2024-1102

Dear Mr. Chen:

We represent ABC Technologies, Inc. ("our client") in connection with the outstanding invoices referenced above. Despite multiple requests for payment, your client, XYZ Solutions, LLC, has failed to remit payment totalling $187,450.00 for services rendered between June and September 2024.

As you know, the Master Services Agreement executed between the parties on March 1, 2023 (the "MSA") provides that all invoices are due and payable within thirty (30) days of receipt. The above-referenced invoices were submitted on June 15, July 20, and August 30, 2024 respectively. None of these invoices have been paid, and each is now more than 150 days overdue.

Section 12.3 of the MSA provides that in the event of non-payment, the non-breaching party shall be entitled to recover all costs of collection, including reasonable attorneys fees and interest at the rate of 1.5% per month. As of today's date, the accrued interest totals approximately $28,117.50, bringing the total amount due to $215,567.50.

We hereby demand that your client remit payment of the full outstanding balance, including accrued interest, within ten (10) business days of receipt of this letter. If payment is not received by March 19, 2026, our client will have no choice but to pursue all available legal remedies, including the commencement of litigation in the Circuit Court of Cook County.

We trust this matter can be resolved without the need for litigation. Please contact the undersigned at your earliest convenience to discuss.

Very truly yours,

Sarah Mitchell, Esq.
Mitchell & Partners, LLP""",
        "error_types": ["spelling_totalling", "missing_apostrophe_attorneys", "missing_comma_after_date", "due_and_payable_doublet", "in_the_event_of", "nominalization_commencement"],
    },
    {
        "category": "letter",
        "doc_subtype": "cease_and_desist",
        "text": """March 8, 2026

VIA CERTIFIED MAIL AND EMAIL

Ms. Jennifer Walsh
BrightField Solutions, LLC
8900 Technology Parkway
Austin, TX 78701

Re: Unauthorized Use of BRIGHTFIELD Trademark — Demand to Cease and Desist

Dear Ms. Walsh:

We represent Brightfield Technologies, Inc. ("Brightfield"), the owner of U.S. Trademark Registration No. 5,892,341 for the mark BRIGHTFIELD, registered in International Class 42 for software development services. It has come to our attention that your company, BrightField Solutions, LLC, is using the designation "BrightField Solutions" in connection with substantially similar software consulting services.

Your unauthorized use of a confusingly similar mark constitutes trademark infringement under Section 43(a) of the Lanham Act, 15 U.S.C. § 1125(a), and unfair competition under Texas common law. Brightfield has used the BRIGHTFIELD mark continuously since 2018 and has invested substantial resources in developing and promoting it's brand identity.

We hereby demand that you immediately: (1) cease and desist from any and all use of "BrightField Solutions" or any confusingly similar variation; (2) remove all references to "BrightField Solutions" from your website, social media, marketing materials and business documents; (3) provide a written accounting of all revenues generated under the infringing mark; and (4) provide written confirmation of your compliance within ten (10) business days.

This letter is written without prejudice to any rights or remedies available to our client, all of which are expressly reserved. If we do not receive a satisfactory response within the timeframe specified above, Brightfield will not hesitate to pursue all available legal remedies, including seeking injunctive relief and damages.

Govern yourself accordingly.

Very truly yours,

James Morrison, Esq.
Morrison IP Law Group""",
        "error_types": ["its_vs_its", "missing_oxford_comma", "govern_yourself", "cease_and_desist_doublet"],
    },
    {
        "category": "letter",
        "doc_subtype": "demand_personal_injury",
        "text": """March 10, 2026

VIA CERTIFIED MAIL

Claims Department
Springfield Properties, Inc.
2200 Corporate Boulevard
Springfield, IL 62704

Re: Claim of Jane Morrison — Slip and Fall Incident of November 12, 2025

Dear Sir or Madam:

This firm represents Jane Morrison in connection with injuries she sustained on November 12, 2025, at your commercial premises located at 4500 Elm Street, Springfield, Illinois.

On the date in question, Ms. Morrison entered the main lobby of your building at approximately 9:15 a.m. The floor was wet due to a water leak that had been reported to your maintenance staff earlier that morning. Despite being aware of this hazardous condition, your employees failed to place warning signs or barriers, failed to clean up the water, and failed to redirect foot traffic away from the affected area. As a direct and proximate result of your negligence, Ms. Morrison slipped and fell, sustaining the following injuries:

- Fractured left wrist requiring surgical repair
- Lumbar spine contusions requiring 12 weeks of physical therapy
- Persistent left wrist pain and reduced range of motion

Ms. Morrison has incurred $32,000 in medical expenses to date, with an estimated $8,000 in future treatment costs. She missed six weeks of work, resulting in $15,000 in lost wages. She continues to experience pain and limitation that effects her daily activities and quality of life.

Based on the foregoing, we hereby demand compensation in the amount of $125,000. This demand remains open for thirty (30) days from the date of this letter. In the event that we do not receive a substantive response within that timeframe, we will file suit in the Circuit Court of Sangamon County.

Very truly yours,

Michael Torres, Esq.
Torres & Associates""",
        "error_types": ["effect_vs_affect", "in_the_event_that", "passive_construction"],
    },
])

# ---------------------------------------------------------------------------
# DISCOVERY RESPONSES (15 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "discovery",
        "doc_subtype": "interrogatory_answers",
        "text": """DEFENDANT'S ANSWERS AND OBJECTIONS TO
PLAINTIFF'S FIRST SET OF INTERROGATORIES

Defendant Springfield Properties, Inc. ("Defendant"), by and through its undersigned counsel, hereby responds to Plaintiff's First Set of Interrogatories as follows:

GENERAL OBJECTIONS

Defendant objects to each and every Interrogatory to the extent it seeks information protected by the attorney-client privilege, work product doctrine, or any other applicable privilege or immunity. Defendant further objects to each Interrogatory to the extent it is overly broad, unduly burdensome, or seeks information that is not relevant to any party's claim or defense and not proportional to the needs of the case.

INTERROGATORY NO. 1: State the full name, job title, and employment dates of every person who was employed as a maintenance worker, custodian, or facilities manager at the premises located at 4500 Elm Street, Springfield, Illinois, at any time between January 1, 2024 and the present.

ANSWER: Defendant objects to this Interrogatory as overly broad and unduly burdensome in that it seeks information about all maintenance personnel over an unreasonably long time period. Subject to and without waiving the foregoing objections, Defendant identifies the following individuals who were employed in maintenance or custodial roles at the subject premises between January 2025 and the present: John Harris (Shift Supervisor, June 2019-present); Maria Santos (Custodian, March 2024-present); Robert Kim (Building Engineer, January 2023-present); Lisa Park (Custodian, September 2025-present).

INTERROGATORY NO. 5: Identify all persons who witnessed or were present during the incident described in the Complaint.

ANSWER: Defendant objects to this Interrogatory as overly broad and vague as to the meaning of "present during the incident." Subject to and without waiving the foregoing objections, Defendant states that John Harris, Maria Santos, and Robert Kim were in the building at the time of the alleged incident, however, Defendant is not aware of any individuals who directly witnessed Plaintiff's alleged fall.""",
        "error_types": ["each_and_every_doublet", "boilerplate_objections", "comma_splice", "by_and_through_legalese"],
    },
])

# ---------------------------------------------------------------------------
# SETTLEMENT AGREEMENTS (15 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "contract",
        "doc_subtype": "settlement",
        "text": """SETTLEMENT AGREEMENT AND MUTUAL RELEASE

This Settlement Agreement and Mutual Release (this "Agreement") is entered into as of March 10, 2026 (the "Effective Date"), by and between Jane Morrison ("Plaintiff") and Springfield Properties, Inc. ("Defendant") (collectively, the "Parties" and each, a "Party").

RECITALS

WHEREAS, Plaintiff filed a civil action against Defendant in the Circuit Court of Sangamon County, Illinois, Case No. 2025-L-04521 (the "Action"), alleging claims for negligence and premises liability; and

WHEREAS, the Parties desire to settle and resolve all disputes between them arising from or relating to the Action, without any admission of liability;

NOW, THEREFORE, in consideration of the mutual covenants herein and for other good and valuable consideration, the receipt and sufficiency of which is hereby acknowledged, the Parties agree as follows:

1. Settlement Payment. Defendant shall pay to Plaintiff the sum of one hundred twenty-five thousand dollars ($125,000.00) (the "Settlement Amount") within thirty (30) days of the Effective Date. Payment shall be made by wire transfer to an account designated by Plaintiff's counsel.

2. Release. Upon receipt of the Settlement Amount, Plaintiff, on behalf of herself, her heirs, executors, administrators, successors and assigns, hereby releases and forever discharges Defendant, its officers, directors, employees, agents, insurers, successors and assigns from any and all claims, demands, actions, causes of action, suits, debts, obligations, damages, losses, costs, expenses and liabilities of every kind and nature, whether known or unknown, suspected or unsuspected, which Plaintiff now has, has ever had, or may hereafter have against Defendant arising out of or in any way related to the Action.

3. Confidentiality. The Parties agree that the terms of this Agreement, including the Settlement Amount, shall remain strictly confidential and shall not be disclosed to any third party except as required by law, court order, or as necessary for tax reporting purposes. The Parties may disclose the existence of the settlement but not it's terms.

4. No Admission. This Agreement shall not be construed as an admission of liability, fault, or wrongdoing by either Party. The Parties have entered into this Agreement solely to avoid the expense and uncertainty of continued litigation.

5. Governing Law. This Agreement shall be governed by and construed in accordance with the laws of the State of Illinois, without regard to it's conflict of laws principles.""",
        "error_types": ["its_vs_its", "missing_oxford_comma", "redundant_doublets", "missing_unknown_claims_waiver", "missing_dispute_resolution"],
    },
])

# ---------------------------------------------------------------------------
# CLEAN SAMPLES (should produce minimal/no findings)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "brief",
        "doc_subtype": "clean_brief",
        "text": """The Court should deny Defendant's Motion for Summary Judgment because genuine disputes of material fact preclude judgment as a matter of law.

Under the applicable standard, summary judgment is appropriate only when "there is no genuine dispute as to any material fact and the movant is entitled to judgment as a matter of law." Fed. R. Civ. P. 56(a). The moving party bears the initial burden of demonstrating the absence of a genuine factual dispute. Once that burden is met, the nonmoving party must present specific facts showing a triable issue.

Here, Plaintiff has submitted the sworn declaration of two eyewitnesses who observed Defendant's maintenance crew inspecting the premises three days before the incident. This testimony directly contradicts Defendant's assertion that it had no knowledge of the hazardous condition. The credibility of witnesses and the weight of evidence are matters for the jury, not the Court, to resolve at the summary judgment stage.""",
        "error_types": ["clean_sample"],
    },
    {
        "category": "email",
        "doc_subtype": "clean_email",
        "text": """Subject: Morrison v. Springfield — Hearing Update

Dear Ms. Morrison,

I am writing to update you on today's hearing. The Court heard arguments on Defendant's motion to exclude our expert witness and ruled in our favor. Dr. Williams will be permitted to testify at trial about the safety standards applicable to commercial properties.

This is a significant development. The Court's ruling preserves our strongest evidence on the question of whether Defendant met its duty of care. I will send you a copy of the written order when it is filed.

Our next deadline is the pretrial conference on April 15. I will be in touch next week to prepare.

Please do not hesitate to contact me if you have any questions.

Sincerely,
Michael Torres""",
        "error_types": ["clean_sample"],
    },
    {
        "category": "contract",
        "doc_subtype": "clean_clause",
        "text": """9.1 Governing Law. This Agreement is governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of laws principles.

9.2 Dispute Resolution. Any dispute arising out of or relating to this Agreement must first be submitted to mediation in accordance with the Commercial Mediation Procedures of the American Arbitration Association. If the dispute is not resolved through mediation within sixty (60) days, either party may commence litigation in the courts of the State of Delaware or the United States District Court for the District of Delaware.

9.3 Attorneys' Fees. In any action to enforce this Agreement, the prevailing party is entitled to recover its reasonable attorneys' fees and costs from the non-prevailing party.

9.4 Waiver. No waiver of any provision of this Agreement is effective unless it is in writing and signed by the waiving party. A party's failure to enforce any provision of this Agreement does not constitute a waiver of that provision or any other provision.""",
        "error_types": ["clean_sample"],
    },
])

# ---------------------------------------------------------------------------
# DEPOSITION SUMMARIES (10 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "deposition",
        "doc_subtype": "summary",
        "text": """DEPOSITION SUMMARY

Case: Morrison v. Springfield Properties, Inc.
Witness: John Harris (Shift Supervisor)
Date of Deposition: February 20, 2026
Summarized by: David Park, Associate

BACKGROUND AND EMPLOYMENT (pp. 5-18)

Mr. Harris testified that he has been employed by Springfield Properties as a shift supervisor since June 2019. He is responsible for overseeing maintenance and custodial staff during the morning shift, which runs from 6:00 AM to 2:00 PM. He acknowledged that he had received training on the company's safety protocols, including procedures for addressing spills and wet floor conditions, however he could not recall the specific date of his most recent training session.

EVENTS OF NOVEMBER 12, 2025 (pp. 19-35)

Harris stated he was notified of a water leak in the main lobby at approximately 8:15 AM via radio from the front desk receptionist. He testified that he "immediately" directed custodial staff member Maria Santos to address the leak. When asked whether he personally verified that wet floor signs were placed, he stated: "I directed Maria to take care of it. I assumed she would follow protocol." (22:14-17)

On cross-examination, Harris admitted that company policy requires wet floor signs to be placed within 5 minutes of a reported spill or leak, and that he did not personally verify compliance with this policy on the date in question. He was showed company records indicating that wet floor signs were not checked out from the supply closet until 9:45 AM — approximately 90 minutes after the initial report and 30 minutes after Plaintiff's alleged fall. Harris did not dispute the accuracy of these records but testified that he was "surprised" by the timeframe.

KEY ADMISSIONS

1. Harris was aware of the water leak at 8:15 AM but took no steps to personally verify that safety measures were implemented.
2. He acknowledged that company policy was not followed with respect to the timing of wet floor sign placement.
3. He admitted that he had received "at least three" prior reports of water leaks in the same lobby area in the preceeding six months. (28:3-9)""",
        "error_types": ["comma_splice", "showed_vs_shown", "with_respect_to", "spelling_preceding"],
    },
])

# ---------------------------------------------------------------------------
# PROPOSED ORDERS (10 samples)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "order",
        "doc_subtype": "proposed_order",
        "text": """IN THE CIRCUIT COURT OF SANGAMON COUNTY, ILLINOIS

JANE MORRISON,
    Plaintiff,
v.                                              Case No. 2025-L-04521
SPRINGFIELD PROPERTIES, INC.,
    Defendant.

[PROPOSED] ORDER GRANTING PLAINTIFF'S MOTION TO COMPEL

THIS MATTER having come before the Court upon Plaintiff's Motion to Compel Discovery Responses, filed on February 14, 2026, and the Court having reviewed the Motion, Defendant's Opposition, Plaintiff's Reply, and the arguments of counsel presented at the hearing held on March 5, 2026, and for good cause shown;

The Court finds that Defendant's responses to Plaintiff's First Set of Interrogatories were insufficient and did not comply with the requirements of Illinois Supreme Court Rule 213.

IT IS HEREBY ORDERED as follows:

1. Plaintiff's Motion to Compel is GRANTED in part and DENIED in part.

2. Defendant shall supplement it's responses to Interrogatory Nos. 1, 5, and 8 within fourteen (14) days of the date of this Order. Supplemental responses must be complete, non-evasive, and responsive to the specific questions asked.

3. Defendant shall produce all documents responsive to Plaintiff's Requests for Production Nos. 3, 7, and 12 within fourteen (14) days of the date of this Order.

4. Defendant's request for a protective order with respect to Interrogatory No. 8 is DENIED.

5. Plaintiffs request for sanctions pursuant to Illinois Supreme Court Rule 219(c) is DENIED without prejudice. However, the Court cautions Defendant that further failures to comply with discovery obligations may result in sanctions, including but not limited to adverse inference instructions.

6. The discovery deadline in this matter is hereby extended to May 15, 2026.

SO ORDERED this ____ day of ____________, 2026.

____________________________________
Hon. Maria Gonzalez
Circuit Court Judge""",
        "error_types": ["its_vs_its", "possessive_error_plaintiffs", "with_respect_to", "including_but_not_limited"],
    },
])

# ---------------------------------------------------------------------------
# PLAIN LANGUAGE TARGETS (10 samples — dense legalese for translation)
# ---------------------------------------------------------------------------

TEMPLATES.extend([
    {
        "category": "contract_dense",
        "doc_subtype": "legalese_termination",
        "text": """Notwithstanding anything herein to the contrary, in the event that the Licensee shall fail to comply with any material term or condition of this Agreement and such failure shall continue unremedied for a period of thirty (30) days after written notice thereof shall have been given by the Licensor to the Licensee, the Licensor shall have the right, at its sole option and discretion, to terminate this Agreement forthwith and without further obligation to the Licensee, and the Licensee shall thereupon cease and desist from any and all use of the Licensed Materials and shall return or destroy, at the Licensor's election, each and every copy of the Licensed Materials in the Licensee's possession or control, and shall certify in writing to the Licensor that such return or destruction has been completed, provided, however, that the Licensee's obligations under Sections 5 (Confidentiality), 7 (Indemnification), and 9 (Limitation of Liability) shall survive any such termination.""",
        "error_types": ["excessive_sentence_length", "archaic_language", "redundant_doublets", "nested_qualifications", "shall_overuse", "provided_however"],
    },
    {
        "category": "contract_dense",
        "doc_subtype": "legalese_indemnity",
        "text": """The Indemnifying Party shall, at its sole cost and expense, indemnify, defend, and hold harmless the Indemnified Party and its respective officers, directors, employees, agents, successors, and assigns (collectively, the "Indemnified Persons") from and against any and all losses, damages, liabilities, deficiencies, claims, actions, judgments, settlements, interest, awards, penalties, fines, costs, and expenses of whatever kind, including reasonable attorneys' fees, fees, and the costs of enforcing any right to indemnification under this Agreement and the cost of pursuing any insurance providers, arising out of or resulting from any claim of a third party or the Indemnifying Party arising out of or occurring in connection with the Indemnifying Party's negligence, willful misconduct, or breach of any representation, warranty, or obligation under this Agreement; provided, however, that the foregoing indemnification shall not apply to the extent that any such losses are attributable to the gross negligence or willful misconduct of the Indemnified Party.""",
        "error_types": ["excessive_sentence_length", "kitchen_sink_definition", "redundant_doublets", "provided_however"],
    },
])

# ============================================================================
# VARIANT GENERATION — expand templates via error injection
# ============================================================================

# Additional error injectors for variant generation
def inject_wrong_modal(text):
    """Swap shall/may/must/will incorrectly."""
    swaps = [
        ("shall ", "will "), ("may ", "shall "), ("must ", "may "),
        ("will ", "shall "), ("shall not", "may not"),
    ]
    r = random.choice(swaps)
    return text.replace(r[0], r[1], 1) if r[0] in text else text

def inject_legalese(text):
    """Add archaic legalese."""
    insertions = [
        ("herein", "hereinafter"), ("under", "pursuant to"),
        ("before", "prior to"), ("because", "due to the fact that"),
        ("if", "in the event that"), ("about", "with respect to"),
        ("use", "utilize"), ("enough", "sufficient"),
        ("begin", "commence"), ("end", "terminate"),
        ("help", "facilitate"), ("buy", "purchase"),
    ]
    for old, new in insertions:
        # Only replace whole words (crude but effective)
        for sep in [" ", ",", "."]:
            pattern = f" {old}{sep}"
            replacement = f" {new}{sep}"
            if pattern in text:
                return text.replace(pattern, replacement, 1)
    return text

def inject_and_or(text):
    """Inject ambiguous 'and/or'."""
    for word in [" and ", " or "]:
        if word in text:
            return text.replace(word, " and/or ", 1)
    return text

def inject_spelling_error(text):
    """Inject common legal misspellings."""
    typos = [
        ("judgment", "judgement"), ("acknowledgment", "acknowledgement"),
        ("privilege", "priviledge"), ("defendant", "defendent"),
        ("plaintiff", "plantiff"), ("deposition", "depostion"),
        ("interrogatory", "interogatory"), ("subpoena", "subpena"),
        ("indemnify", "indemnfy"), ("jurisdiction", "jurisdction"),
        ("allegation", "allegtion"), ("statute", "statut"),
    ]
    r = random.choice(typos)
    if r[0] in text.lower():
        # Case-preserving replace
        import re
        return re.sub(re.escape(r[0]), r[1], text, count=1, flags=re.IGNORECASE)
    return text

def inject_double_negative(text):
    """Add double negatives."""
    swaps = [
        ("common", "not uncommon"), ("likely", "not unlikely"),
        ("frequent", "not infrequent"), ("reasonable", "not unreasonable"),
    ]
    for old, new in swaps:
        if f" {old} " in text:
            return text.replace(f" {old} ", f" {new} ", 1)
    return text

INJECTORS = [
    inject_contraction, inject_passive_voice, inject_nominalization,
    inject_wrong_modal, inject_legalese, inject_and_or,
    inject_spelling_error, inject_double_negative,
]

def inject_subject_verb_error(text):
    """Introduce subject-verb disagreement."""
    swaps = [
        ("parties agree", "parties agrees"), ("court finds", "court find"),
        ("claims are", "claims is"), ("defendants were", "defendants was"),
        ("allegations remain", "allegations remains"),
        ("documents show", "documents shows"), ("terms apply", "terms applies"),
        ("rights are", "rights is"), ("obligations include", "obligations includes"),
        ("provisions govern", "provisions governs"),
    ]
    r = random.choice(swaps)
    if r[0] in text:
        return text.replace(r[0], r[1], 1)
    return text

def inject_which_that_error(text):
    """Swap which/that incorrectly."""
    if " that " in text:
        return text.replace(" that ", " which ", 1)
    if ", which " in text:
        return text.replace(", which ", " that ", 1)
    return text

def inject_redundant_doublet(text):
    """Add redundant legal doublets."""
    doublets = [
        ("void", "null and void"), ("cease", "cease and desist"),
        ("terms", "terms and conditions"), ("rules", "rules and regulations"),
        ("act", "act and deed"), ("will", "last will and testament"),
        ("assign", "assign and transfer"), ("give", "give, devise, and bequeath"),
        ("own", "own, possess, and enjoy"),
    ]
    for old, new in doublets:
        if f" {old} " in text:
            return text.replace(f" {old} ", f" {new} ", 1)
    return text

def inject_hedging(text):
    """Add hedging language."""
    hedges = [
        (". The", ". Arguably, the"), (". This", ". It seems that this"),
        (". We", ". Perhaps we"), ("will ", "may arguably "),
        ("should ", "it could be said that one should "),
    ]
    r = random.choice(hedges)
    if r[0] in text:
        return text.replace(r[0], r[1], 1)
    return text

def inject_missing_oxford(text):
    """Remove Oxford comma from a list."""
    import re
    # Find ", and " preceded by a comma-list pattern
    match = re.search(r',\s+and\s+', text)
    if match:
        # Check if there's another comma before this one (3+ item list)
        before = text[:match.start()]
        if ',' in before:
            return text[:match.start()] + " and " + text[match.end():]
    return text

def inject_sentence_fragment(text):
    """Create a sentence fragment."""
    sentences = text.split('. ')
    if len(sentences) > 2:
        idx = random.randint(1, len(sentences) - 2)
        s = sentences[idx]
        words = s.split()
        if len(words) > 5:
            # Remove the verb (typically word 1-2)
            fragment = ' '.join(words[:2]) + ' ' + ' '.join(words[3:])
            sentences[idx] = fragment
            return '. '.join(sentences)
    return text

INJECTORS = [
    inject_contraction, inject_passive_voice, inject_nominalization,
    inject_wrong_modal, inject_legalese, inject_and_or,
    inject_spelling_error, inject_double_negative,
    inject_subject_verb_error, inject_which_that_error,
    inject_redundant_doublet, inject_hedging, inject_missing_oxford,
    inject_sentence_fragment,
]

def generate_variants(templates, target_total=150):
    """Generate variants of existing templates by applying error injectors."""
    variants = []
    random.seed(123)  # Reproducible variants

    needed = target_total - len(templates)
    if needed <= 0:
        return []

    attempts = 0
    seen_texts = {t["text"].strip()[:80] for t in templates}  # Dedup by prefix

    while len(variants) < needed and attempts < needed * 10:
        attempts += 1
        base = random.choice(templates)
        text = base["text"]

        # Apply 2-4 random injectors for more mutation
        num_injections = random.randint(2, 4)
        chosen = random.sample(INJECTORS, min(num_injections, len(INJECTORS)))
        new_errors = list(base["error_types"])

        changed = False
        for inj in chosen:
            old_text = text
            text = inj(text)
            if text != old_text:
                changed = True
                inj_name = inj.__name__.replace("inject_", "")
                if inj_name not in new_errors:
                    new_errors.append(inj_name)

        prefix = text.strip()[:80]
        if changed and prefix not in seen_texts:
            seen_texts.add(prefix)
            variants.append({
                "category": base["category"],
                "doc_subtype": base.get("doc_subtype", "general") + "_variant",
                "text": text,
                "error_types": new_errors,
            })

    return variants


# ============================================================================
# BATCH GENERATION
# ============================================================================

def make_batch_item(template):
    """Create a batch item from a template."""
    return {
        "batch_id": str(uuid.uuid4()),
        "user_input": template["text"].strip(),
        "category": template["category"],
        "doc_subtype": template.get("doc_subtype", "general"),
        "error_types": template["error_types"],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate grammar training batches")
    parser.add_argument("--output-dir", required=True, help="Output directory for batch files")
    parser.add_argument("--samples-per-batch", type=int, default=25, help="Samples per batch file")
    parser.add_argument("--shuffle", action="store_true", default=True, help="Shuffle samples")
    parser.add_argument("--target", type=int, default=150, help="Target total sample count (generates variants to reach this)")
    parser.add_argument("--no-variants", action="store_true", help="Skip variant generation")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Merge research templates
    all_templates = list(TEMPLATES)
    if RESEARCH_TEMPLATES:
        all_templates.extend(RESEARCH_TEMPLATES)
        print(f"Research templates: {len(RESEARCH_TEMPLATES)}")

    # Generate variants to reach target
    if not args.no_variants and len(all_templates) < args.target:
        variants = generate_variants(TEMPLATES, target_total=args.target)
        all_templates.extend(variants)
        print(f"Base templates: {len(TEMPLATES)}, Generated variants: {len(variants)}")

    # Create batch items
    items = [make_batch_item(t) for t in all_templates]

    if args.shuffle:
        random.seed(42)
        random.shuffle(items)

    # Stats
    categories = {}
    for item in items:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print(f"Generated {len(items)} training samples:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    error_types = set()
    for item in items:
        error_types.update(item["error_types"])
    print(f"\nDistinct error types: {len(error_types)}")

    clean_count = sum(1 for item in items if "clean_sample" in item["error_types"])
    print(f"Clean samples (should pass): {clean_count}")

    # Write batches
    batch_num = 0
    for i in range(0, len(items), args.samples_per_batch):
        batch = items[i:i + args.samples_per_batch]
        batch_file = output_dir / f"batch-{batch_num}.jsonl"
        with open(batch_file, "w") as f:
            for item in batch:
                f.write(json.dumps(item) + "\n")
        print(f"\n  Wrote {len(batch)} items to {batch_file}")
        batch_num += 1

    print(f"\nTotal: {len(items)} items in {batch_num} batch(es)")
    print(f"\nTo generate gold-standard corrections via Claude Sonnet:")
    print(f"  cd /home/veech/Documents/local-ai-legal-setup")
    print(f"  ./tests/tune-grammar-models.sh generate")


if __name__ == "__main__":
    main()
