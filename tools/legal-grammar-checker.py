"""
title: Legal Grammar Checker
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Checks legal text for grammar and style issues using a local LanguageTool server. Returns structured results for the LLM to interpret in legal context.
requirements: httpx
"""

from pydantic import BaseModel, Field
from typing import Optional
import json


class Tools:
    class Valves(BaseModel):
        LANGUAGETOOL_URL: str = Field(
            default="http://localhost:8081/v2/check",
            description="URL of the local LanguageTool API endpoint",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def check_grammar(
        self,
        text: str,
        __event_emitter__=None,
    ) -> str:
        """
        Check legal text for grammar, spelling, and style issues using LanguageTool.
        Provide the text you want to check as the 'text' parameter.

        :param text: The legal text to check for grammar and style issues.
        :return: A structured list of issues found, or an error message.
        """
        import httpx

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Checking grammar with LanguageTool...",
                        "done": False,
                    },
                }
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.valves.LANGUAGETOOL_URL,
                    data={
                        "text": text,
                        "language": "en-US",
                        "enabledOnly": "false",
                    },
                )
                response.raise_for_status()
                result = response.json()
        except httpx.ConnectError:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "LanguageTool not available",
                            "done": True,
                        },
                    }
                )
            return (
                "LanguageTool server is not running. "
                "To use grammar checking, start the LanguageTool container:\n\n"
                "  docker run -d -p 127.0.0.1:8081:8010 --name languagetool "
                "--restart unless-stopped silviof/docker-languagetool\n\n"
                "Then try again."
            )
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Grammar check failed",
                            "done": True,
                        },
                    }
                )
            return f"Error contacting LanguageTool: {str(e)}"

        matches = result.get("matches", [])

        if not matches:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "No grammar issues found",
                            "done": True,
                        },
                    }
                )
            return "No grammar or style issues detected."

        issues = []
        for match in matches:
            context = match.get("context", {})
            replacements = match.get("replacements", [])
            suggestions = [r["value"] for r in replacements[:3]]

            issues.append(
                {
                    "message": match.get("message", ""),
                    "category": match.get("rule", {}).get("category", {}).get("name", "Unknown"),
                    "rule_id": match.get("rule", {}).get("id", ""),
                    "context": context.get("text", ""),
                    "offset": context.get("offset", 0),
                    "length": context.get("length", 0),
                    "suggestions": suggestions,
                }
            )

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Found {len(issues)} issue(s)",
                        "done": True,
                    },
                }
            )

        output = {
            "total_issues": len(issues),
            "issues": issues,
            "note": (
                "These are automated grammar/style suggestions. "
                "Legal terms of art, Latin phrases, and Bluebook citations "
                "may trigger false positives. Review each suggestion in context."
            ),
        }

        return json.dumps(output, indent=2)
