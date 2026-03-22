"""
title: Legal Readability Scorer
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Analyzes legal text readability using standard metrics (Flesch-Kincaid, Gunning Fog, SMOG) with legal-context interpretation bands.
requirements: textstat
"""

from pydantic import BaseModel
from typing import Optional
import json
import re


class Tools:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    async def score_readability(
        self,
        text: str,
        document_type: str = "auto",
        __event_emitter__=None,
    ) -> str:
        """
        Analyze the readability of legal text. Returns grade level scores,
        sentence statistics, and legal-context interpretation.

        :param text: The legal text to analyze for readability.
        :param document_type: Document type for target-band interpretation.
            Options: "brief" (appellate/court filing), "contract" (transactional),
            "client_letter" (advisory/demand letter), "consumer" (disclosures,
            plain-language summaries), "auto" (infer from grade level). Default: "auto".
        :return: Readability metrics with legal-context interpretation.
        """
        import textstat

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Analyzing readability...",
                        "done": False,
                    },
                }
            )

        # Core readability scores
        flesch_ease = textstat.flesch_reading_ease(text)
        flesch_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)
        smog = textstat.smog_index(text)
        coleman_liau = textstat.coleman_liau_index(text)
        ari = textstat.automated_readability_index(text)
        dale_chall = textstat.dale_chall_readability_score(text)

        # Sentence statistics
        sentences = textstat.sentence_count(text)
        words = textstat.lexicon_count(text, removepunct=True)
        avg_sentence_length = round(words / max(sentences, 1), 1)

        # Long sentences (>40 words)
        sentence_list = re.split(r'[.!?]+', text)
        sentence_list = [s.strip() for s in sentence_list if s.strip()]
        long_sentences = sum(
            1 for s in sentence_list
            if len(s.split()) > 40
        )

        # Passive voice estimate (simple heuristic)
        passive_patterns = re.findall(
            r'\b(?:is|are|was|were|be|been|being)\s+\w+(?:ed|en)\b',
            text,
            re.IGNORECASE,
        )
        passive_estimate = len(passive_patterns)
        passive_pct = round(
            (passive_estimate / max(sentences, 1)) * 100, 1
        )

        # Legal context interpretation
        avg_grade = round((flesch_grade + gunning_fog + smog) / 3, 1)

        # Document-type target bands
        # Source: plain-language guidelines, ABA readability research, CFPB consumer disclosure standards
        target_bands = {
            "brief": {
                "ideal_min": 14,
                "ideal_max": 18,
                "label": "Court Brief / Motion",
                "target_note": (
                    "Target: grade 14-18. Below 14 may appear unsophisticated for appellate work; "
                    "above 18 risks losing judicial readers. "
                    "Sentences over 40 words should be broken up."
                ),
            },
            "contract": {
                "ideal_min": 12,
                "ideal_max": 16,
                "label": "Contract / Transactional",
                "target_note": (
                    "Target: grade 12-16. Precision matters more than brevity, but "
                    "sentences over 50 words should be restructured into enumerated lists."
                ),
            },
            "client_letter": {
                "ideal_min": 10,
                "ideal_max": 14,
                "label": "Client Letter / Advisory",
                "target_note": (
                    "Target: grade 10-14. Educated non-lawyers should follow this. "
                    "Above grade 14, consider simplifying for the specific recipient."
                ),
            },
            "consumer": {
                "ideal_min": 6,
                "ideal_max": 10,
                "label": "Consumer Disclosure / Plain Language",
                "target_note": (
                    "Target: grade 6-10 (CFPB plain-language standard: 8th grade or below for consumer disclosures). "
                    "Above grade 10, rewrite for a general audience."
                ),
            },
        }

        # Auto-detect document type from grade level if not specified
        effective_type = document_type.lower().strip()
        if effective_type == "auto" or effective_type not in target_bands:
            if avg_grade >= 16:
                effective_type = "brief"
            elif avg_grade >= 12:
                effective_type = "contract"
            elif avg_grade >= 9:
                effective_type = "client_letter"
            else:
                effective_type = "consumer"

        band = target_bands.get(effective_type)
        if band:
            if avg_grade < band["ideal_min"]:
                target_status = f"BELOW TARGET — may appear unsophisticated for a {band['label']} (target: grade {band['ideal_min']}-{band['ideal_max']})"
            elif avg_grade > band["ideal_max"]:
                target_status = f"ABOVE TARGET — too dense for a {band['label']} (target: grade {band['ideal_min']}-{band['ideal_max']})"
            else:
                target_status = f"ON TARGET for a {band['label']} (target: grade {band['ideal_min']}-{band['ideal_max']})"
            target_note = band["target_note"]
        else:
            target_status = None
            target_note = None

        if avg_grade >= 18:
            interpretation = "Academic/Scholarly"
            recommendation = (
                "Very dense. Appropriate for law review articles or appellate briefs "
                "to sophisticated courts. Consider simplifying for broader audiences."
            )
        elif avg_grade >= 16:
            interpretation = "Legal Brief / Judicial Opinion"
            recommendation = (
                "Typical for briefs, motions, and judicial opinions. "
                "Readable by attorneys and judges but may challenge non-lawyers."
            )
        elif avg_grade >= 14:
            interpretation = "Complex Professional"
            recommendation = (
                "Appropriate for contracts and transactional documents. "
                "Clients with business experience can follow this."
            )
        elif avg_grade >= 12:
            interpretation = "Business Communication"
            recommendation = (
                "Good level for demand letters, settlement communications, "
                "and client advisories. Clear to educated non-lawyers."
            )
        elif avg_grade >= 10:
            interpretation = "Client-Friendly"
            recommendation = (
                "Excellent readability for client letters, FAQs, and plain-language "
                "summaries. Most adults can follow this easily."
            )
        else:
            interpretation = "General Public"
            recommendation = (
                "Very accessible. Good for consumer-facing disclosures, "
                "website terms written in plain language, or public notices."
            )

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Readability analysis complete",
                        "done": True,
                    },
                }
            )

        legal_interpretation = {
            "category": interpretation,
            "recommendation": recommendation,
        }
        if target_status:
            legal_interpretation["document_type_target"] = target_status
        if target_note:
            legal_interpretation["document_type_guidance"] = target_note

        output = {
            "readability_scores": {
                "flesch_reading_ease": flesch_ease,
                "flesch_kincaid_grade": flesch_grade,
                "gunning_fog_index": gunning_fog,
                "smog_index": smog,
                "coleman_liau_index": coleman_liau,
                "automated_readability_index": ari,
                "dale_chall_score": dale_chall,
                "average_grade_level": avg_grade,
            },
            "sentence_statistics": {
                "total_sentences": sentences,
                "total_words": words,
                "average_sentence_length": avg_sentence_length,
                "long_sentences_over_40_words": long_sentences,
                "estimated_passive_voice_instances": passive_estimate,
                "passive_voice_pct_of_sentences": passive_pct,
            },
            "legal_interpretation": legal_interpretation,
            "reference_bands": {
                "grade_18_plus": "Academic / Law review",
                "grade_16_17": "Briefs / Judicial opinions",
                "grade_14_15": "Contracts / Transactional",
                "grade_12_13": "Business letters / Advisories",
                "grade_10_11": "Client letters / Plain-language summaries",
                "grade_below_10": "Consumer disclosures / Public notices",
            },
        }

        return json.dumps(output, indent=2)

    def validate_output(self, json_str: str) -> dict:
        """
        Validate that score_readability output conforms to the expected schema.

        Returns {"valid": True} on success, or {"valid": False, "errors": [...]} listing
        every missing key so callers can catch schema drift early.
        """
        errors = []
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as exc:
            return {"valid": False, "errors": [f"JSON parse error: {exc}"]}

        required_top = {"readability_scores", "sentence_statistics", "legal_interpretation", "reference_bands"}
        for key in required_top:
            if key not in data:
                errors.append(f"Missing top-level key: '{key}'")

        if "readability_scores" in data:
            required_scores = {
                "flesch_reading_ease",
                "flesch_kincaid_grade",
                "gunning_fog_index",
                "smog_index",
                "coleman_liau_index",
                "automated_readability_index",
                "dale_chall_score",
                "average_grade_level",
            }
            for key in required_scores:
                if key not in data["readability_scores"]:
                    errors.append(f"Missing readability_scores key: '{key}'")

        if "sentence_statistics" in data:
            required_stats = {
                "total_sentences",
                "total_words",
                "average_sentence_length",
                "long_sentences_over_40_words",
                "estimated_passive_voice_instances",
            }
            for key in required_stats:
                if key not in data["sentence_statistics"]:
                    errors.append(f"Missing sentence_statistics key: '{key}'")

        return {"valid": len(errors) == 0} if not errors else {"valid": False, "errors": errors}
