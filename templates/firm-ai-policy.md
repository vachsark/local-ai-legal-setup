# Firm AI Usage Policy

_Per ABA Model Rules 5.1 (Supervisory Responsibilities), 5.3 (Non-lawyer Assistants), and ABA Formal Opinion 512 (2024)_

---

> This is a sample firm policy template. Replace bracketed fields with firm-specific information. This policy should be reviewed by firm leadership, IT, and ethics counsel before adoption.

**Effective Date:** [DATE]
**Last Reviewed:** [DATE]
**Next Review:** [DATE — recommend annual review]
**Policy Owner:** [NAME / TITLE]

---

## 1. Purpose

This policy establishes [FIRM NAME]'s standards for the ethical and responsible use of artificial intelligence (AI) tools in legal practice. It implements the requirements of ABA Model Rules 1.1 (Competence), 1.6 (Confidentiality), 5.1 (Supervisory Responsibilities), and 5.3 (Non-lawyer Assistants) as applied to AI, consistent with ABA Formal Opinion 512 (July 2024).

---

## 2. Approved Tools and Configurations

### 2.1 Approved AI Tools

| Tool        | Type          | Data Handling                 | Approved Uses         |
| ----------- | ------------- | ----------------------------- | --------------------- |
| [TOOL NAME] | Local / Cloud | [Local-only / Cloud with DPA] | [List approved tasks] |
| [TOOL NAME] | Local / Cloud | [Local-only / Cloud with DPA] | [List approved tasks] |

### 2.2 Approved Configurations

- All local AI tools must bind to `localhost` only (not accessible from the network)
- Cloud AI tools must have a signed Data Processing Agreement (DPA) on file
- API keys must be stored securely (not in shared documents, chat logs, or email)
- Auto-training on input data must be disabled for all cloud providers

### 2.3 Unapproved Tools

The following are **not approved** for use with client data:

- Free-tier consumer AI chatbots (ChatGPT free, Google Gemini free, etc.)
- AI tools without reviewed privacy policies or DPAs
- Browser extensions that process page content through external servers
- Any AI tool not listed in Section 2.1 above

Personnel who wish to use an AI tool not on the approved list must submit a request to [POLICY OWNER / IT DEPARTMENT] for review before use.

---

## 3. Prohibited Uses

AI tools shall **never** be used to:

1. **File AI output directly** with any court, agency, or opposing party without attorney review and independent verification
2. **Process client data** in non-approved cloud tools without client consent and a signed DPA
3. **Substitute for legal judgment** — AI output is a starting point, not a final product
4. **Generate case citations** for use in filings — all citations must be independently verified in Westlaw, Lexis, or primary sources
5. **Communicate with clients** — AI-generated text must not be sent to clients as legal advice without attorney review
6. **Access opposing party privileged materials** — do not upload potentially privileged documents to AI tools
7. **Create billing entries** — AI cannot generate or modify time entries

---

## 4. Verification Requirements

### 4.1 Citation Verification

**Every legal citation** in AI-generated text must be independently verified before use. This includes:

- Case citations (party names, reporter, volume, page, year, court)
- Statute references (title, section, subsection)
- Regulatory citations (CFR, state regulations)
- Secondary source references

Verification must be performed in authoritative legal databases (Westlaw, Lexis, official government sources), not by asking the AI to confirm its own citations.

### 4.2 Legal Standard Verification

AI descriptions of legal tests, standards, and elements must be verified against authoritative sources. AI tools may conflate elements from different tests or misstate standards.

### 4.3 Factual Claims

All factual assertions in AI-generated text must be verified against the case file and source documents. AI tools may fabricate or misattribute facts.

### 4.4 Documentation

Attorneys should maintain records of:

- Which deliverables involved AI assistance
- What verification steps were performed
- The source used for verification

---

## 5. Competence Requirements (Rule 1.1)

### 5.1 Initial Training

All personnel who use AI tools must complete training covering:

- [ ] How the approved AI tools work (capabilities and limitations)
- [ ] Known risks (hallucination, citation fabrication, bias)
- [ ] This firm AI policy
- [ ] Verification procedures
- [ ] Client disclosure requirements
- [ ] Data handling obligations

### 5.2 Continuing Education

- Personnel must complete at least [NUMBER] hours of AI-related CLE annually
- The firm will track AI-related CLE completion
- New AI tools or significant updates require supplemental training before use

### 5.3 Competence Assessment

Personnel should be able to:

- Identify when AI output is unreliable or fabricated
- Explain AI's limitations to clients in plain language
- Choose the appropriate AI tool for a given task
- Know when NOT to use AI (privileged analysis, high-stakes filings, nuanced jurisdictional questions)

---

## 6. Confidentiality (Rule 1.6)

### 6.1 Client Data Classification

Before using AI tools, classify the data:

| Classification                        | Local AI | Approved Cloud AI   | Consumer AI |
| ------------------------------------- | -------- | ------------------- | ----------- |
| Public filings                        | Yes      | Yes                 | Yes         |
| Non-sensitive work product            | Yes      | Yes                 | No          |
| Client confidential                   | Yes      | With consent        | No          |
| Privileged communications             | Yes      | With consent + DPA  | No          |
| Highly sensitive (trade secrets, PII) | Yes      | Case-by-case review | No          |

### 6.2 Client Consent

- Informed client consent is required before processing client data through cloud AI tools
- Use the firm's client disclosure template (see `templates/client-disclosure.md`)
- Generic engagement letter language is not sufficient — disclosure must be specific to AI use

---

## 7. Supervisory Chain (Rules 5.1 / 5.3)

### 7.1 Attorney Supervision

- **Partners / supervising attorneys** are responsible for ensuring associates' and paralegals' AI use complies with this policy
- All AI-assisted work product must be reviewed by a licensed attorney before use
- Supervising attorneys must be competent in AI capabilities and limitations (Section 5)

### 7.2 Non-Lawyer Personnel

- Paralegals, law clerks, and staff may use approved AI tools under attorney supervision
- Non-lawyer personnel must complete the same training (Section 5.1)
- Their AI-assisted work product requires the same attorney review as any other work product

### 7.3 Vendors and Contractors

- Third-party vendors who use AI in firm work must disclose their AI usage
- Vendor AI tools must meet the same confidentiality standards as firm tools
- Vendor use of AI on firm matters must be covered by appropriate contractual protections

---

## 8. Incident Reporting

### 8.1 What to Report

Report immediately to [POLICY OWNER] if:

- AI-fabricated citations are discovered in filed documents
- Client data is inadvertently processed through an unapproved tool
- AI output is sent to a client or opposing party without proper review
- A security incident involving AI tools or API keys
- Any instance where AI output may have caused client harm

### 8.2 Response Procedure

1. **Contain** — Stop using the involved tool immediately
2. **Report** — Notify [POLICY OWNER] within [TIMEFRAME, e.g., 24 hours]
3. **Assess** — Evaluate the impact on client matters
4. **Remediate** — Take corrective action (amended filings, client notification, etc.)
5. **Document** — Record the incident and response for future reference

---

## 9. Annual Review

This policy will be reviewed and updated at least annually, or sooner when:

- New ABA opinions or state bar guidance is issued
- New AI tools are adopted by the firm
- Significant changes occur in AI capabilities or risks
- An incident reveals a policy gap

**Review checklist:**

- [ ] Approved tools list is current
- [ ] Training requirements reflect current tool capabilities
- [ ] Client disclosure template is current
- [ ] Verification procedures are adequate
- [ ] Incident log reviewed for patterns
- [ ] CLE requirements met by all personnel
- [ ] State bar guidance checked for updates

---

## 10. Acknowledgment

I have read, understand, and agree to comply with [FIRM NAME]'s AI Usage Policy.

**Signature:** **************\_\_\_\_**************

**Printed Name:** **************\_\_\_\_**************

**Title:** **************\_\_\_\_**************

**Date:** **************\_\_\_\_**************

---

_This policy is based on ABA Model Rules of Professional Conduct and ABA Formal Opinion 512 (July 2024). Individual state bar rules may impose additional or different requirements. Consult your jurisdiction's ethics rules and opinions for state-specific obligations._
