# Legal Grammar Test Samples

Test samples with known errors for benchmarking model accuracy. Each sample has annotated expected findings.

---

## Sample 1: Email with Common Errors

```
EXPECTED: contraction (don't), informal tone (ASAP, FYI), missing Oxford comma, passive voice, buried action item
```

Subject: Quick update on the Smith matter

Hi Tom,

I don't think we should file the motion until we've reviewed the deposition transcripts, the expert reports and the interrogatory responses. FYI the deadline is next Friday so we need to move ASAP.

The brief was reviewed by Sarah and she said it looks fine but I think the argument about estoppel could be stronger. Can you take a look when you get a chance?

Also, the client called and they want to know about the settlement offer. I told them we'd get back to them but didn't give a timeline. Let me know what you think we should tell them.

Thanks,
Mike

---

## Sample 2: Brief with Grammar Issues

```
EXPECTED: subject-verb agreement (data...show), which/that confusion, tense inconsistency, sentence length, passive voice, missing parallel structure, hedging language
```

The data collected during the investigation show that Defendant's conduct, which was in direct violation of the terms of the Agreement that was executed on January 15, 2024, constituted a material breach of the covenant of good faith and fair dealing which the parties agreed to uphold.

Plaintiff's damages, which includes lost profits, consequential damages, and the costs of mitigation, was substantial. It is arguable that the evidence presented at trial will demonstrate that Defendant's actions were intentional and that they perhaps knew about the consequences of their breach before it occurred.

The court should also consider that the plaintiff made multiple attempts to resolve this dispute through informal negotiations, mediation, and had also proposed arbitration as an alternative. Each of these efforts were rejected by the Defendant without any explanation being provided.

---

## Sample 3: Contract Clause with Ambiguity

```
EXPECTED: and/or, vague timeframe (promptly, reasonable), missing "without limitation", dangling modifier, inconsistent defined terms, ambiguous scope modifier
```

The Vendor shall promptly notify the Client and/or its designated representative of any security breach affecting the Systems, including unauthorized access to Client Data. The Vendor shall take reasonable steps to mitigate the impact of such breach within a reasonable time after discovery.

Having been notified of the breach, remediation efforts shall commence immediately. The vendor agrees to indemnify Client for all losses, damages, costs and expenses arising from or related to any breach of this Section, including attorney's fees.

The term "Systems" includes all hardware, software, and network infrastructure provided by Vendor to client pursuant to this agreement, including any third-party components.

---

## Sample 4: Memo with Structural Issues

```
EXPECTED: wrong modal verb (will vs shall), "to the extent" misuse, nominalization, passive voice, inconsistent party references
```

QUESTION PRESENTED

Whether the employer will be liable for wrongful termination where the employee was discharged subsequent to the filing of a workers' compensation claim.

DISCUSSION

To the extent that the employee filed a workers' compensation claim, the employer made the determination to terminate her employment. The termination was effectuated approximately fourteen days after the claim was filed by Ms. Rodriguez.

Under the applicable statute, employers shall not retaliate against employees who exercise their right to file workers' compensation claims. The Company argues that the decision to terminate Rodriguez was based on poor performance evaluations that were conducted prior to the filing of the claim by the employee. However, the temporal proximity between the filing of the claim and the termination gives rise to an inference of retaliatory intent.

---

## Sample 5: Clean Text (Should Pass)

```
EXPECTED: No critical issues. At most one or two minor style suggestions.
```

The Court should deny Defendant's Motion for Summary Judgment because genuine disputes of material fact preclude judgment as a matter of law. Specifically, the record contains conflicting testimony about whether Defendant received actual notice of the defective condition before the incident occurred.

Under the applicable standard, summary judgment is appropriate only when "there is no genuine dispute as to any material fact and the movant is entitled to judgment as a matter of law." Fed. R. Civ. P. 56(a). The moving party bears the initial burden of demonstrating the absence of a genuine factual dispute. Once that burden is met, the nonmoving party must present specific facts showing a triable issue.

Here, Plaintiff has submitted the sworn declaration of two eyewitnesses who observed Defendant's maintenance crew inspecting the premises three days before the incident. This testimony directly contradicts Defendant's assertion that it had no knowledge of the hazardous condition.

---

## Scoring Rubric

For each sample, score the model on:

1. **True Positives** — Correctly identified errors (out of expected findings)
2. **False Positives** — Flagged non-issues as errors
3. **False Negatives** — Missed actual errors
4. **Precision** — Of what it flagged, how much was correct?
5. **Legal Awareness** — Did it preserve terms of art? Did it avoid "correcting" correct legal usage?
6. **Output Quality** — Was the output well-organized and actionable?

**Target**: ≥85% true positive rate, ≤10% false positive rate, zero legal term corrections.
