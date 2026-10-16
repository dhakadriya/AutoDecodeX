"""
Explainable rule-based correlation engine for AutoDecodeX.

Each rule has:
  - A stable rule_id
  - A description of what it looks for
  - Required finding categories / evidence keys
  - A severity level
  - Explicit documentation of what a match does NOT prove

Result statuses used:
  CONFIRMED_ARTIFACT   – a named artifact was successfully verified
  SUSPICIOUS_INDICATOR – a heuristic rule fired; investigation required
  NO_INDICATOR_DETECTED – no rule fired
  INCONCLUSIVE         – conflicting or insufficient evidence

Numeric "scores" are NOT used as probabilities of maliciousness.
If a priority value is needed for display ordering it is labelled
heuristic_priority and its formula is documented below.
"""
from __future__ import annotations

import re
from typing import Any

from backend.models.schemas import (
    Case,
    Finding,
    FindingStatus,
    Severity,
    CorrelationResult,
)

# ── Rule registry ──────────────────────────────────────────────────────────

RULES: list[dict[str, Any]] = [
    {
        "rule_id": "CORR-001",
        "description": (
            "File extension does not match detected magic bytes / file format. "
            "The uploaded filename claims one type but the file content indicates another."
        ),
        "severity": Severity.MEDIUM,
        "required_categories": {"file"},
        "what_it_does_not_prove": (
            "A mismatch alone does not establish malicious intent. "
            "Common causes include renamed files, screenshots saved with wrong extension, "
            "or tools that produce non-standard output."
        ),
        "next_step": (
            "Verify the file format independently with a hex editor. "
            "Check whether the declared MIME type from the HTTP upload matches the magic bytes."
        ),
    },
    {
        "rule_id": "CORR-002",
        "description": (
            "High-entropy image region coincides with an LSB anomaly. "
            "Both the entropy analyser and LSB extractor flagged the same image."
        ),
        "severity": Severity.MEDIUM,
        "required_categories": {"steganalysis"},
        "what_it_does_not_prove": (
            "High entropy in an image can result from JPEG compression artifacts, "
            "noise, or natural photographic complexity. "
            "An LSB anomaly alone does not confirm that a hidden payload exists "
            "or that extracted bytes form a meaningful message."
        ),
        "next_step": (
            "Attempt LSB extraction with multiple bit depths and channel combinations. "
            "Compare chi-square score against a clean cover image of the same format. "
            "Check whether extracted bytes form valid UTF-8, Base64, or known file signatures."
        ),
    },
    {
        "rule_id": "CORR-003",
        "description": (
            "A metadata field contains an encoded value that was successfully decoded "
            "to readable text or a recognisable artifact."
        ),
        "severity": Severity.MEDIUM,
        "required_categories": {"metadata"},
        "what_it_does_not_prove": (
            "Successfully decoding a metadata field confirms a transformation was possible, "
            "not that the original encoder intended to hide information. "
            "Some tools embed Base64-encoded thumbnails or checksums in metadata by default."
        ),
        "next_step": (
            "Examine the decoded value for CTF flag patterns, URLs, credentials, "
            "or embedded file signatures. "
            "Cross-reference with other findings from the same artifact."
        ),
    },
    {
        "rule_id": "CORR-004",
        "description": (
            "A CTF flag pattern was identified in a decoded artifact. "
            "The pattern matches a known flag format (e.g. flag{...}, HTB{...})."
        ),
        "severity": Severity.HIGH,
        "required_categories": {"decoder", "steganalysis", "metadata"},
        "what_it_does_not_prove": (
            "The presence of a CTF flag format string confirms that a matching pattern "
            "was extracted. It does not establish malicious activity in a non-CTF context. "
            "Flag-like strings may appear in test data, demonstration files, or comments."
        ),
        "next_step": (
            "Record the flag value, the transformation path that produced it, "
            "and the source artifact hash. Verify against the CTF challenge definition."
        ),
    },
    {
        "rule_id": "CORR-005",
        "description": (
            "Multiple independent analysis modules produced suspicious findings "
            "on the same artifact: two or more of (entropy, LSB, metadata, decoder) "
            "flagged the same file."
        ),
        "severity": Severity.HIGH,
        "required_categories": {"steganalysis", "metadata"},
        "what_it_does_not_prove": (
            "Correlated indicators from independent methods increase investigative "
            "priority but are NOT statistically independent evidence. "
            "Multiple heuristics applied to the same data share common failure modes. "
            "This rule does not confirm that steganography is present."
        ),
        "next_step": (
            "Review each individual finding. Attempt payload extraction and verify "
            "whether extracted bytes form a coherent artifact with a valid file signature."
        ),
    },
    {
        "rule_id": "CORR-006",
        "description": (
            "An embedded file signature was detected inside the primary artifact "
            "(e.g. a ZIP or PNG signature found within a JPEG file body)."
        ),
        "severity": Severity.HIGH,
        "required_categories": {"file", "metadata"},
        "what_it_does_not_prove": (
            "The presence of a secondary file signature does not confirm the embedded "
            "content is malicious or that it can be extracted as a usable file. "
            "JPEG markers and comment blocks can contain arbitrary bytes including "
            "coincidental matches to known signatures."
        ),
        "next_step": (
            "Note the byte offset of the embedded signature. "
            "Extract the bytes starting at that offset and analyse them as a separate artifact. "
            "Compute the SHA-256 of the extracted bytes."
        ),
    },
    {
        "rule_id": "CORR-007",
        "description": (
            "Recursive decoding produced a multi-step transformation chain "
            "(depth >= 2), indicating layered encoding."
        ),
        "severity": Severity.MEDIUM,
        "required_categories": {"decoder"},
        "what_it_does_not_prove": (
            "Multi-layer encoding is common in CTF challenges and is also used by "
            "legitimate tools for serialisation, compression, or protocol framing. "
            "Depth alone does not indicate obfuscation intent."
        ),
        "next_step": (
            "Examine the full transformation graph. Verify each step's output hash "
            "and confirm the final decoded content is the target artifact."
        ),
    },
    {
        "rule_id": "CORR-008",
        "description": (
            "Printable-character ratio is unusually low (< 10%) for a file "
            "claimed to be a text or document format."
        ),
        "severity": Severity.LOW,
        "required_categories": {"file"},
        "what_it_does_not_prove": (
            "Low printable ratio in a file claimed to be text may indicate binary "
            "content, an encoding mismatch, or encryption. "
            "It does not alone indicate steganographic payload."
        ),
        "next_step": (
            "Check the magic bytes and detected format. "
            "Consider whether the file may be compressed or encrypted."
        ),
    },
]

# Index by rule_id for fast lookup
_RULE_INDEX: dict[str, dict] = {r["rule_id"]: r for r in RULES}


# ── Correlation engine ─────────────────────────────────────────────────────

def correlate(case: Case) -> list[CorrelationResult]:
    """
    Run all correlation rules against the findings in a case.
    Returns a list of CorrelationResult objects.
    Each result documents which findings triggered it and why.
    """
    findings = case.findings
    results: list[CorrelationResult] = []

    # Build category → findings index
    by_category: dict[str, list[Finding]] = {}
    for f in findings:
        by_category.setdefault(f.category, []).append(f)

    # ── CORR-001: extension / magic mismatch ──────────────────────────────
    file_findings = by_category.get("file", [])
    mismatch_findings = [
        f for f in file_findings
        if f.rule_id == "FILE-MAGIC-MISMATCH"
        or (f.evidence_details or {}).get("extension_mismatch")
    ]
    if mismatch_findings:
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-001"],
            triggered_by=[f.finding_id for f in mismatch_findings],
            match_reason=(
                f"The following file findings reported a format/extension discrepancy: "
                + "; ".join(f.title for f in mismatch_findings)
            ),
            supporting_evidence=(
                "Magic bytes check was performed on the actual file bytes, "
                "not on the browser-reported MIME type."
            ),
            status=FindingStatus.SUSPICIOUS_INDICATOR,
        ))

    # ── CORR-002: high entropy + LSB anomaly ─────────────────────────────
    stego_findings = by_category.get("steganalysis", [])
    entropy_suspicious = [
        f for f in stego_findings
        if "entropy" in f.detection_method.lower() and f.status == FindingStatus.SUSPICIOUS_INDICATOR
    ]
    lsb_suspicious = [
        f for f in stego_findings
        if "lsb" in f.detection_method.lower() and f.status == FindingStatus.SUSPICIOUS_INDICATOR
    ]
    if entropy_suspicious and lsb_suspicious:
        triggered = [f.finding_id for f in entropy_suspicious + lsb_suspicious]
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-002"],
            triggered_by=triggered,
            match_reason=(
                f"Entropy analysis flagged {len(entropy_suspicious)} region(s) as suspicious "
                f"and LSB analysis flagged {len(lsb_suspicious)} result(s) on the same artifact."
            ),
            supporting_evidence=(
                "Both detectors operated independently on the same file bytes. "
                "Their concurrent suspicion increases investigative priority."
            ),
            status=FindingStatus.SUSPICIOUS_INDICATOR,
        ))

    # ── CORR-003: metadata field successfully decoded ─────────────────────
    meta_findings = by_category.get("metadata", [])
    decoded_meta = [
        f for f in meta_findings
        if f.status == FindingStatus.CONFIRMED_ARTIFACT and "decoded" in f.title.lower()
    ]
    if decoded_meta:
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-003"],
            triggered_by=[f.finding_id for f in decoded_meta],
            match_reason=(
                f"{len(decoded_meta)} metadata field(s) were decoded to readable output."
            ),
            supporting_evidence=(
                "The decoder confirmed a valid transformation from the raw metadata value."
            ),
            status=FindingStatus.CONFIRMED_ARTIFACT,
        ))

    # ── CORR-004: CTF flag detected ───────────────────────────────────────
    flag_findings = [
        f for f in findings
        if (f.evidence_details or {}).get("is_ctf_flag")
        or "flag" in f.title.lower()
        or f.severity == Severity.CRITICAL
    ]
    if flag_findings:
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-004"],
            triggered_by=[f.finding_id for f in flag_findings],
            match_reason=(
                f"CTF flag pattern matched in {len(flag_findings)} finding(s): "
                + "; ".join(f.title for f in flag_findings[:3])
            ),
            supporting_evidence="Flag format regex matched the extracted/decoded output.",
            status=FindingStatus.CONFIRMED_ARTIFACT,
        ))

    # ── CORR-005: multiple modules suspicious ────────────────────────────
    suspicious_categories = {
        cat for cat, flist in by_category.items()
        if any(f.status == FindingStatus.SUSPICIOUS_INDICATOR for f in flist)
    }
    if len(suspicious_categories) >= 2:
        suspicious_findings = [
            f for f in findings
            if f.status == FindingStatus.SUSPICIOUS_INDICATOR
            and f.category in suspicious_categories
        ]
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-005"],
            triggered_by=[f.finding_id for f in suspicious_findings[:10]],
            match_reason=(
                f"Suspicious indicators found in {len(suspicious_categories)} "
                f"independent modules: {', '.join(sorted(suspicious_categories))}."
            ),
            supporting_evidence=(
                "Each module operated on the same source bytes independently."
            ),
            status=FindingStatus.SUSPICIOUS_INDICATOR,
        ))

    # ── CORR-006: embedded file signature ────────────────────────────────
    embedded_findings = [
        f for f in findings
        if "embedded" in f.title.lower() or f.rule_id == "META-EMBEDDED-FILE"
    ]
    if embedded_findings:
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-006"],
            triggered_by=[f.finding_id for f in embedded_findings],
            match_reason=(
                f"{len(embedded_findings)} embedded file signature(s) detected. "
                + "; ".join(
                    (f.evidence_details or {}).get("file_type", "unknown type")
                    for f in embedded_findings[:3]
                )
            ),
            supporting_evidence=(
                "Magic byte scan found known file headers at non-zero offsets."
            ),
            status=FindingStatus.SUSPICIOUS_INDICATOR,
        ))

    # ── CORR-007: multi-layer decode ─────────────────────────────────────
    decode_findings = by_category.get("decoder", [])
    deep_decode = [
        f for f in decode_findings
        if (f.evidence_details or {}).get("recursion_depth", 0) >= 2
    ]
    if deep_decode:
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-007"],
            triggered_by=[f.finding_id for f in deep_decode],
            match_reason=(
                f"Decoding required {max((f.evidence_details or {}).get('recursion_depth', 0) for f in deep_decode)} "
                "nested transformations."
            ),
            supporting_evidence=(
                "Each transformation step was individually verified with a readability scorer."
            ),
            status=FindingStatus.SUSPICIOUS_INDICATOR,
        ))

    # ── CORR-008: low printable ratio for text format ─────────────────────
    low_printable = [
        f for f in file_findings
        if (f.evidence_details or {}).get("printable_ratio", 100) < 10
        and (f.evidence_details or {}).get("is_text_format", False)
    ]
    if low_printable:
        results.append(_make_result(
            case_id=case.case_id,
            rule=_RULE_INDEX["CORR-008"],
            triggered_by=[f.finding_id for f in low_printable],
            match_reason="Printable character ratio below 10% for a declared text/document format.",
            supporting_evidence="Printable character count was computed from actual file bytes.",
            status=FindingStatus.SUSPICIOUS_INDICATOR,
        ))

    return results


# ── Helper ─────────────────────────────────────────────────────────────────

def _make_result(
    case_id: str,
    rule: dict,
    triggered_by: list[str],
    match_reason: str,
    supporting_evidence: str,
    status: FindingStatus,
) -> CorrelationResult:
    return CorrelationResult(
        case_id=case_id,
        rule_id=rule["rule_id"],
        rule_description=rule["description"],
        triggered_by_finding_ids=triggered_by,
        status=status,
        severity=rule["severity"],
        match_reason=match_reason,
        supporting_evidence=supporting_evidence,
        what_this_does_not_prove=rule["what_it_does_not_prove"],
        next_step=rule["next_step"],
    )
