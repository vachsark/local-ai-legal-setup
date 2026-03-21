"""
title: Citation Checker
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Scans AI-generated legal text for citation-like patterns and flags every instance for human verification. Prioritizes high recall — better to over-flag than miss a fabricated citation. Addresses ABA Rules 3.3 (candor) and 1.1 (competence).
"""

import json
import re
from typing import Optional

from pydantic import BaseModel


class Tools:
    class Valves(BaseModel):
        max_text_length: int = 50000

    def __init__(self):
        self.valves = self.Valves()

        # Federal reporters
        self.federal_reporters = [
            r"U\.S\.",
            r"S\.Ct\.",
            r"S\. Ct\.",
            r"L\.Ed\.",
            r"L\. Ed\.",
            r"L\.Ed\.2d",
            r"L\. Ed\. 2d",
            r"F\.",
            r"F\.2d",
            r"F\.3d",
            r"F\.4th",
            r"F\.\s*Supp\.",
            r"F\.\s*Supp\.\s*2d",
            r"F\.\s*Supp\.\s*3d",
            r"Fed\.\s*Cl\.",
            r"B\.R\.",
        ]

        # State reporters
        self.state_reporters = [
            r"Cal\.App\.",
            r"Cal\.App\.\s*\d+",
            r"Cal\.\s*\d+",
            r"Cal\.Rptr\.",
            r"Cal\.Rptr\.\s*2d",
            r"Cal\.Rptr\.\s*3d",
            r"N\.Y\.S\.",
            r"N\.Y\.S\.2d",
            r"N\.Y\.S\.3d",
            r"A\.D\.\s*\d+",
            r"N\.Y\.\s*\d+",
            r"N\.E\.",
            r"N\.E\.2d",
            r"N\.E\.3d",
            r"N\.W\.",
            r"N\.W\.2d",
            r"S\.E\.",
            r"S\.E\.2d",
            r"S\.W\.",
            r"S\.W\.2d",
            r"S\.W\.3d",
            r"So\.",
            r"So\.\s*2d",
            r"So\.\s*3d",
            r"P\.",
            r"P\.2d",
            r"P\.3d",
            r"A\.",
            r"A\.2d",
            r"A\.3d",
        ]

        # Non-existent reporters (red flags)
        # These are series beyond the current highest series for each reporter.
        # LLMs frequently hallucinate "next series" reporters.
        self.fake_reporters = [
            # Federal reporters — F. is only at 4th
            r"F\.5th",
            r"F\.6th",
            # Supreme Court reporters — no 2d series
            r"U\.S\.R\.",
            r"S\.Ct\.2d",
            # Federal Supplement — no 4th series
            r"F\.Supp\.4th",
            # Regional reporters — each currently stops at 3d (NE, NW) or 2d (SE)
            r"N\.E\.4th",
            r"S\.E\.3d",
            r"N\.W\.3d",
            r"S\.W\.4th",
            r"P\.4th",
            r"A\.4th",
            r"So\.\s*4th",
            # New York state reporters — N.Y.S. is at 3d, no 4th series
            r"N\.Y\.S\.4d",
            r"N\.Y\.S\.4th",
            # California App reporters — Cal.App. is at 4th (5th and above do not exist)
            r"Cal\.App\.\s*5th",
            r"Cal\.App\.\s*6th",
            # Cal.Rptr. is at 3d — no 4th series
            r"Cal\.Rptr\.\s*4th",
        ]

        # Bluebook signals
        self.bluebook_signals = [
            "See,",
            "See ",
            "See also",
            "Cf.",
            "But see",
            "But cf.",
            "Compare",
            "See generally",
            "Accord",
            "E.g.,",
            "Contra",
        ]

    async def check_citations(
        self,
        text: str,
        __event_emitter__=None,
    ) -> str:
        """
        Scan legal text for citations and flag each one for human verification.
        Detects case citations, statute references, regulatory citations, and
        Bluebook signals. Flags suspicious patterns (non-existent reporters,
        impossible volumes, court/reporter mismatches).

        :param text: The legal text to scan for citations.
        :return: JSON report of all citations found with risk flags.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Scanning for citations...",
                        "done": False,
                    },
                }
            )

        if not text or not text.strip():
            return json.dumps(
                {
                    "citations_found": [],
                    "summary": {
                        "total": 0,
                        "high_risk_count": 0,
                        "recommendation": "No text provided to scan.",
                    },
                },
                indent=2,
            )

        # Truncate if too long
        if len(text) > self.valves.max_text_length:
            text = text[: self.valves.max_text_length]

        citations = []

        # 1. Case citations: volume reporter page pattern
        # e.g., 123 F.3d 456, 550 U.S. 544
        citations.extend(self._find_case_citations(text))

        # 2. Statute citations: U.S.C., C.F.R., state codes
        citations.extend(self._find_statute_citations(text))

        # 3. "v." pattern (party names)
        citations.extend(self._find_v_citations(text))

        # 4. Bluebook signals
        citations.extend(self._find_bluebook_signals(text))

        # Deduplicate by position
        citations = self._deduplicate(citations)

        # Count high-risk
        high_risk = sum(1 for c in citations if c.get("red_flags"))

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Found {len(citations)} citation(s), {high_risk} flagged",
                        "done": True,
                    },
                }
            )

        if not citations:
            recommendation = "No citations detected. If the text was expected to contain legal references, this may indicate they were described generally rather than cited specifically."
        elif high_risk > 0:
            recommendation = f"ATTENTION: {high_risk} citation(s) have red flags suggesting possible fabrication. ALL {len(citations)} citations should be independently verified in Westlaw, Lexis, or primary sources before use."
        else:
            recommendation = f"Found {len(citations)} citation(s). None triggered automatic red flags, but ALL citations from AI-generated text must be independently verified before use in any legal document."

        output = {
            "citations_found": citations,
            "summary": {
                "total": len(citations),
                "high_risk_count": high_risk,
                "recommendation": recommendation,
            },
        }

        return json.dumps(output, indent=2)

    def _find_case_citations(self, text: str) -> list:
        """Find volume/reporter/page citations."""
        citations = []

        # Build reporter alternation — include fake reporters so they get matched
        # and then flagged, rather than passing silently through undetected.
        all_reporters = self.federal_reporters + self.state_reporters + self.fake_reporters
        reporter_pattern = "|".join(all_reporters)

        # Match: number reporter number (optional parenthetical)
        pattern = (
            r"(\d{1,4})\s+("
            + reporter_pattern
            + r")\s+(\d{1,5})"
            + r"(?:\s*,\s*\d{1,5})?"  # optional pinpoint
            + r"(?:\s*\([^)]{1,50}\))?"  # optional parenthetical
        )

        for match in re.finditer(pattern, text):
            full_text = match.group(0).strip()
            volume = int(match.group(1))
            reporter = match.group(2).strip()
            page = int(match.group(3))
            start = match.start()

            red_flags = []

            # Check for non-existent reporters
            for fake in self.fake_reporters:
                if re.search(fake, reporter):
                    red_flags.append(f"Non-existent reporter: {reporter}")

            # Check impossible U.S. Reports volume (currently ~600)
            if re.search(r"U\.S\.", reporter) and not re.search(
                r"U\.S\.C\.", reporter
            ):
                if volume > 600:
                    red_flags.append(
                        f"Suspicious U.S. Reports volume: {volume} (currently ~600 volumes)"
                    )

            # Check for round-number suspicious patterns
            if volume % 100 == 0 and page % 100 == 0 and volume > 0 and page > 0:
                red_flags.append(
                    f"Suspiciously round numbers: {volume} ... {page}"
                )

            # Check court/reporter mismatch in parenthetical
            paren_match = re.search(r"\(([^)]+)\)", full_text)
            if paren_match:
                paren = paren_match.group(1)
                # F.3d/F.4th should have circuit court, not district
                if re.search(r"F\.(?:3d|4th)", reporter):
                    if re.search(
                        r"[SNWCE]\.D\.|M\.D\.|W\.D\.", paren
                    ) and not re.search(r"Cir\.", paren):
                        red_flags.append(
                            "Court/reporter mismatch: F.3d/F.4th is for circuit courts, but parenthetical suggests district court"
                        )
                # F.Supp. should have district court, not circuit
                if re.search(r"F\.\s*Supp\.", reporter):
                    if re.search(r"Cir\.", paren) and not re.search(
                        r"D\.|Bankr\.", paren
                    ):
                        red_flags.append(
                            "Court/reporter mismatch: F.Supp. is for district courts, but parenthetical suggests circuit court"
                        )

            citations.append(
                {
                    "text": full_text,
                    "type": "case_citation",
                    "position": start,
                    "red_flags": red_flags,
                }
            )

        return citations

    def _find_statute_citations(self, text: str) -> list:
        """Find statute and regulation citations."""
        citations = []

        # U.S.C. citations: 42 U.S.C. § 1983
        for match in re.finditer(
            r"\d{1,2}\s+U\.S\.C\.?\s*(?:§|[Ss]ec(?:tion|\.)?)\s*\d+[\w.-]*(?:\([a-zA-Z0-9]+\))*",
            text,
        ):
            citations.append(
                {
                    "text": match.group(0).strip(),
                    "type": "federal_statute",
                    "position": match.start(),
                    "red_flags": [],
                }
            )

        # C.F.R. citations: 29 C.F.R. § 1926.451
        for match in re.finditer(
            r"\d{1,2}\s+C\.F\.R\.?\s*(?:§|[Ss]ec(?:tion|\.)?|[Pp]art)?\s*\d+[\w.-]*",
            text,
        ):
            citations.append(
                {
                    "text": match.group(0).strip(),
                    "type": "federal_regulation",
                    "position": match.start(),
                    "red_flags": [],
                }
            )

        # State statute patterns: Cal. Civ. Code § 1234, N.Y. Gen. Bus. Law § 349
        for match in re.finditer(
            r"(?:Cal|N\.Y|Tex|Fla|Ill|Ohio|Pa|Mich|Ga|N\.J|Va|Wash|Mass|Ind|Ariz|Tenn|Mo|Md|Wis|Minn|Colo|Ala|La|Ky|Or|Okla|Conn|Iowa|Miss|Ark|Kan|Utah|Nev|N\.M|W\.Va|Neb|Idaho|Haw|Me|N\.H|R\.I|Mont|Del|S\.D|N\.D|Alaska|Vt|Wyo)\.?\s+(?:\w+\.?\s+)*(?:Code|Law|Stat|Ann|Gen|Rev|Comp|Bus)\b[^.]*?§\s*[\d.-]+",
            text,
        ):
            citations.append(
                {
                    "text": match.group(0).strip(),
                    "type": "state_statute",
                    "position": match.start(),
                    "red_flags": [],
                }
            )

        # Generic section symbol pattern: § followed by numbers
        for match in re.finditer(r"§§?\s*\d+[\w.-]*", text):
            # Skip if already captured as federal/state statute
            pos = match.start()
            if not any(
                c["position"] <= pos <= c["position"] + len(c["text"])
                for c in citations
            ):
                citations.append(
                    {
                        "text": match.group(0).strip(),
                        "type": "statute_reference",
                        "position": pos,
                        "red_flags": [],
                    }
                )

        return citations

    def _find_v_citations(self, text: str) -> list:
        """Find party v. party case name patterns."""
        citations = []

        # Match: Capitalized word(s) v. Capitalized word(s)
        # Avoid matching things like "v. 2.0" or common non-case uses
        pattern = r"(?<!\w)([A-Z][a-zA-Z'.-]+(?:\s+[A-Z][a-zA-Z'.-]+){0,4})\s+v\.\s+([A-Z][a-zA-Z'.-]+(?:\s+[A-Z][a-zA-Z'.-]+){0,4})(?!\w)"

        for match in re.finditer(pattern, text):
            full = match.group(0).strip()
            start = match.start()

            # Skip if this is part of an already-captured case citation
            # (the case citation finder gets the full cite with reporter)
            red_flags = []

            # Check if the case name appears without any reporter citation nearby
            context_after = text[match.end() : match.end() + 100]
            has_reporter = bool(
                re.search(
                    r"\d{1,4}\s+(?:"
                    + "|".join(self.federal_reporters + self.state_reporters)
                    + r")",
                    context_after,
                )
            )
            if not has_reporter:
                # Check if there's a reporter on the same line or nearby
                context_line = text[
                    max(0, start - 20) : min(len(text), match.end() + 150)
                ]
                has_reporter = bool(
                    re.search(
                        r"\d{1,4}\s+(?:"
                        + "|".join(
                            self.federal_reporters + self.state_reporters
                        )
                        + r")",
                        context_line,
                    )
                )

            if not has_reporter:
                red_flags.append(
                    "Case name without reporter citation — may be incomplete or fabricated"
                )

            citations.append(
                {
                    "text": full,
                    "type": "case_name",
                    "position": start,
                    "red_flags": red_flags,
                }
            )

        return citations

    def _find_bluebook_signals(self, text: str) -> list:
        """Find Bluebook introductory signals."""
        citations = []

        for signal in self.bluebook_signals:
            # Use word boundary to avoid false positives
            escaped = re.escape(signal)
            for match in re.finditer(
                r"(?:^|(?<=\s))" + escaped, text, re.MULTILINE
            ):
                citations.append(
                    {
                        "text": signal.strip(),
                        "type": "bluebook_signal",
                        "position": match.start(),
                        "red_flags": [],
                    }
                )

        return citations

    def _deduplicate(self, citations: list) -> list:
        """Remove duplicate citations at the same position."""
        seen = set()
        unique = []
        for c in sorted(citations, key=lambda x: x["position"]):
            key = (c["position"], c["type"])
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def validate_output(self, output_json: str) -> dict:
        """
        Validate that the citation checker output conforms to the expected schema.
        Returns {"valid": bool, "errors": list[str]}.
        Useful for catching model output drift when this tool is used with an LLM pipeline.
        """
        import json

        errors = []
        try:
            data = json.loads(output_json)
        except json.JSONDecodeError as e:
            return {"valid": False, "errors": [f"Invalid JSON: {e}"]}

        # Top-level keys
        for key in ("citations_found", "summary"):
            if key not in data:
                errors.append(f"Missing top-level key: '{key}'")

        # summary sub-keys
        summary = data.get("summary", {})
        for key in ("total", "high_risk_count", "recommendation"):
            if key not in summary:
                errors.append(f"Missing summary key: '{key}'")

        if "total" in summary and not isinstance(summary["total"], int):
            errors.append("summary.total must be an integer")

        if "high_risk_count" in summary and not isinstance(
            summary["high_risk_count"], int
        ):
            errors.append("summary.high_risk_count must be an integer")

        # citations_found entries
        citations = data.get("citations_found", [])
        for i, c in enumerate(citations):
            for key in ("text", "type", "position", "red_flags"):
                if key not in c:
                    errors.append(f"Citation [{i}] missing key: '{key}'")
            if "red_flags" in c and not isinstance(c["red_flags"], list):
                errors.append(f"Citation [{i}].red_flags must be a list")

        return {"valid": len(errors) == 0, "errors": errors}
