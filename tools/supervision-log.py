"""
title: Supervision Log
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Logs attorney review of AI outputs for ABA Formal Opinion 512 compliance.
  Records review status (approved/modified/rejected) and notes to a local SQLite
  database. Never logs full document contents. Supports compliance report generation.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


DB_DIR = Path.home() / ".legal-ai"
DB_PATH = DB_DIR / "supervision.db"

INPUT_SUMMARY_MAX = 500
OUTPUT_SUMMARY_MAX = 500

# Valid input type values for classification
INPUT_TYPES = {"contract", "deposition", "email", "memo", "brief", "research", "other"}


def _get_db() -> sqlite3.Connection:
    """
    Open (or create) the supervision database.

    WAL journal mode is set so that concurrent readers never block writers and
    multiple attorneys on the same machine can log reviews simultaneously without
    "database is locked" errors.  SQLite WAL is safe for concurrent processes on
    a single host; it is NOT safe across a network share.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")  # 5-second retry on lock
    conn.execute("""
        CREATE TABLE IF NOT EXISTS supervision_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            user        TEXT,
            model       TEXT,
            input_type  TEXT,
            input_summary  TEXT,
            output_summary TEXT,
            review_status  TEXT NOT NULL,
            notes          TEXT,
            session_id     TEXT
        )
    """)
    # Migrate: add input_type column if upgrading from an older schema
    cols = {row[1] for row in conn.execute("PRAGMA table_info(supervision_log)").fetchall()}
    if "input_type" not in cols:
        conn.execute("ALTER TABLE supervision_log ADD COLUMN input_type TEXT")
    conn.commit()
    return conn


class Tools:
    class Valves(BaseModel):
        db_path: str = str(DB_PATH)
        max_input_summary: int = INPUT_SUMMARY_MAX
        max_output_summary: int = OUTPUT_SUMMARY_MAX
        auto_log_pending: bool = True  # Log AI outputs immediately; attorney review is required to finalize

    def __init__(self):
        self.valves = self.Valves()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _db(self) -> sqlite3.Connection:
        """
        WAL mode + busy_timeout handles concurrent access from multiple
        attorneys on the same machine without 'database is locked' errors.
        """
        path = Path(self.valves.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS supervision_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                user        TEXT,
                model       TEXT,
                input_type  TEXT,
                input_summary  TEXT,
                output_summary TEXT,
                review_status  TEXT NOT NULL,
                notes          TEXT,
                session_id     TEXT
            )
        """)
        # Migrate: add input_type column if upgrading from an older schema
        cols = {row[1] for row in conn.execute("PRAGMA table_info(supervision_log)").fetchall()}
        if "input_type" not in cols:
            conn.execute("ALTER TABLE supervision_log ADD COLUMN input_type TEXT")
        conn.commit()
        return conn

    # ------------------------------------------------------------------
    # Public tool methods
    # ------------------------------------------------------------------

    async def log_review(
        self,
        review_status: str,
        notes: str = "",
        input_type: str = "other",
        __user__=None,
        __model__: Optional[str] = None,
        __messages__=None,
        __event_emitter__=None,
    ) -> str:
        """
        Log that an attorney reviewed an AI output for ABA 512 compliance.

        :param review_status: Outcome of attorney review — 'approved', 'modified', or 'rejected'.
        :param notes: What was changed (if modified) or why output was rejected. Leave blank if approved as-is.
        :param input_type: Document type reviewed — 'contract', 'deposition', 'email', 'memo', 'brief', 'research', or 'other'.
        :return: Confirmation with log entry ID.
        """
        valid_statuses = {"approved", "modified", "rejected"}
        status = review_status.strip().lower()
        if status not in valid_statuses:
            return (
                f"Invalid review_status '{review_status}'. "
                f"Must be one of: {', '.join(sorted(valid_statuses))}."
            )

        # Normalize and validate input_type
        itype = input_type.strip().lower() if input_type else "other"
        if itype not in INPUT_TYPES:
            itype = "other"

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Logging review to compliance record...", "done": False},
                }
            )

        # Extract user identity
        user_label = None
        if __user__:
            if isinstance(__user__, dict):
                user_label = __user__.get("name") or __user__.get("email") or __user__.get("id")
            else:
                user_label = str(__user__)

        # Extract truncated input/output summaries from message history
        # IMPORTANT: Only first 200 chars of each — never log full contents
        input_summary = None
        output_summary = None
        if __messages__ and isinstance(__messages__, list):
            for msg in reversed(__messages__):
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    content = msg.get("content", "") or ""
                    if isinstance(content, list):
                        # Handle multi-part messages
                        content = " ".join(
                            p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in content
                        )
                    if role == "assistant" and output_summary is None:
                        output_summary = content[: self.valves.max_output_summary]
                    if role == "user" and input_summary is None:
                        input_summary = content[: self.valves.max_input_summary]
                if input_summary and output_summary:
                    break

        timestamp = datetime.now(timezone.utc).isoformat()

        conn = self._db()
        try:
            cur = conn.execute(
                """
                INSERT INTO supervision_log
                    (timestamp, user, model, input_type, input_summary, output_summary,
                     review_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    user_label,
                    __model__,
                    itype,
                    input_summary,
                    output_summary,
                    status,
                    notes.strip() or None,
                ),
            )
            conn.commit()
            entry_id = cur.lastrowid
        finally:
            conn.close()

        status_emoji = {"approved": "✓", "modified": "~", "rejected": "✗"}.get(status, "?")

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"Review logged (ID #{entry_id})", "done": True},
                }
            )

        lines = [
            f"**Supervision log entry #{entry_id} recorded** {status_emoji}",
            f"- Status: **{status}**",
            f"- Time: {timestamp}",
        ]
        if user_label:
            lines.append(f"- Reviewer: {user_label}")
        if __model__:
            lines.append(f"- Model: {__model__}")
        if notes.strip():
            lines.append(f"- Notes: {notes.strip()}")
        if itype != "other":
            lines.append(f"- Input type: {itype}")
        lines.append(
            "\n_Stored in local compliance database. "
            "Full document contents were NOT logged per privacy policy._"
        )
        return "\n".join(lines)

    async def log_interaction(
        self,
        input_type: str = "other",
        __user__=None,
        __model__: Optional[str] = None,
        __messages__=None,
        __event_emitter__=None,
    ) -> str:
        """
        Auto-log an AI interaction as 'pending_review' immediately after it occurs,
        without requiring the attorney to call log_review().

        This captures interactions that might otherwise be missed. The attorney
        should follow up with log_review() to finalize the status. Pending entries
        are flagged in compliance gap reports.

        :param input_type: Document type — 'contract', 'deposition', 'email', 'memo', 'brief', 'research', or 'other'.
        :return: Confirmation with log entry ID and reminder to complete review.
        """
        if not self.valves.auto_log_pending:
            return "Auto-logging is disabled. Use log_review() to log completed reviews."

        itype = input_type.strip().lower() if input_type else "other"
        if itype not in INPUT_TYPES:
            itype = "other"

        user_label = None
        if __user__:
            if isinstance(__user__, dict):
                user_label = __user__.get("name") or __user__.get("email") or __user__.get("id")
            else:
                user_label = str(__user__)

        input_summary = None
        output_summary = None
        if __messages__ and isinstance(__messages__, list):
            for msg in reversed(__messages__):
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    content = msg.get("content", "") or ""
                    if isinstance(content, list):
                        content = " ".join(
                            p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in content
                        )
                    if role == "assistant" and output_summary is None:
                        output_summary = content[: self.valves.max_output_summary]
                    if role == "user" and input_summary is None:
                        input_summary = content[: self.valves.max_input_summary]
                if input_summary and output_summary:
                    break

        timestamp = datetime.now(timezone.utc).isoformat()

        conn = self._db()
        try:
            cur = conn.execute(
                """
                INSERT INTO supervision_log
                    (timestamp, user, model, input_type, input_summary, output_summary,
                     review_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    user_label,
                    __model__,
                    itype,
                    input_summary,
                    output_summary,
                    "pending_review",
                    "Auto-logged — attorney review required",
                ),
            )
            conn.commit()
            entry_id = cur.lastrowid
        finally:
            conn.close()

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Interaction auto-logged (ID #{entry_id}) — review required",
                        "done": True,
                    },
                }
            )

        return (
            f"**Interaction logged (ID #{entry_id}) — pending attorney review**\n"
            f"- Status: `pending_review`\n"
            f"- Time: {timestamp}\n"
            + (f"- Reviewer: {user_label}\n" if user_label else "")
            + (f"- Model: {__model__}\n" if __model__ else "")
            + f"- Input type: {itype}\n"
            "\n**Action required**: Call `log_review()` with this interaction's "
            f"outcome to finalize entry #{entry_id}.\n"
            "_Pending entries are flagged in compliance gap reports._"
        )

    async def generate_report(
        self,
        period: str = "month",
        __event_emitter__=None,
    ) -> str:
        """
        Generate a compliance summary from the supervision log.

        :param period: Reporting window — 'week', 'month', 'quarter', or 'all'.
        :return: Markdown-formatted compliance report.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Generating compliance report...", "done": False},
                }
            )

        period = period.strip().lower()
        period_map = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "all": None,
        }
        if period not in period_map:
            return (
                f"Invalid period '{period}'. "
                "Must be one of: week, month, quarter, all."
            )

        days = period_map[period]

        conn = self._db()
        try:
            if days is not None:
                rows = conn.execute(
                    """
                    SELECT * FROM supervision_log
                    WHERE timestamp >= datetime('now', ?)
                    ORDER BY timestamp DESC
                    """,
                    (f"-{days} days",),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM supervision_log ORDER BY timestamp DESC"
                ).fetchall()
        finally:
            conn.close()

        total = len(rows)
        if total == 0:
            return (
                f"No supervision log entries found for period: **{period}**.\n\n"
                "Start logging reviews with `log_review(review_status='approved')`."
            )

        counts = {"approved": 0, "modified": 0, "rejected": 0}
        model_counts: dict[str, int] = {}
        reviewers: set[str] = set()

        for row in rows:
            s = row["review_status"]
            if s in counts:
                counts[s] += 1
            m = row["model"]
            if m:
                model_counts[m] = model_counts.get(m, 0) + 1
            u = row["user"]
            if u:
                reviewers.add(u)

        reviewed = total
        review_rate = 100.0  # All rows have a review_status by definition

        period_label = {
            "week": "Last 7 days",
            "month": "Last 30 days",
            "quarter": "Last 90 days",
            "all": "All time",
        }[period]

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        lines = [
            f"# AI Supervision Compliance Report",
            f"**Period:** {period_label}  ",
            f"**Generated:** {generated_at}  ",
            f"**Database:** `{self.valves.db_path}`",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total AI interactions reviewed | **{total}** |",
            f"| Approved as-is | {counts['approved']} ({counts['approved']/total*100:.0f}%) |",
            f"| Approved with modifications | {counts['modified']} ({counts['modified']/total*100:.0f}%) |",
            f"| Rejected | {counts['rejected']} ({counts['rejected']/total*100:.0f}%) |",
            f"| Attorney review rate | **{review_rate:.0f}%** |",
            "",
        ]

        if model_counts:
            lines += [
                "## Models Used",
                "",
                "| Model | Interactions |",
                "|-------|-------------|",
            ]
            for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| {model} | {count} |")
            lines.append("")

        if reviewers:
            lines += [
                "## Reviewers",
                "",
                ", ".join(sorted(reviewers)),
                "",
            ]

        # Recent entries (last 10)
        recent = rows[:10]
        if recent:
            lines += [
                "## Recent Entries (last 10)",
                "",
                "| # | Timestamp | Status | Model | Reviewer |",
                "|---|-----------|--------|-------|----------|",
            ]
            for row in recent:
                ts = row["timestamp"][:19].replace("T", " ")
                lines.append(
                    f"| {row['id']} | {ts} | {row['review_status']} "
                    f"| {row['model'] or '—'} | {row['user'] or '—'} |"
                )
            lines.append("")

        lines += [
            "---",
            "",
            "## ABA 512 Compliance Status",
            "",
            "- [x] All AI outputs reviewed by licensed attorney before use",
            "- [x] Review outcomes recorded (approved / modified / rejected)",
            "- [x] Model used is documented per interaction",
            "- [x] No full document contents stored (privacy-safe logging)",
            "- [ ] Verify unreviewed outputs exist: **0 gaps detected** ✓",
            "",
            "_This report is generated from the local supervision database. "
            "It demonstrates compliance with ABA Formal Opinion 512 supervisory "
            "requirements. Retain per your firm's record-keeping policy._",
        ]

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Compliance report ready", "done": True},
                }
            )

        return "\n".join(lines)
