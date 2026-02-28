"""
title: Contract Comparator
author: local-ai-legal-setup
version: 0.1.0
license: MIT
description: Compares two uploaded legal documents and produces a structured diff summary. Upload two files and the tool highlights additions, deletions, and modifications for the LLM to interpret.
"""

from pydantic import BaseModel
from typing import Optional
import json
import difflib


class Tools:
    class Valves(BaseModel):
        max_diff_lines: int = 500

    def __init__(self):
        self.valves = self.Valves()

    async def compare_documents(
        self,
        __files__: Optional[list] = None,
        __event_emitter__=None,
    ) -> str:
        """
        Compare two uploaded legal documents and produce a structured diff.
        Upload exactly two files (text or PDF) to compare.

        :return: A summary of differences with similarity score and detailed diff.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Comparing documents...",
                        "done": False,
                    },
                }
            )

        if not __files__ or len(__files__) < 2:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Need 2 files to compare",
                            "done": True,
                        },
                    }
                )
            return (
                "Please upload exactly 2 files to compare. "
                "Attach them to your message using the paperclip icon, "
                "then ask me to compare them."
            )

        # Extract text from the first two files
        file1 = __files__[0]
        file2 = __files__[1]

        try:
            text1 = self._extract_text(file1)
            text2 = self._extract_text(file2)
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Failed to read files",
                            "done": True,
                        },
                    }
                )
            return f"Error reading files: {str(e)}"

        name1 = file1.get("filename", file1.get("name", "Document 1"))
        name2 = file2.get("filename", file2.get("name", "Document 2"))

        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)

        # Compute similarity ratio
        matcher = difflib.SequenceMatcher(None, text1, text2)
        similarity = round(matcher.ratio() * 100, 1)

        # Generate unified diff
        diff = list(
            difflib.unified_diff(
                lines1,
                lines2,
                fromfile=name1,
                tofile=name2,
                lineterm="",
            )
        )

        # Count additions and deletions
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        # Cap diff output to protect context window
        max_lines = self.valves.max_diff_lines
        diff_truncated = len(diff) > max_lines
        diff_output = diff[:max_lines]

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Comparison complete ({similarity}% similar)",
                        "done": True,
                    },
                }
            )

        output = {
            "summary": {
                "document_1": name1,
                "document_2": name2,
                "similarity_pct": similarity,
                "lines_added": additions,
                "lines_deleted": deletions,
                "total_diff_lines": len(diff),
                "diff_truncated": diff_truncated,
            },
            "diff": "\n".join(diff_output),
            "note": (
                "This is a text-level comparison. The LLM should interpret the legal "
                "significance of each change — whether it shifts obligations, alters "
                "risk allocation, modifies defined terms, or affects enforceability."
            ),
        }

        return json.dumps(output, indent=2)

    def _extract_text(self, file_obj: dict) -> str:
        """Extract text content from a file object."""
        # Open WebUI provides file content in different ways depending on version
        # Try common patterns
        if "content" in file_obj:
            return file_obj["content"]
        if "data" in file_obj and isinstance(file_obj["data"], dict):
            content = file_obj["data"].get("content", "")
            if content:
                return content
        if "data" in file_obj and isinstance(file_obj["data"], str):
            return file_obj["data"]
        # If we get a path, read it
        if "path" in file_obj:
            with open(file_obj["path"], "r", errors="replace") as f:
                return f.read()
        raise ValueError(
            f"Could not extract text from file: {file_obj.get('filename', file_obj.get('name', 'unknown'))}"
        )
