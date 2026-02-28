"""
title: AI Disclaimer
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Appends a configurable disclaimer to AI-generated legal output. Addresses ABA Rules 3.3 (candor to tribunals) and 1.4 (communication with clients). Ensures all AI-generated text is clearly marked for attorney review.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


class Tools:
    class Valves(BaseModel):
        disclaimer_text: str = (
            "AI-GENERATED DRAFT — Requires attorney review. "
            "All citations, legal standards, and factual claims "
            "must be independently verified."
        )
        include_timestamp: bool = True
        include_model_name: bool = True

    def __init__(self):
        self.valves = self.Valves()

    async def add_disclaimer(
        self,
        text: str,
        __model__: Optional[str] = None,
        __event_emitter__=None,
    ) -> str:
        """
        Append an ABA-compliant disclaimer to AI-generated legal text.
        Marks the output as AI-generated and requiring attorney verification.

        :param text: The AI-generated text to add a disclaimer to.
        :return: The original text with a disclaimer appended.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Adding disclaimer...",
                        "done": False,
                    },
                }
            )

        if not text or not text.strip():
            return text

        # Build disclaimer
        parts = [self.valves.disclaimer_text]

        if self.valves.include_model_name and __model__:
            parts.append(f"Model: {__model__}")

        if self.valves.include_timestamp:
            timestamp = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            )
            parts.append(f"Generated: {timestamp}")

        disclaimer = "\n".join(parts)
        separator = "\n\n" + "=" * 60 + "\n"

        result = text.rstrip() + separator + disclaimer + "\n"

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Disclaimer added",
                        "done": True,
                    },
                }
            )

        return result
