"""
title: AI Time Savings Tracker
author: local-ai-legal-setup
version: 1.0.0
license: MIT
description: Estimates billable time saved by AI assistance based on the supervision log.
  Compares typical manual task durations against AI-assisted durations logged in
  the supervision record. Useful for demonstrating ROI and for ABA Rule 1.5 fee
  transparency documentation.

  Import into Open WebUI: Workspace → Tools → + → paste this file.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


DB_PATH = Path.home() / ".legal-ai" / "supervision.db"

# Estimated manual time (in minutes) for each task type — conservative estimates
# based on common legal workflow benchmarks. Adjust for your practice.
MANUAL_TIME_ESTIMATES: dict[str, float] = {
    "contract":   45.0,   # Contract clause review/analysis
    "deposition": 60.0,   # Deposition transcript review
    "email":       8.0,   # Professional email drafting
    "memo":       90.0,   # Legal memo drafting
    "brief":      120.0,  # Brief review/section drafting
    "research":   45.0,   # Research framework/organization
    "other":      20.0,   # General document tasks
}

# Estimated AI-assisted time (attorney review time after AI output)
AI_ASSISTED_TIME_ESTIMATES: dict[str, float] = {
    "contract":   10.0,
    "deposition": 12.0,
    "email":       2.0,
    "memo":       20.0,
    "brief":      25.0,
    "research":   10.0,
    "other":       5.0,
}


class Tools:
    class Valves(BaseModel):
        db_path: str = str(DB_PATH)
        hourly_rate: float = 300.0  # Default billing rate ($/hour) — update per attorney
        # Override time estimates (minutes) — leave 0 to use defaults
        manual_contract_min: float = 0.0
        manual_deposition_min: float = 0.0
        manual_email_min: float = 0.0
        manual_memo_min: float = 0.0

    def __init__(self):
        self.valves = self.Valves()

    def _connect(self) -> Optional[sqlite3.Connection]:
        path = Path(self.valves.db_path)
        if not path.exists():
            return None
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        return conn

    def _manual_time(self, input_type: str) -> float:
        """Return manual time estimate in minutes, respecting valve overrides."""
        overrides = {
            "contract":   self.valves.manual_contract_min,
            "deposition": self.valves.manual_deposition_min,
            "email":      self.valves.manual_email_min,
            "memo":       self.valves.manual_memo_min,
        }
        override = overrides.get(input_type, 0.0)
        if override > 0:
            return override
        return MANUAL_TIME_ESTIMATES.get(input_type, MANUAL_TIME_ESTIMATES["other"])

    async def time_savings_report(
        self,
        period: str = "month",
        __event_emitter__=None,
    ) -> str:
        """
        Estimate total attorney time saved by AI assistance based on the supervision log.

        Compares typical manual task durations to AI-assisted review times. Useful for
        ROI documentation and ABA Rule 1.5 fee transparency.

        :param period: Reporting window — 'week', 'month', 'quarter', or 'all'.
        :return: Markdown report with time savings and equivalent billing value.
        """
        period = period.strip().lower()
        period_map = {"week": 7, "month": 30, "quarter": 90, "all": None}
        if period not in period_map:
            return f"Invalid period '{period}'. Must be: week, month, quarter, or all."

        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Calculating time savings...", "done": False}}
            )

        conn = self._connect()
        if conn is None:
            return (
                f"Supervision database not found at `{self.valves.db_path}`. "
                "Start logging reviews with the **Supervision Log** tool first."
            )

        days = period_map[period]
        try:
            if days is not None:
                rows = conn.execute(
                    """
                    SELECT review_status, input_type FROM supervision_log
                    WHERE timestamp >= datetime('now', ?)
                    AND review_status IN ('approved', 'modified', 'rejected')
                    ORDER BY timestamp DESC
                    """,
                    (f"-{days} days",),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT review_status, input_type FROM supervision_log
                    WHERE review_status IN ('approved', 'modified', 'rejected')
                    ORDER BY timestamp DESC
                    """
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
        total = len(rows)

        if total == 0:
            return (
                f"# AI Time Savings Report — {period_labels[period]}\n\n"
                f"**Generated:** {generated_at}\n\n"
                "No finalized supervision log entries found for this period."
            )

        # Tally by input_type
        type_counts: dict[str, int] = {}
        total_manual_min = 0.0
        total_ai_min = 0.0

        for row in rows:
            itype = (row["input_type"] or "other").lower()
            if itype not in MANUAL_TIME_ESTIMATES:
                itype = "other"
            type_counts[itype] = type_counts.get(itype, 0) + 1
            total_manual_min += self._manual_time(itype)
            total_ai_min += AI_ASSISTED_TIME_ESTIMATES.get(itype, AI_ASSISTED_TIME_ESTIMATES["other"])

        saved_min = total_manual_min - total_ai_min
        saved_hr = saved_min / 60
        rate = self.valves.hourly_rate
        saved_value = saved_hr * rate

        lines = [
            f"# AI Time Savings Report — {period_labels[period]}",
            f"**Generated:** {generated_at}  ",
            f"**Billing rate used:** ${rate:.0f}/hour  ",
            f"_(Update in Tools → Time Savings Tracker → Valves → hourly_rate)_",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| AI-assisted tasks completed | **{total}** |",
            f"| Estimated manual time | {total_manual_min:.0f} min ({total_manual_min/60:.1f} hrs) |",
            f"| Estimated AI-assisted time | {total_ai_min:.0f} min ({total_ai_min/60:.1f} hrs) |",
            f"| **Time saved** | **{saved_min:.0f} min ({saved_hr:.1f} hrs)** |",
            f"| **Equivalent billing value** | **${saved_value:,.0f}** at ${rate:.0f}/hr |",
            "",
            "## Breakdown by Document Type",
            "",
            "| Type | Tasks | Manual Est. | AI Est. | Saved |",
            "|------|-------|-------------|---------|-------|",
        ]

        for itype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            manual = self._manual_time(itype) * count
            ai_t = AI_ASSISTED_TIME_ESTIMATES.get(itype, AI_ASSISTED_TIME_ESTIMATES["other"]) * count
            saved = manual - ai_t
            lines.append(
                f"| {itype.capitalize()} | {count} | {manual:.0f} min | {ai_t:.0f} min | {saved:.0f} min |"
            )

        lines += [
            "",
            "---",
            "",
            "## Methodology Notes",
            "",
            "Time estimates are conservative benchmarks based on typical legal task durations.",
            "Actual savings vary by task complexity, attorney familiarity, and document length.",
            "",
            "| Document Type | Manual Estimate | AI-Assisted Estimate |",
            "|---------------|-----------------|----------------------|",
        ]
        for itype, manual in MANUAL_TIME_ESTIMATES.items():
            ai_t = AI_ASSISTED_TIME_ESTIMATES[itype]
            lines.append(f"| {itype.capitalize()} | {manual:.0f} min | {ai_t:.0f} min |")

        lines += [
            "",
            "_Estimates can be customized in Valves. Only finalized interactions (approved/modified/rejected) are counted._",
            "_Pending reviews are excluded until finalized._",
            "",
            "---",
            "_Generated by local-ai-legal-setup time-tracker tool._",
        ]

        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Time savings report ready", "done": True}}
            )

        return "\n".join(lines)

    async def roi_summary(
        self,
        __event_emitter__=None,
    ) -> str:
        """
        Generate a one-line ROI summary for quick reference.

        :return: Brief summary of estimated time saved this month.
        """
        conn = self._connect()
        if conn is None:
            return "Supervision database not found. Start logging reviews first."

        try:
            rows = conn.execute(
                """
                SELECT input_type FROM supervision_log
                WHERE timestamp >= datetime('now', '-30 days')
                AND review_status IN ('approved', 'modified', 'rejected')
                """
            ).fetchall()
        finally:
            conn.close()

        total = len(rows)
        if total == 0:
            return "No finalized interactions found in the last 30 days."

        total_manual = sum(
            MANUAL_TIME_ESTIMATES.get((row["input_type"] or "other").lower(), 20.0)
            for row in rows
        )
        total_ai = sum(
            AI_ASSISTED_TIME_ESTIMATES.get((row["input_type"] or "other").lower(), 5.0)
            for row in rows
        )
        saved_hr = (total_manual - total_ai) / 60
        saved_value = saved_hr * self.valves.hourly_rate

        return (
            f"**Last 30 days**: {total} AI-assisted tasks → "
            f"~{saved_hr:.1f} hours saved (${saved_value:,.0f} at ${self.valves.hourly_rate:.0f}/hr). "
            "Run `time_savings_report()` for the full breakdown."
        )
