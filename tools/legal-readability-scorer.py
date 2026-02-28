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
        __event_emitter__=None,
    ) -> str:
        """
        Analyze the readability of legal text. Returns grade level scores,
        sentence statistics, and legal-context interpretation.

        :param text: The legal text to analyze for readability.
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
            "legal_interpretation": {
                "category": interpretation,
                "recommendation": recommendation,
            },
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
