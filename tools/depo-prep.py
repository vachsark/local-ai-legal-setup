"""
title: Deposition Prep Assistant
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Analyze prior deposition transcripts, generate follow-up questions, flag
  contradictions and evasion, and build topic outlines. Upload a transcript to get started.
"""

import json
import re
from typing import Optional

from pydantic import BaseModel


class Tools:
    class Valves(BaseModel):
        max_transcript_chars: int = 200000
        max_qa_pairs_in_payload: int = 150

    def __init__(self):
        self.valves = self.Valves()

    # ── Public tool methods ────────────────────────────────────────────────────

    async def analyze_transcript(
        self,
        __files__: Optional[list] = None,
        __event_emitter__=None,
    ) -> str:
        """
        Upload a deposition transcript for full analysis. Extracts all Q/A exchanges,
        identifies admissions, flags contradictions, notes evasion patterns, and
        catalogs objections. Upload a TXT, PDF, or DOCX file.

        :return: Structured transcript analysis for the LLM to present.
        """
        await self._emit(__event_emitter__, "Loading transcript...", done=False)

        if not __files__:
            return (
                "No transcript uploaded. Please attach a TXT, PDF, or DOCX file "
                "using the paperclip icon, then ask me to analyze it."
            )

        try:
            text = self._extract_text(__files__[0])
        except Exception as e:
            await self._emit(__event_emitter__, "Failed to read file", done=True)
            return f"Error reading file: {e}"

        if not text or not text.strip():
            return "The uploaded file appears to be empty or could not be read."

        truncated = len(text) > self.valves.max_transcript_chars
        if truncated:
            text = text[: self.valves.max_transcript_chars]

        await self._emit(__event_emitter__, "Parsing Q/A exchanges...", done=False)

        exchanges = self._parse_qa_pairs(text)
        objections = self._extract_objections(text)
        admissions = self._find_admissions(exchanges)
        evasions = self._find_evasions(exchanges)
        contradictions = self._find_contradictions(exchanges)
        topics = self._identify_topic_shifts(exchanges)
        witness_name = self._extract_witness_name(text)

        await self._emit(__event_emitter__, "Analysis complete", done=True)

        payload = {
            "analysis_type": "deposition_transcript",
            "witness": witness_name,
            "source_file": __files__[0].get("filename", __files__[0].get("name", "transcript")),
            "truncated": truncated,
            "stats": {
                "total_exchanges": len(exchanges),
                "total_objections": len(objections),
                "admissions_flagged": len(admissions),
                "evasion_instances": len(evasions),
                "potential_contradictions": len(contradictions),
                "topic_areas": len(topics),
            },
            "admissions": admissions,
            "contradictions": contradictions,
            "evasion_instances": evasions,
            "objections": objections,
            "topic_areas": topics,
            "qa_sample": exchanges[: self.valves.max_qa_pairs_in_payload],
            "analysis_instructions": (
                "You have been given structured pre-analysis of a deposition transcript. "
                "Using the extracted data above, produce a full deposition analysis with these sections:\n\n"
                "## 1. Witness Overview\n"
                "Brief description of the witness's role and the scope of their testimony.\n\n"
                "## 2. Key Admissions\n"
                "For each admission, quote the testimony and note its legal significance. "
                "Include exchange numbers from the data.\n\n"
                "## 3. Contradictions & Inconsistencies\n"
                "For each contradiction, quote both statements and describe the inconsistency. "
                "Suggest how to use each for impeachment.\n\n"
                "## 4. Evasion & Non-Responsive Answers\n"
                "For each flagged evasion, quote the Q and A, identify the evasion pattern, "
                "and suggest the follow-up approach.\n\n"
                "## 5. Objection Log\n"
                "List all objections with their grounds and the resulting answer (if any).\n\n"
                "## 6. Topic Coverage & Gaps\n"
                "List the major topic areas covered and identify areas that appear under-explored.\n\n"
                "## 7. Priority Follow-Up Areas\n"
                "Ranked list of the 5-7 most important areas for continued examination."
            ),
        }

        return json.dumps(payload, indent=2)

    async def generate_questions(
        self,
        topic: str,
        witness_role: str,
        case_type: str,
        context: str = "",
        __event_emitter__=None,
    ) -> str:
        """
        Generate deposition questions for a specific topic, witness, and case type.
        Provides discovery questions, impeachment question templates, and a topic outline.

        :param topic: The specific topic or issue to cover (e.g., "contract negotiation history").
        :param witness_role: The witness's role (e.g., "VP of Operations", "treating physician").
        :param case_type: Type of case (e.g., "breach of contract", "personal injury", "employment").
        :param context: Optional — paste relevant prior testimony or case facts for tailored questions.
        :return: Structured question set for the LLM to present.
        """
        await self._emit(__event_emitter__, "Building question set...", done=False)

        qa_sample = []
        if context:
            exchanges = self._parse_qa_pairs(context)
            qa_sample = exchanges[:40]

        await self._emit(__event_emitter__, "Questions ready", done=True)

        payload = {
            "tool": "question_generator",
            "topic": topic,
            "witness_role": witness_role,
            "case_type": case_type,
            "prior_testimony_provided": bool(context),
            "prior_testimony_sample": qa_sample,
            "generation_instructions": (
                f"Generate a structured deposition question set for the following:\n\n"
                f"- **Topic**: {topic}\n"
                f"- **Witness role**: {witness_role}\n"
                f"- **Case type**: {case_type}\n"
                + (
                    f"\nPrior testimony has been provided in `prior_testimony_sample`. "
                    f"Use it to generate targeted follow-up questions.\n"
                    if qa_sample
                    else ""
                )
                + "\n\nProduce the following sections:\n\n"
                "## Foundation & Background Questions\n"
                "5-7 open-ended questions to establish the witness's knowledge and role. "
                "Each question on its own line, numbered.\n\n"
                "## Core Topic Questions\n"
                "10-15 questions covering the main topic. Mix of open and leading. "
                "Note the purpose of each question in brackets: [discovery] [foundation] [lock-in].\n\n"
                "## Impeachment Sequences\n"
                "If prior testimony was provided, identify 2-4 contradiction areas and write a "
                "3-step impeachment sequence for each:\n"
                "  1. Pin the current testimony (leading, get a clear commitment)\n"
                "  2. Confront with the prior inconsistent statement\n"
                "  3. Follow-up to prevent wiggle room\n\n"
                "## Document Introduction Questions\n"
                "5 template questions for introducing exhibits on this topic. "
                "Use [EXHIBIT X] as a placeholder.\n\n"
                "## Cleanup Questions\n"
                "3-5 catch-all questions to close the topic.\n\n"
                "**Drafting rules to follow (mandatory)**:\n"
                "- One fact per question. No compound questions.\n"
                "- Leading is acceptable — this is a deposition.\n"
                "- Open-ended for new territory, closed/leading for impeachment.\n"
                "- Never argumentative. Pin facts, don't editorialize.\n"
                "- Foundation before impeachment — always.\n"
            ),
        }

        return json.dumps(payload, indent=2)

    async def prep_outline(
        self,
        topics: str = "",
        __files__: Optional[list] = None,
        __event_emitter__=None,
    ) -> str:
        """
        Generate a full deposition outline from an uploaded transcript plus optional topic list.
        Organizes questions by legal element, flags gaps, and suggests exhibit sequence.
        Upload a prior transcript and/or case materials.

        :param topics: Comma-separated list of legal elements or topics to cover
                       (e.g., "notice, damages, breach, affirmative defenses").
        :return: Full structured deposition outline for the LLM to build on.
        """
        await self._emit(__event_emitter__, "Building outline...", done=False)

        transcript_text = ""
        filename = ""
        if __files__:
            try:
                transcript_text = self._extract_text(__files__[0])
                filename = __files__[0].get("filename", __files__[0].get("name", ""))
                if len(transcript_text) > self.valves.max_transcript_chars:
                    transcript_text = transcript_text[: self.valves.max_transcript_chars]
            except Exception as e:
                await self._emit(__event_emitter__, "File read error", done=True)
                return f"Error reading uploaded file: {e}"

        parsed_topics = [t.strip() for t in topics.split(",") if t.strip()] if topics else []

        exchanges = []
        witness_name = ""
        covered_topics = []
        admissions = []
        evasions = []
        contradictions = []
        objections = []

        if transcript_text:
            exchanges = self._parse_qa_pairs(transcript_text)
            witness_name = self._extract_witness_name(transcript_text)
            covered_topics = self._identify_topic_shifts(exchanges)
            admissions = self._find_admissions(exchanges)
            evasions = self._find_evasions(exchanges)
            contradictions = self._find_contradictions(exchanges)
            objections = self._extract_objections(transcript_text)

        await self._emit(__event_emitter__, "Outline ready", done=True)

        payload = {
            "tool": "prep_outline",
            "witness": witness_name or "Unknown",
            "source_file": filename or "No file uploaded",
            "requested_topics": parsed_topics,
            "transcript_stats": {
                "exchanges_parsed": len(exchanges),
                "admissions": len(admissions),
                "contradictions": len(contradictions),
                "evasions": len(evasions),
                "objections": len(objections),
            },
            "covered_topic_areas": covered_topics,
            "admissions_found": admissions,
            "contradictions_found": contradictions,
            "evasion_areas": evasions,
            "objection_summary": objections[:20],
            "transcript_sample": exchanges[:60],
            "outline_instructions": (
                "Build a complete deposition outline using the pre-analyzed data above.\n\n"
                + (
                    f"The attorney wants to cover these legal elements: {', '.join(parsed_topics)}.\n\n"
                    if parsed_topics
                    else ""
                )
                + "Structure the outline as follows:\n\n"
                "## Deposition Outline — [Witness Name]\n\n"
                "### I. Background & Qualifications (10-15 min)\n"
                "Bullet list of specific questions.\n\n"
                "### II. [Topic Area 1] (estimate time)\n"
                "- Legal element this covers\n"
                "- Foundation questions (numbered)\n"
                "- Core questions (numbered)\n"
                "- Documents to introduce (list by exhibit or description)\n"
                "- Follow-up if evasive (based on evasion patterns found)\n\n"
                "[Repeat for each topic area]\n\n"
                "### [IMPEACHMENT SECTION] Contradictions to Exploit\n"
                "For each contradiction found:\n"
                "  - Contradiction description\n"
                "  - 3-step impeachment sequence\n\n"
                "### CLOSING — Cleanup & Commitments\n"
                "Standard closing questions to lock in the record.\n\n"
                "## Exhibit Sequence\n"
                "List exhibits in the order they should be introduced, with a one-line "
                "purpose for each.\n\n"
                "## Strategic Notes\n"
                "2-3 bullet points on the most important vulnerabilities to exploit "
                "and areas to avoid or handle carefully."
            ),
        }

        return json.dumps(payload, indent=2)

    # ── Transcript parser ──────────────────────────────────────────────────────

    def _parse_qa_pairs(self, text: str) -> list:
        """
        Parse Q/A exchanges from a deposition transcript.

        Handles four transcript formats:
          1. Standard:     "Q: Did you sign?"  / "A: Yes."
          2. Dotted:       "Q. Did you sign?"  / "A. Yes."
          3. Verbose:      "QUESTION: Did you sign?" / "ANSWER: Yes."
          4. Numbered:     "  5    Q.  Did you sign?" (federal court reporter style —
                           leading line number stripped before pattern matching)

        Also handles VOLUME / DAY headers for multi-day depositions (pagination
        resets are noted in page_line as "Vol.N p.PP:LL").

        Returns list of dicts with keys: index, page_line, question, answer,
        objections, answer_quality.
        """
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        exchanges = []
        lines = text.splitlines()

        current_q = []
        current_a = []
        current_objections = []
        current_page = ""
        current_line_no = ""
        current_volume = ""
        exchange_idx = 0

        # ── Pattern definitions ────────────────────────────────────────────────
        # Page header: standalone number (transcript page number)
        page_pattern = re.compile(r"^\s{0,4}(\d{1,4})\s*$")

        # Volume / day header (multi-day depositions)
        volume_pattern = re.compile(
            r"VOLUME\s+(?:I{1,3}V?|V?I{0,3}|\d+)\b.*?(?:DAY\s+\d+)?",
            re.IGNORECASE,
        )

        # Federal reporter numbered-line format: "   5    Q.  text"
        # Captures: (line_number, Q_or_A_or_QUESTION_or_ANSWER, content)
        numbered_line_pattern = re.compile(
            r"^\s{1,6}(\d{1,2})\s{1,8}"  # leading line number (1-99)
            r"(Q|A|QUESTION|ANSWER|BY\s+\w[\w\s\.]*?)\s*[\.:]?\s+(.*)",
            re.IGNORECASE,
        )

        # Standard Q/A: "Q: ...", "Q. ...", "Q  ..."
        qa_q_pattern = re.compile(r"^Q[:\.]?\s+(.*)", re.IGNORECASE)
        qa_a_pattern = re.compile(r"^A[:\.]?\s+(.*)", re.IGNORECASE)

        # Verbose format: "QUESTION: ..." / "ANSWER: ..."
        verbose_q_pattern = re.compile(r"^QUESTION\s*:\s*(.*)", re.IGNORECASE)
        verbose_a_pattern = re.compile(r"^ANSWER\s*:\s*(.*)", re.IGNORECASE)

        obj_pattern = re.compile(
            r"^(?:MR\.|MS\.|MRS\.|THE COURT:|COURT:)\s+\S.*\b(?:Objection|Object)\b",
            re.IGNORECASE,
        )
        obj_any = re.compile(
            r"^(?:MR\.|MS\.|MRS\.|THE COURT:|COURT:|COUNSEL:)\s+(.+)", re.IGNORECASE
        )

        state = "idle"  # idle | q | a

        def flush_exchange():
            nonlocal exchange_idx
            if current_q and current_a:
                q_text = " ".join(current_q).strip()
                a_text = " ".join(current_a).strip()
                exchange_idx += 1
                quality = self._classify_answer_quality(q_text, a_text)
                # Build page_line reference: "p.5:3" or "Vol.II p.5:3"
                pl = ""
                if current_page:
                    pl = f"p.{current_page}"
                    if current_line_no:
                        pl += f":{current_line_no}"
                    if current_volume:
                        pl = f"{current_volume} {pl}"
                exchanges.append(
                    {
                        "index": exchange_idx,
                        "page_line": pl,
                        "question": q_text,
                        "answer": a_text,
                        "objections": list(current_objections),
                        "answer_quality": quality,
                    }
                )

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Volume/day header — update volume tracking, don't reset page
            if volume_pattern.search(stripped) and len(stripped) < 80:
                vm = re.search(
                    r"VOLUME\s+(I{1,3}V?|V?I{0,3}|\d+)", stripped, re.IGNORECASE
                )
                if vm:
                    current_volume = f"Vol.{vm.group(1).upper()}"
                continue

            # Page number line — track current page
            pm = page_pattern.match(stripped)
            if pm and len(stripped) <= 4:
                current_page = pm.group(1)
                current_line_no = ""
                continue

            # Try numbered-line format first (federal court reporter)
            m_num = numbered_line_pattern.match(line)  # use raw line for indent check
            if m_num:
                line_no_str, role, content = m_num.group(1), m_num.group(2).strip(), m_num.group(3).strip()
                current_line_no = line_no_str
                role_upper = role.upper().split()[0]  # "BY" -> "BY", "Q" -> "Q", etc.
                if role_upper in ("Q", "QUESTION"):
                    flush_exchange()
                    current_q = [content]
                    current_a = []
                    current_objections = []
                    state = "q"
                    continue
                elif role_upper in ("A", "ANSWER"):
                    current_a = [content]
                    state = "a"
                    continue
                # "BY MR. JONES:" lines are examiner labels — skip
                elif role_upper == "BY":
                    continue

            m_q = qa_q_pattern.match(stripped)
            m_a = qa_a_pattern.match(stripped)
            m_vq = verbose_q_pattern.match(stripped)
            m_va = verbose_a_pattern.match(stripped)
            m_obj = obj_pattern.match(stripped)

            if m_vq:
                # QUESTION: ... (verbose format)
                flush_exchange()
                current_q = [m_vq.group(1)]
                current_a = []
                current_objections = []
                state = "q"

            elif m_va:
                # ANSWER: ... (verbose format)
                current_a = [m_va.group(1)]
                state = "a"

            elif m_q:
                # New question — flush prior exchange
                flush_exchange()
                current_q = [m_q.group(1)]
                current_a = []
                current_objections = []
                state = "q"

            elif m_a:
                current_a = [m_a.group(1)]
                state = "a"

            elif m_obj:
                # Objection between Q and A, or after Q before A
                full_obj = stripped
                grounds = self._extract_objection_grounds(full_obj)
                current_objections.append(
                    {
                        "text": full_obj,
                        "grounds": grounds,
                        "exchange_index": exchange_idx + 1,
                    }
                )

            elif state == "q" and not m_a and not m_obj:
                # Continuation of question
                if stripped and not obj_any.match(stripped):
                    current_q.append(stripped)

            elif state == "a" and not m_q and not m_obj:
                # Continuation of answer
                if stripped and not obj_any.match(stripped):
                    current_a.append(stripped)

        # Flush last exchange
        flush_exchange()
        return exchanges

    def _classify_answer_quality(self, question: str, answer: str) -> str:
        """Classify whether an answer is responsive, evasive, or a denial."""
        a_lower = answer.lower()
        q_lower = question.lower()

        # Evasion patterns — checked FIRST to prevent denial short-circuit
        # (many evasive phrases contain "not" and would be misclassified as denial)
        evasion_signals = [
            r"\bi don'?t (?:recall|remember|know|recollect)\b",
            r"\bi'?m not (?:sure|certain|aware|familiar)\b",
            r"\bi (?:would|would have to|can't) (?:need to |)(?:review|check|look at)\b",
            r"\bi'?d (?:have to|need to) (?:check|review|look at|see)\b",
            r"\bi may have\b",
            r"\bi might have\b",
            r"\bwould need to (?:review|check|see|look)\b",
            r"\bto the best of my (?:recollection|knowledge|memory)\b",
            r"\bi believe\b.{0,40}\bbut\b",
            r"\bsomething like that\b",
            r"\bgenerally speaking\b",
            r"\bthat'?s not (?:my|the right)\b",
            r"\bcan you (?:repeat|rephrase|clarify)\b",
            r"\bi'?d have to (?:check|review|look)\b",
            r"\bwithout reviewing\b",
            r"\bwithout (?:looking at|checking)\b",
            r"\bnot (?:familiar|sure) (?:with |about )?(?:the )?specific\b",
            # Deflection / responsibility dodging
            r"\b(?:you'?d?|you would) (?:have to|need to) (?:ask|check with)\b",
            r"\b(?:that'?s|this is) (?:not my|outside my|beyond my) (?:area|role|department|responsibility|expertise)\b",
            r"\bi'?m not the (?:right person|best person|appropriate person)\b",
            r"\bsomeone else (?:would|could|should)\b",
            r"\byou'?d? (?:have to|need to|want to) (?:ask|check)\b",
            # Memory failure with selective precision
            r"\bi (?:cannot|can'?t) (?:recall|remember) (?:specifically|exactly|precisely|the exact)\b",
            r"\bas i (?:sit|stand) here (?:today|now)\b",
            r"\bat this (?:time|point|moment),?\s*i (?:cannot|can'?t|don'?t)\b",
            # Non-answer / redirect
            r"\bthat'?s not (?:what i said|what i meant|how i would characterize)\b",
            r"\bi (?:cannot|can'?t) speak to\b",
            r"\bi(?:'?m| am) not (?:in a position|able) to\b",
            r"\bif i said that\b",
            # Over-hedging
            r"\bto (?:my|the best of my) (?:knowledge|recollection|understanding|awareness)\b",
            r"\bmy (?:understanding|recollection|recollection) (?:is|was) that\b.{0,40}\bbut\b",
            r"\bapproximately\b.{0,30}\bi(?:'?m| am) not (?:sure|certain)\b",
            r"\bi (?:prefer not|would prefer not) to (?:speculate|guess)\b",
            r"\bi (?:really|honestly) (?:cannot|can'?t|don'?t)\b",
        ]
        for pat in evasion_signals:
            if re.search(pat, a_lower):
                return "evasive"

        # Admission patterns — short affirmative answers
        if re.search(r"^(yes|correct|that's right|that is correct|right|true|i did|i was|i am)", a_lower):
            return "admission"

        # Direct denial patterns (checked after evasion to avoid false positives
        # on phrases like "I am not in a position to answer")
        if re.search(r"\b(no|not|never|didn't|did not|wasn't|was not|don't|do not)\b", a_lower):
            if len(answer.split()) < 15:
                return "denial"

        # Qualified admission
        qualifier_signals = [r"\bi think\b", r"\bi believe\b", r"\bi assume\b", r"\bprobably\b"]
        for pat in qualifier_signals:
            if re.search(pat, a_lower):
                return "qualified"

        return "responsive"

    def _extract_objections(self, text: str) -> list:
        """Extract all objections with their stated grounds from raw transcript text."""
        objections = []
        seen = set()

        obj_line_pattern = re.compile(
            r"^(?:MR\.|MS\.|MRS\.|THE COURT:|COUNSEL:)\s+"
            r"(?:[A-Z][A-Z\s\.]+:\s+)?Objection[,\.]?\s*(.*)",
            re.IGNORECASE | re.MULTILINE,
        )

        for m in obj_line_pattern.finditer(text):
            full = m.group(0).strip()
            grounds_raw = m.group(1).strip().rstrip(".")
            if not grounds_raw:
                grounds_raw = "unstated"
            key = full[:80].lower()
            if key not in seen:
                objections.append(
                    {
                        "objection": full,
                        "grounds": self._normalize_objection_grounds(grounds_raw),
                        "raw_grounds": grounds_raw,
                    }
                )
                seen.add(key)

        return objections

    def _extract_objection_grounds(self, obj_text: str) -> str:
        after = re.sub(
            r"^(?:MR\.|MS\.|MRS\.|THE COURT:|COUNSEL:)\s+(?:[A-Z]+:\s+)?Objection[,\.]?\s*",
            "",
            obj_text,
            flags=re.IGNORECASE,
        ).strip().rstrip(".")
        return self._normalize_objection_grounds(after) if after else "unstated"

    def _normalize_objection_grounds(self, raw: str) -> str:
        raw_lower = raw.lower()
        mapping = {
            "form": "form",
            "leading": "leading",
            "foundation": "foundation / lack of foundation",
            "lack of foundation": "foundation / lack of foundation",
            "assumes facts": "assumes facts not in evidence",
            "not in evidence": "assumes facts not in evidence",
            "speculation": "calls for speculation",
            "calls for speculation": "calls for speculation",
            "hearsay": "hearsay",
            "relevance": "relevance",
            "vague": "vague and ambiguous",
            "ambiguous": "vague and ambiguous",
            "argumentative": "argumentative",
            "asked and answered": "asked and answered",
            "compound": "compound question",
            "mischaracterizes": "mischaracterizes testimony/evidence",
            "legal conclusion": "calls for a legal conclusion",
            "privilege": "privilege",
        }
        for key, label in mapping.items():
            if key in raw_lower:
                return label
        return raw[:60] if raw else "unstated"

    def _find_admissions(self, exchanges: list) -> list:
        """Find exchanges where the witness made clear admissions."""
        admissions = []
        admission_triggers = [
            r"^yes\b",
            r"^correct\b",
            r"^that'?s? (?:right|correct)\b",
            r"^i (?:did|was|am|have|had|knew|know|saw|said|told|agreed|signed|approved|authorized)\b",
            r"^that is correct\b",
            r"^absolutely\b",
            r"^you'?re (?:right|correct)\b",
        ]
        for ex in exchanges:
            a_lower = ex["answer"].lower().strip()
            for pat in admission_triggers:
                if re.match(pat, a_lower):
                    # Only flag if there's a substantive question (not just "state your name")
                    q_lower = ex["question"].lower()
                    skip_q = re.search(
                        r"\b(name|title|spell|how long|how many years|introduce)\b", q_lower
                    )
                    if not skip_q:
                        admissions.append(
                            {
                                "exchange": ex["index"],
                                "page_line": ex["page_line"],
                                "question": ex["question"],
                                "answer": ex["answer"],
                                "admission_type": "direct_affirmative",
                            }
                        )
                    break

        return admissions[:30]

    def _find_evasions(self, exchanges: list) -> list:
        """Find exchanges where the answer quality is evasive."""
        evasions = []
        for ex in exchanges:
            if ex["answer_quality"] == "evasive":
                evasions.append(
                    {
                        "exchange": ex["index"],
                        "page_line": ex["page_line"],
                        "question": ex["question"],
                        "answer": ex["answer"],
                        "pattern": self._characterize_evasion(ex["answer"]),
                    }
                )
        return evasions[:30]

    def _characterize_evasion(self, answer: str) -> str:
        a = answer.lower()
        if re.search(r"\bdon'?t (?:recall|remember|recollect)\b", a):
            return "memory_failure"
        if re.search(r"\bas i (?:sit|stand) here|at this (?:time|point|moment),?\s*i (?:cannot|can'?t|don'?t)\b", a):
            return "memory_failure"
        if re.search(r"\b(?:need to|have to|would need to) (?:review|check|look at)\b", a):
            return "defers_to_documents"
        if re.search(
            r"\b(?:i'?m not the right person|not my (?:role|responsibility|department|area|expertise))\b"
            r"|\b(?:you'?d?|you would) (?:have to|need to) (?:ask|check with)\b"
            r"|\bsomeone else (?:would|could|should)\b",
            a,
        ):
            return "deflects_responsibility"
        if re.search(r"\bi(?:'?m| am) not (?:in a position|able) to\b|\bi (?:cannot|can'?t) speak to\b", a):
            return "deflects_responsibility"
        if re.search(r"\bi'?m not (?:sure|certain|aware)\b|\bi (?:prefer not|would prefer not) to (?:speculate|guess)\b", a):
            return "uncertainty_hedge"
        if re.search(r"\bthat'?s not what i said\b|\bthat'?s not how i would characterize\b|\bif i said that\b", a):
            return "disputes_characterization"
        if re.search(r"\bto (?:my|the best of my) (?:knowledge|recollection|understanding|awareness)\b", a):
            return "selective_precision"
        return "non_responsive"

    def _find_contradictions(self, exchanges: list) -> list:
        """
        Find potential contradictions within the transcript.
        Looks for: (1) answers that directly contradict each other on the same factual
        issue, (2) timeline inconsistencies, (3) knowledge-then-ignorance patterns.
        """
        contradictions = []

        # Strategy: compare all evasive/denial answers against all admissions
        # for overlapping subject-matter keywords
        admissions = [e for e in exchanges if e["answer_quality"] in ("admission", "responsive")]
        denials_evasions = [e for e in exchanges if e["answer_quality"] in ("denial", "evasive")]

        for d in denials_evasions:
            d_tokens = set(self._key_tokens(d["question"] + " " + d["answer"]))
            for a in admissions:
                if a["index"] >= d["index"]:
                    continue  # Only look backward for earlier admissions
                a_tokens = set(self._key_tokens(a["question"] + " " + a["answer"]))
                overlap = d_tokens & a_tokens
                if len(overlap) >= 3:
                    contradictions.append(
                        {
                            "type": "potential_contradiction",
                            "earlier_exchange": a["index"],
                            "later_exchange": d["index"],
                            "earlier_statement": {
                                "question": a["question"],
                                "answer": a["answer"],
                                "answer_quality": a["answer_quality"],
                            },
                            "later_statement": {
                                "question": d["question"],
                                "answer": d["answer"],
                                "answer_quality": d["answer_quality"],
                            },
                            "shared_subject_tokens": list(overlap)[:10],
                            "description": (
                                f"Exchange {a['index']} (admission/responsive) vs "
                                f"Exchange {d['index']} (denial/evasive) on overlapping subject matter."
                            ),
                        }
                    )
                    if len(contradictions) >= 15:
                        break
            if len(contradictions) >= 15:
                break

        return contradictions

    def _key_tokens(self, text: str) -> list:
        """Extract meaningful tokens (nouns, verbs) for overlap comparison."""
        stop = {
            "the", "a", "an", "is", "it", "in", "of", "to", "and", "or", "for",
            "with", "on", "at", "was", "were", "be", "been", "by", "that", "this",
            "i", "you", "he", "she", "we", "they", "my", "your", "his", "her",
            "not", "no", "yes", "did", "do", "does", "have", "had", "are", "am",
            "any", "some", "from", "about", "as", "but", "if", "so", "what",
            "when", "how", "which", "who", "can", "would", "could", "should",
            "may", "might", "will", "just", "then", "than", "there", "here",
            "also", "all", "more", "one", "would", "those", "these",
        }
        tokens = re.findall(r"\b[a-z]{3,}\b", text.lower())
        return [t for t in tokens if t not in stop]

    def _identify_topic_shifts(self, exchanges: list) -> list:
        """
        Identify major topic areas by clustering adjacent questions with shared vocabulary.
        Returns list of topic summary dicts.
        """
        if not exchanges:
            return []

        topics = []
        window = 5
        used = set()

        for i, ex in enumerate(exchanges):
            if i in used:
                continue

            # Build a cluster of exchanges with high token overlap
            anchor_tokens = set(self._key_tokens(ex["question"]))
            if len(anchor_tokens) < 2:
                continue

            cluster = [ex]
            for j in range(i + 1, min(i + window + 1, len(exchanges))):
                neighbor_tokens = set(self._key_tokens(exchanges[j]["question"]))
                overlap = anchor_tokens & neighbor_tokens
                if len(overlap) >= 2:
                    cluster.append(exchanges[j])
                    used.add(j)

            if len(cluster) >= 2:
                # Name the topic from most common tokens
                all_tokens = []
                for c in cluster:
                    all_tokens.extend(self._key_tokens(c["question"]))
                token_freq = {}
                for t in all_tokens:
                    token_freq[t] = token_freq.get(t, 0) + 1
                top = sorted(token_freq.items(), key=lambda x: -x[1])[:4]
                topic_label = ", ".join(t for t, _ in top) if top else "general"

                topics.append(
                    {
                        "topic_label": topic_label,
                        "exchange_range": f"{cluster[0]['index']}-{cluster[-1]['index']}",
                        "exchange_count": len(cluster),
                        "first_question": cluster[0]["question"][:120],
                        "admissions_in_topic": sum(
                            1 for c in cluster if c["answer_quality"] == "admission"
                        ),
                        "evasions_in_topic": sum(
                            1 for c in cluster if c["answer_quality"] == "evasive"
                        ),
                    }
                )
            used.add(i)

        return topics[:25]

    def _extract_witness_name(self, text: str) -> str:
        """Extract the deponent's name from standard transcript headers."""
        patterns = [
            r"DEPOSITION OF ([A-Z][A-Z ,.]+)",
            r"EXAMINATION OF ([A-Z][A-Z ,.]+)",
            r"DEPONENT[:\s]+([A-Z][A-Za-z ,.\-]+)",
            r"WITNESS[:\s]+([A-Z][A-Za-z ,.\-]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text[:3000])
            if m:
                return m.group(1).strip().title()
        return ""

    # ── File extraction (shared pattern) ──────────────────────────────────────

    def _extract_text(self, file_obj: dict) -> str:
        filename = file_obj.get("filename", file_obj.get("name", ""))

        content = None
        if "content" in file_obj:
            content = file_obj["content"]
        elif "data" in file_obj and isinstance(file_obj["data"], dict):
            content = file_obj["data"].get("content", "")
        elif "data" in file_obj and isinstance(file_obj["data"], str):
            content = file_obj["data"]
        elif "path" in file_obj:
            return self._read_from_path(file_obj["path"], filename)

        if content is None:
            raise ValueError(
                f"Could not extract text from '{filename}'. "
                "Ensure the file is TXT or that Open WebUI has extracted its content."
            )

        if isinstance(content, str) and self._is_base64(content):
            content = self._decode_base64(content, filename)

        return content if isinstance(content, str) else str(content)

    def _read_from_path(self, path: str, filename: str) -> str:
        import subprocess

        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext == "pdf":
            try:
                result = subprocess.run(
                    ["pdftotext", path, "-"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return result.stdout
                raise ValueError(f"pdftotext failed: {result.stderr[:200]}")
            except FileNotFoundError:
                raise ValueError(
                    "pdftotext not found. Install poppler-utils: "
                    "'brew install poppler' (Mac) or 'apt install poppler-utils' (Linux)."
                )
        else:
            with open(path, "r", errors="replace") as f:
                return f.read()

    def _is_base64(self, s: str) -> bool:
        if len(s) < 100:
            return False
        sample = s[:200].strip()
        b64_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        )
        return all(c in b64_chars for c in sample if c not in "\n\r")

    def _decode_base64(self, encoded: str, filename: str) -> str:
        import base64
        import subprocess
        import tempfile
        import os

        data = base64.b64decode(encoded)
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

        if ext == "pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                result = subprocess.run(
                    ["pdftotext", tmp_path, "-"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return result.stdout
                raise ValueError(f"pdftotext failed: {result.stderr[:200]}")
            except FileNotFoundError:
                raise ValueError("pdftotext not found. Install poppler-utils.")
            finally:
                os.unlink(tmp_path)
        else:
            return data.decode("utf-8", errors="replace")

    # ── Utilities ──────────────────────────────────────────────────────────────

    async def _emit(self, emitter, description: str, done: bool = False):
        if emitter:
            await emitter(
                {
                    "type": "status",
                    "data": {"description": description, "done": done},
                }
            )
