"""
Forensic report generator for AutoDecodeX.

Produces:
  - JSON report (canonical machine-readable representation)
  - PDF report (derived from the same ForensicReport data)

Security notes:
  - Untrusted extracted content is NEVER rendered as executable HTML.
  - Large payloads are replaced with hashes and byte-count summaries.
  - No raw credentials, secrets, or full binary payloads are included by default.
  - PDF text is escaped before embedding.

PDF dependency: fpdf2 (fpdf2 >= 2.7.0)
If fpdf2 is not installed, JSON export remains available and the PDF
endpoint returns a 503 with an installation hint.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Optional

from backend.models.schemas import ForensicReport, FindingStatus, Severity

# Maximum characters of any extracted/observed value included in a report
_MAX_VALUE_CHARS = 500

# ── JSON export ────────────────────────────────────────────────────────────

def report_to_json(report: ForensicReport, indent: int = 2) -> str:
    """
    Serialise the report to a JSON string.
    Observed values are truncated to _MAX_VALUE_CHARS.
    The underlying JSON is the canonical record; it drives the PDF.
    """
    data = report.model_dump()
    _truncate_values(data)
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def _truncate_values(obj):
    """Recursively truncate long string values so reports stay manageable."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and len(v) > _MAX_VALUE_CHARS:
                obj[k] = v[:_MAX_VALUE_CHARS] + f"... [truncated, total {len(v)} chars]"
            else:
                _truncate_values(v)
    elif isinstance(obj, list):
        for item in obj:
            _truncate_values(item)


# ── PDF export ─────────────────────────────────────────────────────────────

def report_to_pdf(report: ForensicReport) -> bytes:
    """
    Generate a PDF from the ForensicReport.
    Returns raw PDF bytes.
    Raises ImportError if fpdf2 is not installed.
    All text is escaped before embedding to prevent injection.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError(
            "fpdf2 is required for PDF generation. "
            "Install it with: pip install fpdf2"
        )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Header ──────────────────────────────────────────────────────────
    _h1(pdf, "AutoDecodeX Forensic Report")
    _field(pdf, "Report ID", report.report_id)
    _field(pdf, "Case ID", report.case_id)
    _field(pdf, "Generated (UTC)", report.generated_at_utc)
    _field(pdf, "App Version", report.app_version)
    _field(pdf, "Engine Version", report.engine_version)
    _spacer(pdf)

    # ── Evidence ─────────────────────────────────────────────────────────
    _h2(pdf, "Evidence Summary")
    _field(pdf, "Filename", report.original_filename)
    _field(pdf, "Size", f"{report.file_size_bytes:,} bytes")
    _field(pdf, "Detected Format", report.detected_format or "Unknown")
    _field(pdf, "SHA-256", report.sha256)
    _field(pdf, "MD5 (non-cryptographic ID)", report.md5)
    _spacer(pdf)

    # ── Scope ─────────────────────────────────────────────────────────────
    _h2(pdf, "Scope of Analysis")
    _para(pdf, _safe(report.scope_statement))
    _spacer(pdf)

    # ── Modules ───────────────────────────────────────────────────────────
    _h2(pdf, "Analysis Modules")
    _field(pdf, "Completed", ", ".join(report.modules_run) if report.modules_run else "none")
    _field(pdf, "Failed", ", ".join(report.modules_failed) if report.modules_failed else "none")
    _spacer(pdf)

    # ── Verified Observations ─────────────────────────────────────────────
    if report.verified_observations:
        _h2(pdf, "Verified Observations")
        for obs in report.verified_observations:
            _bullet(pdf, _safe(obs))
        _spacer(pdf)

    # ── Analyst Interpretations ───────────────────────────────────────────
    if report.analyst_interpretations:
        _h2(pdf, "Indicators Requiring Investigation")
        for interp in report.analyst_interpretations:
            _bullet(pdf, _safe(interp))
        _spacer(pdf)

    # ── Findings ──────────────────────────────────────────────────────────
    _h2(pdf, f"Findings ({len(report.findings)})")
    for idx, f in enumerate(report.findings, 1):
        _h3(pdf, f"{idx}. [{_severity_label(f.severity)}] {_safe(f.title)}")
        _field(pdf, "Category", f.category)
        _field(pdf, "Status", f.status.value)
        _field(pdf, "Summary", _safe(f.summary))
        _field(pdf, "Method", f.detection_method)
        if f.observed_value:
            _field(pdf, "Observed", _safe(f.observed_value[:_MAX_VALUE_CHARS]))
        _field(pdf, "Explanation", _safe(f.explanation))
        _field(pdf, "Limitations", _safe(f.limitations))
        if f.recommended_next_step:
            _field(pdf, "Next Step", _safe(f.recommended_next_step))
        _spacer(pdf)

    # ── Correlations ──────────────────────────────────────────────────────
    if report.correlations:
        _h2(pdf, f"Correlation Rules ({len(report.correlations)})")
        for idx, c in enumerate(report.correlations, 1):
            _h3(pdf, f"{idx}. [{c.rule_id}] {_safe(c.rule_description[:80])}")
            _field(pdf, "Status", c.status.value)
            _field(pdf, "Severity", c.severity.value)
            _field(pdf, "Why Triggered", _safe(c.match_reason))
            _field(pdf, "Supporting Evidence", _safe(c.supporting_evidence))
            _field(pdf, "Does NOT Prove", _safe(c.what_this_does_not_prove))
            _field(pdf, "Next Step", _safe(c.next_step))
            _spacer(pdf)

    # ── Transformation Graph ──────────────────────────────────────────────
    if report.transformation_graph:
        _h2(pdf, f"Decoding Transformation Graph ({len(report.transformation_graph)} steps)")
        for step in report.transformation_graph:
            _bullet(
                pdf,
                f"Depth {step.recursion_depth}: {step.decoder_name} | "
                f"{step.input_size_bytes}B → {step.output_size_bytes}B | "
                f"{step.duration_ms:.1f}ms | {step.status}"
            )
        _spacer(pdf)

    # ── Artifacts ────────────────────────────────────────────────────────
    if report.artifacts:
        _h2(pdf, f"Evidence Artifacts ({len(report.artifacts)})")
        for art in report.artifacts:
            _bullet(
                pdf,
                f"[{art.kind.value}] {_safe(art.filename)} | "
                f"{art.size_bytes:,}B | SHA-256: {art.sha256[:16]}..."
                + (f" | parent: {art.parent_artifact_id[:8]}..." if art.parent_artifact_id else "")
            )
        _spacer(pdf)

    # ── Errors & Warnings ────────────────────────────────────────────────
    if report.errors:
        _h2(pdf, "Errors")
        for e in report.errors:
            _bullet(pdf, _safe(str(e)))
        _spacer(pdf)

    if report.warnings:
        _h2(pdf, "Warnings")
        for w in report.warnings:
            _bullet(pdf, _safe(str(w)))
        _spacer(pdf)

    # ── Limitations ──────────────────────────────────────────────────────
    _h2(pdf, "Known Limitations")
    for lim in report.limitations:
        _bullet(pdf, _safe(lim))
    _spacer(pdf)

    # ── Final Summary ─────────────────────────────────────────────────────
    _h2(pdf, "Final Summary")
    _para(pdf, _safe(report.final_summary))

    return bytes(pdf.output())


# ── PDF helpers ────────────────────────────────────────────────────────────

def _safe(text: str) -> str:
    """Escape text for safe embedding in PDF. No HTML/active content."""
    if not text:
        return ""
    # Replace control characters, keep printable
    cleaned = "".join(c if (32 <= ord(c) <= 126) or c in "\n\r\t" else "?" for c in str(text))
    return cleaned


def _h1(pdf, text: str):
    pdf.set_font("Helvetica", "B", 16)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(w, 10, _safe(text)[:80])
    pdf.set_font("Helvetica", "", 10)


def _h2(pdf, text: str):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(230, 230, 230)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(w, 8, _safe(text)[:100], fill=True)
    pdf.set_font("Helvetica", "", 10)


def _h3(pdf, text: str):
    pdf.set_font("Helvetica", "B", 10)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(w, 7, _safe(text)[:100])
    pdf.set_font("Helvetica", "", 10)


def _field(pdf, label: str, value: str):
    pdf.set_font("Helvetica", "B", 9)
    safe_value = _safe(str(value))[:150].replace("\n", " ")
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(w, 6, f"{label}: {safe_value}")
    pdf.set_font("Helvetica", "", 9)


def _bullet(pdf, text: str):
    pdf.set_font("Helvetica", "", 9)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(w, 6, f"  - {_safe(text)[:180]}")


def _para(pdf, text: str):
    pdf.set_font("Helvetica", "", 10)
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(w, 6, _safe(text)[:1500])


def _spacer(pdf):
    pdf.ln(3)


def _severity_label(severity: Severity) -> str:
    MAP = {
        Severity.INFORMATIONAL: "INFO",
        Severity.LOW: "LOW",
        Severity.MEDIUM: "MED",
        Severity.HIGH: "HIGH",
        Severity.CRITICAL: "CRIT",
    }
    return MAP.get(severity, str(severity))
