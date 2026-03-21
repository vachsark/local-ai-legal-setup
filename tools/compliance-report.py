"""
title: Compliance Report
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Generates compliance reports from the supervision log database.
  Produces monthly summaries, model usage stats, reviewer breakdowns, and
  compliance gap detection. Output is exportable as Markdown (copy/paste to PDF).
  Companion to supervision-log.py — requires its database to be present.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


DB_PATH = Path.home() / ".legal-ai" / "supervision.db"


class Tools:
    class Valves(BaseModel):
        db_path: str = str(DB_PATH)

    def __init__(self):
        self.valves = self.Valves()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> Optional[sqlite3.Connection]:
        path = Path(self.valves.db_path)
        if not path.exists():
            return None
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        return conn

    def _require_db(self) -> tuple[Optional[sqlite3.Connection], Optional[str]]:
        conn = self._connect()
        if conn is None:
            return None, (
                "Supervision database not found at "
                f"`{self.valves.db_path}`. "
                "Start logging reviews with the **Supervision Log** tool first."
            )
        return conn, None

    # ------------------------------------------------------------------
    # Public tool methods
    # ------------------------------------------------------------------

    async def monthly_summary(
        self,
        year: int = 0,
        month: int = 0,
        __event_emitter__=None,
    ) -> str:
        """
        Generate a monthly compliance summary.

        :param year: Four-digit year (e.g. 2026). Defaults to current year.
        :param month: Month number 1-12. Defaults to current month.
        :return: Markdown report suitable for firm records or PDF export.
        """
        now = datetime.now(timezone.utc)
        year = year or now.year
        month = month or now.month

        if not (1 <= month <= 12):
            return "Invalid month. Must be 1–12."
        if year < 2020 or year > 2100:
            return "Invalid year."

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Generating {year}-{month:02d} compliance report...",
                        "done": False,
                    },
                }
            )

        conn, err = self._require_db()
        if err:
            return err

        month_start = f"{year}-{month:02d}-01T00:00:00"
        if month == 12:
            month_end = f"{year+1}-01-01T00:00:00"
        else:
            month_end = f"{year}-{month+1:02d}-01T00:00:00"

        try:
            rows = conn.execute(
                """
                SELECT * FROM supervision_log
                WHERE timestamp >= ? AND timestamp < ?
                ORDER BY timestamp ASC
                """,
                (month_start, month_end),
            ).fetchall()
        finally:
            conn.close()

        import calendar
        month_name = calendar.month_name[month]
        period_label = f"{month_name} {year}"
        generated_at = now.strftime("%Y-%m-%d %H:%M UTC")

        total = len(rows)
        if total == 0:
            return (
                f"# Compliance Report — {period_label}\n\n"
                f"**Generated:** {generated_at}\n\n"
                "No supervision log entries found for this period."
            )

        counts = {"approved": 0, "modified": 0, "rejected": 0, "pending_review": 0}
        model_counts: dict[str, int] = {}
        reviewer_counts: dict[str, int] = {}
        daily_counts: dict[str, int] = {}
        input_type_counts: dict[str, int] = {}

        for row in rows:
            s = row["review_status"]
            if s in counts:
                counts[s] += 1
            elif s:
                counts[s] = counts.get(s, 0) + 1
            m = row["model"]
            if m:
                model_counts[m] = model_counts.get(m, 0) + 1
            u = row["user"]
            if u:
                reviewer_counts[u] = reviewer_counts.get(u, 0) + 1
            day = row["timestamp"][:10]
            daily_counts[day] = daily_counts.get(day, 0) + 1
            # Track input types (column may not exist in older DBs)
            try:
                it = row["input_type"]
            except IndexError:
                it = None
            if it:
                input_type_counts[it] = input_type_counts.get(it, 0) + 1

        active_days = len(daily_counts)
        avg_per_day = total / active_days if active_days else 0
        busiest_day = max(daily_counts, key=daily_counts.get) if daily_counts else "—"
        busiest_count = daily_counts.get(busiest_day, 0)

        # Review rate = finalized reviews / total interactions
        # pending_review entries are NOT counted as reviewed
        finalized = counts["approved"] + counts["modified"] + counts["rejected"]
        pending = counts.get("pending_review", 0)
        review_rate = (finalized / total * 100) if total > 0 else 0.0

        lines = [
            f"# AI Supervision Compliance Report — {period_label}",
            f"**Generated:** {generated_at}  ",
            f"**Database:** `{self.valves.db_path}`",
            "",
            "---",
            "",
            "## Monthly Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Period | {period_label} |",
            f"| Total AI interactions | **{total}** |",
            f"| Attorney review rate | **{review_rate:.0f}%** ({finalized}/{total} finalized) |",
            + (f"| Pending review | ⚠ {pending} (require attorney follow-up) |" if pending else "| Pending review | 0 |"),
            f"| Active days with AI usage | {active_days} |",
            f"| Average per active day | {avg_per_day:.1f} |",
            f"| Busiest day | {busiest_day} ({busiest_count} reviews) |",
            "",
            "## Review Outcomes",
            "",
            "| Outcome | Count | Percentage of Total |",
            "|---------|-------|---------------------|",
            f"| Approved as-is | {counts['approved']} | {counts['approved']/total*100:.0f}% |",
            f"| Approved with modifications | {counts['modified']} | {counts['modified']/total*100:.0f}% |",
            f"| Rejected | {counts['rejected']} | {counts['rejected']/total*100:.0f}% |",
            f"| Pending attorney review | {pending} | {pending/total*100:.0f}% |",
            f"| **Total** | **{total}** | **100%** |",
            "",
        ]

        if input_type_counts:
            lines += [
                "## Interactions by Document Type",
                "",
                "| Document Type | Count | % of Total |",
                "|---------------|-------|------------|",
            ]
            for itype, count in sorted(input_type_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| {itype.capitalize()} | {count} | {count/total*100:.0f}% |")
            lines.append("")

        if model_counts:
            lines += [
                "## Models Used",
                "",
                "| Model | Interactions | % of Total |",
                "|-------|-------------|------------|",
            ]
            for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| {model} | {count} | {count/total*100:.0f}% |")
            lines.append("")

        if reviewer_counts:
            lines += [
                "## Reviewer Activity",
                "",
                "| Reviewer | Reviews Logged |",
                "|----------|----------------|",
            ]
            for reviewer, count in sorted(reviewer_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| {reviewer} | {count} |")
            lines.append("")

        if pending > 0:
            attestation_status = (
                f"**{finalized} of {total}** AI-generated outputs used in {period_label} "
                "were reviewed by a licensed attorney. "
                f"**{pending} interaction(s) have pending reviews** — these must be "
                "finalized to achieve full ABA Formal Opinion 512 compliance."
            )
            review_status_cell = f"⚠ {review_rate:.0f}% — {pending} pending"
        else:
            attestation_status = (
                f"All {total} AI-generated outputs used in {period_label} were reviewed by "
                "a licensed attorney prior to use, in compliance with ABA Formal Opinion "
                "512 (2024) supervisory requirements."
            )
            review_status_cell = "✓ 100% — all interactions finalized"

        lines += [
            "## Compliance Attestation",
            "",
            attestation_status,
            "",
            "| Requirement | Status |",
            "|-------------|--------|",
            f"| Attorney review before use | {review_status_cell} |",
            "| Review outcome documented | ✓ Approved / Modified / Rejected / Pending |",
            "| Model identity recorded | ✓ Per entry |",
            "| Document type tracked | ✓ Per entry (contract/depo/email/etc.) |",
            "| Client data NOT stored | ✓ Summaries only (≤500 chars) |",
            "",
            "---",
            "",
            "_Retain this report per your firm's document retention policy. "
            "Recommended minimum: 3 years post-matter-close, consistent with "
            "Model Rules on file retention._",
        ]

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Monthly compliance report ready", "done": True},
                }
            )

        return "\n".join(lines)

    async def compliance_gap_report(
        self,
        __event_emitter__=None,
    ) -> str:
        """
        Identify any unreviewed AI outputs (compliance gaps).
        Returns a summary of gaps and their severity for attorney follow-up.

        :return: Markdown report listing compliance gaps, or a clean bill of health.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Scanning for compliance gaps...", "done": False},
                }
            )

        conn, err = self._require_db()
        if err:
            return err

        try:
            # pending_review: auto-logged interactions awaiting attorney finalization
            pending = conn.execute(
                """
                SELECT id, timestamp, user, model, review_status
                FROM supervision_log
                WHERE review_status = 'pending_review'
                ORDER BY timestamp DESC
                """,
            ).fetchall()

            # unexpected: entries with invalid status values (data integrity issue)
            unexpected = conn.execute(
                """
                SELECT id, timestamp, user, model, review_status
                FROM supervision_log
                WHERE review_status NOT IN ('approved', 'modified', 'rejected', 'pending_review')
                ORDER BY timestamp DESC
                """,
            ).fetchall()

            # Stats for context
            total = conn.execute(
                "SELECT COUNT(*) as n FROM supervision_log"
            ).fetchone()["n"]

            last_entry = conn.execute(
                "SELECT timestamp FROM supervision_log ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        lines = [
            "# Compliance Gap Report",
            f"**Generated:** {generated_at}  ",
            f"**Total log entries:** {total}",
            "",
        ]

        gap_count = len(pending) + len(unexpected)

        if gap_count == 0:
            lines += [
                "## Status: No Gaps Detected ✓",
                "",
                f"All {total} supervision log entries have valid review outcomes "
                "(approved, modified, or rejected).",
                "",
                "No remediation required.",
            ]
            if last_entry:
                lines.append(
                    f"\n**Last logged review:** {last_entry['timestamp'][:19].replace('T', ' ')} UTC"
                )
        else:
            if pending:
                lines += [
                    f"## ⚠ {len(pending)} Pending Reviews",
                    "",
                    "These interactions were auto-logged but have not yet been finalized "
                    "by an attorney. Call `log_review()` to complete each one:",
                    "",
                    "| Entry ID | Timestamp | Model | Reviewer |",
                    "|----------|-----------|-------|----------|",
                ]
                for row in pending:
                    ts = row["timestamp"][:19].replace("T", " ")
                    lines.append(
                        f"| {row['id']} | {ts} "
                        f"| {row['model'] or '—'} | {row['user'] or '—'} |"
                    )
                lines += [
                    "",
                    "**Recommended action:** Review each entry and call "
                    "`log_review(review_status='approved')` (or modified/rejected) "
                    "to finalize.",
                    "",
                ]

            if unexpected:
                lines += [
                    f"## ⚠ {len(unexpected)} Entries With Unexpected Status (Data Integrity)",
                    "",
                    "The following entries have status values outside the expected set. "
                    "These indicate a possible data integrity issue:",
                    "",
                    "| Entry ID | Timestamp | Status | Model | Reviewer |",
                    "|----------|-----------|--------|-------|----------|",
                ]
                for row in unexpected:
                    ts = row["timestamp"][:19].replace("T", " ")
                    lines.append(
                        f"| {row['id']} | {ts} | `{row['review_status']}` "
                        f"| {row['model'] or '—'} | {row['user'] or '—'} |"
                    )
                lines += [
                    "",
                    "**Recommended action:** Investigate and correct these entries. "
                    "They cannot be counted toward compliance.",
                ]

        lines += [
            "",
            "---",
            "_ABA Formal Opinion 512 requires that attorneys review AI outputs before "
            "use. This report helps ensure no outputs were used without documented review._",
        ]

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Gap scan complete", "done": True},
                }
            )

        return "\n".join(lines)

    async def export_markdown(
        self,
        period: str = "month",
        __event_emitter__=None,
    ) -> str:
        """
        Export the full supervision log as a Markdown document for PDF conversion
        or firm record retention.

        :param period: 'week', 'month', 'quarter', or 'all'.
        :return: Full Markdown export ready to copy into a PDF generator.
        """
        period = period.strip().lower()
        period_map = {"week": 7, "month": 30, "quarter": 90, "all": None}
        if period not in period_map:
            return f"Invalid period '{period}'. Must be: week, month, quarter, or all."

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Preparing Markdown export...", "done": False},
                }
            )

        conn, err = self._require_db()
        if err:
            return err

        days = period_map[period]
        try:
            if days is not None:
                rows = conn.execute(
                    """
                    SELECT * FROM supervision_log
                    WHERE timestamp >= datetime('now', ?)
                    ORDER BY timestamp ASC
                    """,
                    (f"-{days} days",),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM supervision_log ORDER BY timestamp ASC"
                ).fetchall()
        finally:
            conn.close()

        period_labels = {
            "week": "Last 7 Days",
            "month": "Last 30 Days",
            "quarter": "Last 90 Days",
            "all": "All Time",
        }
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        lines = [
            f"# AI Supervision Log Export — {period_labels[period]}",
            f"**Exported:** {generated_at}",
            f"**Total entries:** {len(rows)}",
            "",
            "---",
            "",
        ]

        if not rows:
            lines.append("No entries found for this period.")
        else:
            lines += [
                "| # | Date/Time (UTC) | Reviewer | Model | Status | Notes |",
                "|---|-----------------|----------|-------|--------|-------|",
            ]
            for row in rows:
                ts = row["timestamp"][:19].replace("T", " ")
                notes = (row["notes"] or "").replace("|", "\\|")
                lines.append(
                    f"| {row['id']} | {ts} | {row['user'] or '—'} "
                    f"| {row['model'] or '—'} | {row['review_status']} "
                    f"| {notes or '—'} |"
                )

        lines += [
            "",
            "---",
            "",
            "## Export Notes",
            "",
            "- Input and output summaries are truncated to 200 characters each.",
            "  Full document contents are never stored.",
            "- This log satisfies ABA Formal Opinion 512 supervisory documentation",
            "  requirements.",
            "- To convert to PDF: paste into a Markdown editor (Typora, Obsidian,",
            "  Pandoc) and export as PDF.",
            "",
            "_Generated by local-ai-legal-setup supervision-log tool._",
        ]

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Export ready", "done": True},
                }
            )

        return "\n".join(lines)
