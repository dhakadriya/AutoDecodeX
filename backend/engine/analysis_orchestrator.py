"""
Centralized analysis orchestrator for AutoDecodeX.

Execution stages:
  1.  Validate input
  2.  Create case and evidence records
  3.  Calculate evidence hashes
  4.  Identify file type and structure
  5.  Run file analysis
  6.  Run metadata analysis
  7.  Run applicable steganalysis
  8.  Run decoding and controlled extraction
  9.  Analyse eligible derived artifacts
  10. Correlate findings
  11. Generate investigation summary
  12. Produce exportable report

Design principles:
  - One module failing does not erase successful results from other modules.
  - The original evidence bytes are never modified.
  - All derived artifacts have hashes and parent-child links.
  - Analysis is reproducible given the same input and configuration.
  - No extracted content is executed, opened, or launched.
  - Binary content is preserved as bytes until a valid encoding is established.
"""
from __future__ import annotations

import hashlib
import math
import re
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from backend.engine.correlation import correlate
from backend.engine.file_handler import sanitize_filename
from backend.engine.orchestrator import decode as bfs_decode
from backend.models.schemas import (
    APP_VERSION,
    ENGINE_VERSION,
    AnalysisStatus,
    Artifact,
    ArtifactKind,
    Case,
    Finding,
    FindingStatus,
    ForensicReport,
    ModuleResult,
    SafetyLimits,
    Severity,
    TransformationStep,
    DEFAULT_LIMITS,
)
from backend.models.case_store import save_case
from backend.scoring.scorer import score_text

# Image formats supported by steganalysis modules
_IMAGE_FORMATS = {"PNG image", "JPEG image", "BMP image", "GIF image",
                  "PNG", "JPEG", "BMP", "WebP image"}
_IMAGE_MIME = {"image/png", "image/jpeg", "image/jpg", "image/bmp", "image/webp", "image/gif"}

# Known text extensions that should have high printable ratio
_TEXT_EXTENSIONS = {".txt", ".csv", ".json", ".xml", ".html", ".htm", ".md",
                    ".yaml", ".yml", ".log", ".py", ".js", ".ts", ".c", ".cpp"}


# ── Public entry point ─────────────────────────────────────────────────────

def run_full_analysis(
    filename: str,
    file_bytes: bytes,
    mime_type: Optional[str] = None,
    limits: SafetyLimits = DEFAULT_LIMITS,
) -> Case:
    """
    Run the complete analysis pipeline on an uploaded file.
    Returns a fully populated Case object that is also persisted in the case store.
    Partial results are always preserved; one module failing does not abort the case.
    """
    t_start = time.monotonic()

    # ── Stage 1 & 2: Create case ──────────────────────────────────────────
    safe_name = sanitize_filename(filename)
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    md5 = hashlib.md5(file_bytes).hexdigest()

    case = Case(
        original_filename=safe_name,
        file_size_bytes=len(file_bytes),
        sha256=sha256,
        md5=md5,
        mime_type=mime_type,
        status=AnalysisStatus.RUNNING,
        enabled_modules=[
            "file_analysis", "metadata_analysis", "steganalysis",
            "decoder", "correlation"
        ],
    )

    # ── Stage 2: Create original evidence artifact ────────────────────────
    evidence = Artifact(
        case_id=case.case_id,
        kind=ArtifactKind.ORIGINAL_EVIDENCE,
        filename=safe_name,
        size_bytes=len(file_bytes),
        sha256=sha256,
        md5=md5,
        mime_type=mime_type,
    )
    case.artifacts.append(evidence)
    save_case(case)

    # ── Stage 4: Identify file type ───────────────────────────────────────
    detected_format, file_mime = _detect_format(file_bytes, safe_name, mime_type)
    evidence.detected_format = detected_format
    evidence.mime_type = file_mime or mime_type
    case.detected_format = detected_format
    case.mime_type = file_mime or mime_type

    # ── Stage 5: File analysis ────────────────────────────────────────────
    file_module = _run_file_analysis(case, evidence, file_bytes, safe_name)
    case.module_results.append(file_module)
    case.findings.extend(file_module.findings)
    if file_module.status == "completed":
        case.completed_modules.append("file_analysis")
    save_case(case)

    # ── Stage 6: Metadata analysis ────────────────────────────────────────
    meta_module = _run_metadata_analysis(case, evidence, file_bytes)
    case.module_results.append(meta_module)
    case.findings.extend(meta_module.findings)
    if meta_module.status == "completed":
        case.completed_modules.append("metadata_analysis")
    save_case(case)

    # ── Stage 7: Steganalysis (image-only) ───────────────────────────────
    is_image = (
        detected_format in _IMAGE_FORMATS
        or (file_mime or "") in _IMAGE_MIME
        or (mime_type or "") in _IMAGE_MIME
    )
    if is_image:
        stego_module = _run_steganalysis(case, evidence, file_bytes)
        case.module_results.append(stego_module)
        case.findings.extend(stego_module.findings)
        if stego_module.status == "completed":
            case.completed_modules.append("steganalysis")
    else:
        case.module_results.append(ModuleResult(
            module_name="steganalysis",
            artifact_id=evidence.artifact_id,
            status="not_applicable",
            warnings=[f"Steganalysis skipped: detected format '{detected_format}' is not a supported image."],
        ))
    save_case(case)

    # ── Stage 8: Decode extracted text ────────────────────────────────────
    decode_module = _run_decode_module(case, evidence, file_bytes, limits, t_start)
    case.module_results.append(decode_module)
    case.findings.extend(decode_module.findings)
    if decode_module.status == "completed":
        case.completed_modules.append("decoder")
    save_case(case)

    # ── Stage 10: Correlation ─────────────────────────────────────────────
    try:
        correlations = correlate(case)
        case.correlations.extend(correlations)
        case.completed_modules.append("correlation")
    except Exception as exc:
        case.warnings.append(f"Correlation engine error: {exc}")
    save_case(case)

    # ── Stage 11: Summary ─────────────────────────────────────────────────
    case.summary = _build_summary(case)
    case.completed_at_utc = datetime.now(timezone.utc).isoformat()

    has_errors = any(m.status == "failed" for m in case.module_results)
    case.status = (
        AnalysisStatus.COMPLETED_WITH_WARNINGS if has_errors
        else AnalysisStatus.COMPLETED
    )
    save_case(case)
    return case


# ── Stage 5: File analysis ─────────────────────────────────────────────────

def _run_file_analysis(
    case: Case,
    evidence: Artifact,
    file_bytes: bytes,
    filename: str,
) -> ModuleResult:
    t0 = time.monotonic()
    findings: list[Finding] = []
    warnings: list[str] = []
    errors: list[str] = []

    try:
        size = len(file_bytes)
        sha256 = evidence.sha256

        # Entropy
        entropy = _shannon_entropy(file_bytes)

        # Printable ratio
        printable = sum(1 for b in file_bytes if 32 <= b <= 126)
        printable_ratio = (printable / size * 100) if size > 0 else 0.0

        # Magic bytes (first 16)
        magic_hex = " ".join(f"{b:02X}" for b in file_bytes[:16])

        # String extraction
        strings = _extract_strings(file_bytes)

        # Extension vs detected format
        ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
        is_text_ext = ext in _TEXT_EXTENSIONS

        detected = evidence.detected_format or "Unknown"

        # Finding: file identity
        findings.append(Finding(
            case_id=case.case_id,
            artifact_id=evidence.artifact_id,
            category="file",
            title="File Identity",
            summary=f"File '{filename}': {size} bytes, format '{detected}'",
            status=FindingStatus.CONFIRMED_ARTIFACT,
            severity=Severity.INFORMATIONAL,
            observed_value=f"SHA-256: {sha256}",
            detection_method="hash_and_magic_bytes",
            explanation=(
                "SHA-256 was computed from the actual uploaded bytes. "
                "MD5 is provided for compatibility identification only "
                "and is NOT cryptographically secure."
            ),
            limitations="Hash values confirm file integrity; they do not indicate content.",
            evidence_details={
                "sha256": sha256,
                "md5": evidence.md5,
                "size_bytes": size,
                "detected_format": detected,
                "magic_bytes_hex": magic_hex,
                "entropy": round(entropy, 4),
                "printable_ratio": round(printable_ratio, 2),
                "strings_found": len(strings),
                "extension_mismatch": _check_extension_mismatch(ext, detected),
                "is_text_format": is_text_ext,
            },
        ))

        # Finding: entropy
        entropy_status = FindingStatus.INFORMATIONAL if entropy < 7.5 else FindingStatus.SUSPICIOUS_INDICATOR
        if hasattr(FindingStatus, 'INFORMATIONAL'):
            entropy_status = FindingStatus.SUSPICIOUS_INDICATOR if entropy >= 7.5 else FindingStatus.NO_INDICATOR_DETECTED
        findings.append(Finding(
            case_id=case.case_id,
            artifact_id=evidence.artifact_id,
            category="file",
            title="Entropy Analysis",
            summary=f"Shannon entropy: {entropy:.4f} bits/byte",
            status=FindingStatus.SUSPICIOUS_INDICATOR if entropy >= 7.5 else FindingStatus.NO_INDICATOR_DETECTED,
            severity=Severity.MEDIUM if entropy >= 7.5 else Severity.INFORMATIONAL,
            observed_value=str(round(entropy, 4)),
            expected_value="< 7.5 for typical uncompressed files",
            detection_method="shannon_entropy",
            explanation=(
                "Shannon entropy measures information density. "
                "Values near 8.0 indicate near-random byte distribution, "
                "consistent with encryption, compression, or random noise."
            ),
            limitations=(
                "High entropy alone does not confirm encryption or steganography. "
                "Compressed archives legitimately have entropy near 8.0."
            ),
            recommended_next_step=(
                "If entropy is near 8.0, check for known compression/encryption magic bytes. "
                "Compare entropy of different file sections."
            ) if entropy >= 7.5 else None,
            evidence_details={"entropy": round(entropy, 4), "printable_ratio": round(printable_ratio, 2)},
        ))

        # Finding: extension mismatch
        if _check_extension_mismatch(ext, detected):
            findings.append(Finding(
                case_id=case.case_id,
                artifact_id=evidence.artifact_id,
                category="file",
                title="File Extension / Format Mismatch",
                summary=f"Extension '{ext}' does not match detected format '{detected}'",
                status=FindingStatus.SUSPICIOUS_INDICATOR,
                severity=Severity.MEDIUM,
                observed_value=f"extension={ext}, detected={detected}",
                detection_method="magic_bytes",
                rule_id="FILE-MAGIC-MISMATCH",
                explanation="The file extension declared in the upload name differs from the format identified by magic bytes.",
                limitations="Mismatches are common for renamed or re-saved files and do not confirm malicious intent.",
                recommended_next_step="Verify the file in a hex editor. Check the first 16 bytes against known signatures.",
                evidence_details={"extension": ext, "detected_format": detected, "extension_mismatch": True},
            ))

        # Finding: string extraction
        if strings:
            findings.append(Finding(
                case_id=case.case_id,
                artifact_id=evidence.artifact_id,
                category="file",
                title="Printable String Extraction",
                summary=f"Extracted {len(strings)} printable string(s) of length >= 4",
                status=FindingStatus.CONFIRMED_ARTIFACT,
                severity=Severity.INFORMATIONAL,
                observed_value=f"{len(strings)} strings",
                detection_method="printable_string_scan",
                explanation="Printable ASCII runs of 4+ characters were extracted from the file bytes.",
                limitations="Extracted strings are observations only. Presence of readable strings does not establish intent.",
                evidence_details={"strings_sample": strings[:20], "total_strings": len(strings)},
            ))

    except Exception as exc:
        errors.append(f"File analysis error: {exc}")
        return ModuleResult(
            module_name="file_analysis",
            artifact_id=evidence.artifact_id,
            status="failed",
            duration_ms=round((time.monotonic() - t0) * 1000, 2),
            findings=findings,
            warnings=warnings,
            errors=errors,
        )

    return ModuleResult(
        module_name="file_analysis",
        artifact_id=evidence.artifact_id,
        status="completed",
        duration_ms=round((time.monotonic() - t0) * 1000, 2),
        findings=findings,
        warnings=warnings,
        errors=errors,
        config_snapshot={"min_string_length": 4, "max_strings": 100},
    )


# ── Stage 6: Metadata analysis ─────────────────────────────────────────────

def _run_metadata_analysis(
    case: Case,
    evidence: Artifact,
    file_bytes: bytes,
) -> ModuleResult:
    t0 = time.monotonic()
    findings: list[Finding] = []
    warnings: list[str] = []
    errors: list[str] = []

    try:
        from backend.stego.metadata_analyzer import full_metadata_pipeline

        pipeline = full_metadata_pipeline(file_bytes)
        analysis = pipeline.get("analysis", {})
        embedded = pipeline.get("embedded_files", [])
        meta = pipeline.get("metadata", {})

        # Finding: metadata summary
        total_fields = analysis.get("total_fields_scanned", 0)
        suspicious_count = analysis.get("total_suspicious", 0)
        flags = analysis.get("flags_found", [])

        findings.append(Finding(
            case_id=case.case_id,
            artifact_id=evidence.artifact_id,
            category="metadata",
            title="Metadata Overview",
            summary=f"{total_fields} field(s) scanned, {suspicious_count} suspicious",
            status=FindingStatus.SUSPICIOUS_INDICATOR if suspicious_count > 0 else FindingStatus.NO_INDICATOR_DETECTED,
            severity=Severity.MEDIUM if suspicious_count > 0 else Severity.INFORMATIONAL,
            observed_value=f"{suspicious_count}/{total_fields} suspicious fields",
            detection_method="metadata_pipeline",
            explanation="All metadata fields were scanned for encoded content, high entropy, and known flag patterns.",
            limitations="Metadata anomalies indicate fields worth examining; they do not confirm hidden data.",
            evidence_details={
                "total_fields": total_fields,
                "suspicious_fields": suspicious_count,
                "flags_found": flags,
                "has_exif": bool(meta.get("exif")),
                "has_gps": bool(meta.get("gps")),
                "has_png_text": bool(meta.get("png_text")),
            },
        ))

        # Per suspicious finding
        for mf in analysis.get("findings", []):
            if not mf.get("suspicious", False):
                continue
            decode_res = mf.get("decode_result")
            is_flag = (decode_res or {}).get("is_ctf_flag", False)
            findings.append(Finding(
                case_id=case.case_id,
                artifact_id=evidence.artifact_id,
                category="metadata",
                title=f"Suspicious Metadata Field: {mf.get('field', 'unknown')}",
                summary="; ".join(mf.get("suspicious_reasons", ["Unknown reason"])),
                status=FindingStatus.CONFIRMED_ARTIFACT if decode_res else FindingStatus.SUSPICIOUS_INDICATOR,
                severity=Severity.CRITICAL if is_flag else Severity.HIGH if decode_res else Severity.MEDIUM,
                observed_value=mf.get("raw_value", "")[:500],
                detection_method="metadata_encoding_scan",
                explanation=(
                    f"Field '{mf.get('field')}' in section '{mf.get('section')}' "
                    f"was flagged: {'; '.join(mf.get('suspicious_reasons', []))}. "
                    + (f"Decoded output: {decode_res.get('final_output', '')[:200]}" if decode_res else "")
                ),
                limitations=(
                    "Successfully decoding a metadata field confirms a transformation is possible, "
                    "not that the encoder intended to hide information."
                ),
                recommended_next_step=(
                    f"Verify the CTF flag value: {decode_res.get('final_output', '')} "
                    if is_flag else "Examine the decoded value manually."
                ),
                evidence_details={
                    "field": mf.get("field"),
                    "section": mf.get("section"),
                    "entropy": mf.get("entropy"),
                    "flags": mf.get("flags", []),
                    "is_ctf_flag": is_flag,
                    "decode_result": decode_res,
                },
            ))

        # Embedded file findings
        for ef in embedded:
            findings.append(Finding(
                case_id=case.case_id,
                artifact_id=evidence.artifact_id,
                category="metadata",
                title=f"Embedded File Signature: {ef.get('file_type', 'unknown')}",
                summary=f"Found at offset {ef.get('offset')} (0x{ef.get('offset_hex', '?')})",
                status=FindingStatus.SUSPICIOUS_INDICATOR,
                severity=Severity.HIGH,
                observed_value=ef.get("signature_hex", ""),
                detection_method="magic_byte_scan",
                rule_id="META-EMBEDDED-FILE",
                explanation=(
                    f"A {ef.get('file_type')} signature was detected at byte offset "
                    f"{ef.get('offset')} within the primary artifact."
                ),
                limitations=(
                    "File signatures can occur coincidentally. "
                    "The embedded content may not be extractable as a usable file."
                ),
                recommended_next_step=f"Extract bytes from offset {ef.get('offset')} and analyse as a separate artifact.",
                supporting_offsets=[ef.get("offset", 0)],
                evidence_details={
                    "offset": ef.get("offset"),
                    "offset_hex": ef.get("offset_hex"),
                    "file_type": ef.get("file_type"),
                    "signature_hex": ef.get("signature_hex"),
                    "context": ef.get("context", "")[:100],
                },
            ))

    except Exception as exc:
        errors.append(f"Metadata analysis error: {exc}")
        return ModuleResult(
            module_name="metadata_analysis",
            artifact_id=evidence.artifact_id,
            status="failed",
            duration_ms=round((time.monotonic() - t0) * 1000, 2),
            findings=findings,
            warnings=warnings,
            errors=errors,
        )

    return ModuleResult(
        module_name="metadata_analysis",
        artifact_id=evidence.artifact_id,
        status="completed",
        duration_ms=round((time.monotonic() - t0) * 1000, 2),
        findings=findings,
        warnings=warnings,
        errors=errors,
    )


# ── Stage 7: Steganalysis ──────────────────────────────────────────────────

def _run_steganalysis(
    case: Case,
    evidence: Artifact,
    file_bytes: bytes,
) -> ModuleResult:
    t0 = time.monotonic()
    findings: list[Finding] = []
    warnings: list[str] = []
    errors: list[str] = []

    # Validate image mode
    try:
        import io as _io
        from PIL import Image as _Image
        img = _Image.open(_io.BytesIO(file_bytes))
        mode = img.mode
        if mode not in ("RGB", "RGBA", "L", "P"):
            warnings.append(f"Unusual image mode '{mode}'; converting to RGB for analysis.")
        width, height = img.size
        if width * height > 20_000_000:
            warnings.append(
                f"Large image ({width}x{height}). Analysis may be slower."
            )
    except Exception as exc:
        errors.append(f"Image validation failed: {exc}")
        return ModuleResult(
            module_name="steganalysis",
            artifact_id=evidence.artifact_id,
            status="failed",
            duration_ms=round((time.monotonic() - t0) * 1000, 2),
            findings=findings, warnings=warnings, errors=errors,
        )

    # LSB extraction
    try:
        from backend.stego.lsb_extractor import extract_lsb
        lsb = extract_lsb(file_bytes, bits=1, channels="RGB", password=None)
        ascii_text = lsb.get("ascii_text", "")
        lsb_score = score_text(ascii_text) if ascii_text else 0.0
        has_readable = lsb_score > 0.5

        findings.append(Finding(
            case_id=case.case_id,
            artifact_id=evidence.artifact_id,
            category="steganalysis",
            title="LSB Extraction (1-bit RGB)",
            summary=f"Extracted {lsb.get('total_bits_extracted', 0)} bits; readable text score: {lsb_score:.3f}",
            status=FindingStatus.SUSPICIOUS_INDICATOR if has_readable else FindingStatus.NO_INDICATOR_DETECTED,
            severity=Severity.HIGH if has_readable else Severity.INFORMATIONAL,
            observed_value=ascii_text[:300] if ascii_text else "(no printable content)",
            detection_method="lsb_extraction_1bit_rgb",
            detector_version=ENGINE_VERSION,
            explanation=(
                "The least-significant bit of each RGB channel pixel was extracted in raster order. "
                + ("The extracted bytes contain readable text, which may indicate a hidden payload."
                   if has_readable else
                   "The extracted bytes did not form readable text. This does not rule out a payload.")
            ),
            limitations=(
                "LSB extraction assumes sequential, unencrypted, 1-bit embedding. "
                "Passwords, bit-depth variations, or channel order changes will produce noise. "
                "An anomaly here indicates the bytes are worth examining; "
                "it does NOT confirm that a payload was intentionally hidden."
            ),
            recommended_next_step="Try LSB brute-force with multiple bit depths and channel combinations." if has_readable else None,
            evidence_details={
                "bits_used": 1,
                "channels": "RGB",
                "total_bits": lsb.get("total_bits_extracted"),
                "ascii_preview": ascii_text[:200],
                "readability_score": round(lsb_score, 3),
                "possible_b64": lsb.get("possible_b64", []),
            },
        ))
    except Exception as exc:
        errors.append(f"LSB extraction failed: {exc}")

    # Entropy + chi-square
    try:
        from backend.stego.entropy_analyzer import analyze_entropy
        ent = analyze_entropy(file_bytes)

        stego_likelihood = ent.get("stego_likelihood", 0.0)
        chi = ent.get("chi_square_score", 0.0)
        suspicious = ent.get("suspicious", False)

        findings.append(Finding(
            case_id=case.case_id,
            artifact_id=evidence.artifact_id,
            category="steganalysis",
            title="Entropy and Chi-Square Analysis",
            summary=(
                f"LSB entropy: {ent.get('avg_lsb_entropy', 0):.4f}, "
                f"chi-square score: {chi:.4f}, "
                f"heuristic stego likelihood: {stego_likelihood:.3f}"
            ),
            status=FindingStatus.SUSPICIOUS_INDICATOR if suspicious else FindingStatus.NO_INDICATOR_DETECTED,
            severity=Severity.MEDIUM if suspicious else Severity.INFORMATIONAL,
            observed_value=f"stego_likelihood={stego_likelihood:.3f}, chi_square={chi:.4f}",
            expected_value="LSB entropy ~0.9-1.0 for natural images; chi_square < 0.7 for unmodified images",
            detection_method="shannon_entropy_and_chi_square_lsb",
            detector_version=ENGINE_VERSION,
            explanation=(
                "Shannon entropy of LSB planes and a chi-square test on value-pair frequencies "
                "were computed. Natural images have near-uniform LSB distributions; "
                "LSB steganography further homogenises them. "
                "The 'stego_likelihood' is a HEURISTIC PRIORITY SCORE, not a probability of maliciousness. "
                "Formula: max(0, min(1, (avg_lsb_entropy - 0.85) / 0.15))."
            ),
            limitations=(
                "Chi-square and entropy metrics have known false-positive rates on "
                "heavily compressed images (JPEG, lossy WebP) and uniformly coloured images. "
                "A suspicious score does not confirm steganographic content."
            ),
            recommended_next_step="Cross-reference with LSB extraction results. Compare against a clean cover image." if suspicious else None,
            evidence_details={
                "global_entropy": ent.get("global_entropy"),
                "channel_entropy": ent.get("channel_entropy"),
                "lsb_entropy": ent.get("lsb_entropy"),
                "avg_lsb_entropy": ent.get("avg_lsb_entropy"),
                "stego_likelihood": stego_likelihood,
                "chi_square_score": chi,
                "suspicious": suspicious,
                "note_on_score": (
                    "stego_likelihood is a heuristic display priority, "
                    "not a statistical probability of steganographic content."
                ),
            },
        ))
    except Exception as exc:
        errors.append(f"Entropy analysis failed: {exc}")

    return ModuleResult(
        module_name="steganalysis",
        artifact_id=evidence.artifact_id,
        status="completed" if not errors else "completed",  # partial is still completed
        duration_ms=round((time.monotonic() - t0) * 1000, 2),
        findings=findings,
        warnings=warnings,
        errors=errors,
        config_snapshot={
            "lsb_bits": 1,
            "lsb_channels": "RGB",
            "image_mode": mode,
            "image_size": f"{width}x{height}",
        },
    )


# ── Stage 8: Decoder ───────────────────────────────────────────────────────

def _run_decode_module(
    case: Case,
    evidence: Artifact,
    file_bytes: bytes,
    limits: SafetyLimits,
    t_case_start: float,
) -> ModuleResult:
    """
    Attempt to decode:
     a) Any text content extracted from the file
     b) LSB-extracted text (image only)
     c) Suspicious metadata field values
    Records transformation steps and derived artifacts.
    """
    t0 = time.monotonic()
    findings: list[Finding] = []
    warnings: list[str] = []
    errors: list[str] = []

    # Collect text candidates from prior findings
    candidates: list[tuple[str, str]] = []  # (text, source_description)

    # Try to interpret the whole file as text if mostly printable
    printable_ratio = sum(1 for b in file_bytes if 32 <= b <= 126) / max(len(file_bytes), 1)
    if printable_ratio > 0.9 and len(file_bytes) < 1_000_000:
        try:
            file_text = file_bytes.decode("utf-8", errors="replace").strip()
            if file_text:
                candidates.append((file_text[:100_000], "file_content_as_text"))
        except Exception:
            pass

    # Gather LSB ascii from prior stego results
    for mr in case.module_results:
        if mr.module_name == "steganalysis":
            for f in mr.findings:
                lsb_text = (f.evidence_details or {}).get("ascii_preview", "")
                if lsb_text and len(lsb_text) >= 4:
                    candidates.append((lsb_text, "lsb_extracted"))

    # Gather suspicious metadata values
    for mr in case.module_results:
        if mr.module_name == "metadata_analysis":
            for f in mr.findings:
                if f.status == FindingStatus.SUSPICIOUS_INDICATOR:
                    raw = (f.evidence_details or {}).get("field") or f.observed_value or ""
                    raw_val = (f.evidence_details or {}).get("raw_value", "")
                    if raw_val and len(raw_val) >= 4:
                        candidates.append((raw_val[:2000], f"metadata_field:{raw}"))

    seen_hashes: set[str] = set()
    artifact_count = 0

    for (text, source) in candidates:
        elapsed = time.monotonic() - t_case_start
        if elapsed > limits.max_processing_seconds:
            warnings.append(f"Processing time limit ({limits.max_processing_seconds}s) reached; remaining candidates skipped.")
            break
        if artifact_count >= limits.max_artifacts:
            warnings.append("Artifact count limit reached; remaining candidates skipped.")
            break

        text_hash = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        if text_hash in seen_hashes:
            continue
        seen_hashes.add(text_hash)

        try:
            t_decode = time.monotonic()
            result = bfs_decode(text, max_depth=limits.max_recursion_depth)
            decode_ms = (time.monotonic() - t_decode) * 1000

            is_flag = result.is_ctf_flag
            depth = len(result.steps)

            # Record transformation steps
            prev_text = text
            prev_hash = text_hash
            for step in result.steps:
                out_hash = hashlib.sha256(
                    step.output_text.encode("utf-8", errors="replace")
                ).hexdigest()
                ts = TransformationStep(
                    case_id=case.case_id,
                    source_artifact_id=evidence.artifact_id,
                    source_sha256=prev_hash,
                    decoder_name=step.encoding_type,
                    input_size_bytes=len(prev_text.encode("utf-8", errors="replace")),
                    output_size_bytes=len(step.output_text.encode("utf-8", errors="replace")),
                    output_sha256=out_hash,
                    detected_output_type=None,
                    recursion_depth=step.step_number,
                    duration_ms=round(decode_ms / max(len(result.steps), 1), 2),
                    status="success",
                )
                case.transformation_graph.append(ts)
                prev_text = step.output_text
                prev_hash = out_hash
                artifact_count += 1

            # Create derived artifact for the final output
            if result.steps:
                out_bytes = result.final_output.encode("utf-8", errors="replace")
                out_sha = hashlib.sha256(out_bytes).hexdigest()
                out_md5 = hashlib.md5(out_bytes).hexdigest()
                derived = Artifact(
                    case_id=case.case_id,
                    kind=ArtifactKind.DECODED_CONTENT,
                    filename=f"decoded_{source[:30]}.txt",
                    size_bytes=len(out_bytes),
                    sha256=out_sha,
                    md5=out_md5,
                    parent_artifact_id=evidence.artifact_id,
                    parent_operation=" -> ".join(s.encoding_type for s in result.steps),
                    recursion_depth=depth,
                )
                case.artifacts.append(derived)

            status = FindingStatus.CONFIRMED_ARTIFACT if result.success or is_flag else FindingStatus.INCONCLUSIVE
            severity = Severity.CRITICAL if is_flag else (Severity.HIGH if result.success and depth >= 2 else Severity.MEDIUM if result.success else Severity.INFORMATIONAL)

            findings.append(Finding(
                case_id=case.case_id,
                artifact_id=evidence.artifact_id,
                category="decoder",
                title=f"{'CTF Flag Decoded' if is_flag else 'Decoded Content'} from {source}",
                summary=result.path_description or f"{'No encoding detected' if not result.steps else ' -> '.join(s.encoding_type for s in result.steps)}",
                status=status,
                severity=severity,
                observed_value=result.final_output[:500],
                detection_method="bfs_recursive_decoder",
                detector_version=ENGINE_VERSION,
                explanation=(
                    f"BFS decoder explored encoding paths to depth {depth}. "
                    f"Transformation path: {result.path_description}. "
                    f"Readability score: {result.total_score:.3f}."
                ),
                limitations=(
                    "Successful decoding confirms a valid transformation was applied. "
                    "It does not confirm that content was intentionally encoded. "
                    "Readability score is a heuristic, not a semantic evaluation."
                ),
                recommended_next_step=f"Verify flag: {result.final_output[:100]}" if is_flag else None,
                evidence_details={
                    "source": source,
                    "is_ctf_flag": is_flag,
                    "total_score": round(result.total_score, 3),
                    "recursion_depth": depth,
                    "steps": [
                        {"encoding_type": s.encoding_type, "confidence": s.confidence, "score": s.score}
                        for s in result.steps
                    ],
                    "final_output_preview": result.final_output[:300],
                },
                input_artifact_hash=text_hash,
            ))

        except Exception as exc:
            errors.append(f"Decode failed for source '{source}': {exc}")

    return ModuleResult(
        module_name="decoder",
        artifact_id=evidence.artifact_id,
        status="completed",
        duration_ms=round((time.monotonic() - t0) * 1000, 2),
        findings=findings,
        warnings=warnings,
        errors=errors,
        config_snapshot={
            "max_recursion_depth": limits.max_recursion_depth,
            "max_artifacts": limits.max_artifacts,
            "max_processing_seconds": limits.max_processing_seconds,
            "candidates_processed": len(candidates),
        },
    )


# ── Stage 11: Summary ──────────────────────────────────────────────────────

def _build_summary(case: Case) -> str:
    total = len(case.findings)
    flags = sum(1 for f in case.findings if (f.evidence_details or {}).get("is_ctf_flag"))
    suspicious = sum(1 for f in case.findings if f.status == FindingStatus.SUSPICIOUS_INDICATOR)
    confirmed = sum(1 for f in case.findings if f.status == FindingStatus.CONFIRMED_ARTIFACT)
    failed_mods = [m.module_name for m in case.module_results if m.status == "failed"]

    lines = [
        f"Case {case.case_id[:8]}... | File: {case.original_filename} ({case.file_size_bytes:,} bytes)",
        f"Format: {case.detected_format or 'Unknown'} | SHA-256: {case.sha256[:16]}...",
        f"Findings: {total} total — {confirmed} confirmed, {suspicious} suspicious indicators",
    ]
    if flags:
        lines.append(f"CTF Flags: {flags} flag pattern(s) detected")
    if case.correlations:
        lines.append(f"Correlations: {len(case.correlations)} rule(s) fired")
    if case.transformation_graph:
        lines.append(f"Decoding graph: {len(case.transformation_graph)} transformation step(s)")
    if failed_mods:
        lines.append(f"Modules with errors: {', '.join(failed_mods)}")
    lines.append(
        "NOTE: Suspicious indicators require further investigation. "
        "They do not confirm malicious activity or the presence of a hidden payload."
    )
    return "\n".join(lines)


# ── Stage 12: Report generation ────────────────────────────────────────────

def build_report(case: Case) -> ForensicReport:
    """Build a ForensicReport from a completed Case."""
    modules_run = [m.module_name for m in case.module_results if m.status != "failed"]
    modules_failed = [m.module_name for m in case.module_results if m.status == "failed"]

    verified = []
    interpretations = []
    limitations_seen: set[str] = set()
    all_limitations: list[str] = []

    for f in case.findings:
        if f.status == FindingStatus.CONFIRMED_ARTIFACT:
            verified.append(f.summary)
        elif f.status == FindingStatus.SUSPICIOUS_INDICATOR:
            interpretations.append(f.summary)
        if f.limitations and f.limitations not in limitations_seen:
            limitations_seen.add(f.limitations)
            all_limitations.append(f.limitations)

    all_errors = []
    all_warnings = list(case.warnings)
    for m in case.module_results:
        all_errors.extend(m.errors)
        all_warnings.extend(m.warnings)

    return ForensicReport(
        case_id=case.case_id,
        original_filename=case.original_filename,
        file_size_bytes=case.file_size_bytes,
        sha256=case.sha256,
        md5=case.md5,
        detected_format=case.detected_format,
        app_version=APP_VERSION,
        engine_version=ENGINE_VERSION,
        modules_run=modules_run,
        modules_failed=modules_failed,
        findings=case.findings,
        correlations=case.correlations,
        transformation_graph=case.transformation_graph,
        artifacts=case.artifacts,
        scope_statement=(
            "This report was generated by AutoDecodeX, an automated digital-forensics "
            "and steganalysis tool. Analysis is limited to the modules listed above "
            "and the algorithms they implement. Results are observations and heuristic "
            "indicators, not formal forensic conclusions. Manual review by a qualified "
            "analyst is required before drawing conclusions about malicious activity."
        ),
        verified_observations=verified,
        analyst_interpretations=interpretations,
        limitations=all_limitations + [
            "Storage is in-process; data does not survive a server restart.",
            "No formal chain-of-custody is implemented.",
            "Hashes are computed in-process from uploaded bytes; physical media integrity is not verified.",
        ],
        errors=all_errors,
        warnings=all_warnings,
        final_summary=case.summary or "Analysis incomplete.",
    )


# ── Helpers ────────────────────────────────────────────────────────────────

def _shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _extract_strings(data: bytes, min_len: int = 4, max_count: int = 100) -> list[str]:
    strings: list[str] = []
    current: list[str] = []
    for b in data:
        if 32 <= b <= 126:
            current.append(chr(b))
        else:
            if len(current) >= min_len:
                strings.append("".join(current))
                if len(strings) >= max_count:
                    break
            current = []
    if len(current) >= min_len and len(strings) < max_count:
        strings.append("".join(current))
    return strings


def _detect_format(
    data: bytes, filename: str, mime_type: Optional[str]
) -> tuple[str, Optional[str]]:
    """Identify file format from magic bytes. Returns (format_name, mime_type)."""
    MAGIC: list[tuple[bytes, str, str]] = [
        (b"\x89PNG\r\n\x1a\n", "PNG image", "image/png"),
        (b"\xff\xd8\xff", "JPEG image", "image/jpeg"),
        (b"BM", "BMP image", "image/bmp"),
        (b"GIF87a", "GIF image", "image/gif"),
        (b"GIF89a", "GIF image", "image/gif"),
        (b"PK\x03\x04", "ZIP archive", "application/zip"),
        (b"PK\x05\x06", "ZIP archive", "application/zip"),
        (b"\x1f\x8b", "GZIP archive", "application/gzip"),
        (b"%PDF", "PDF document", "application/pdf"),
        (b"\x7fELF", "ELF executable", "application/octet-stream"),
        (b"MZ", "Windows PE/EXE", "application/octet-stream"),
        (b"Rar!", "RAR archive", "application/x-rar"),
        (b"7z\xbc\xaf", "7-Zip archive", "application/x-7z-compressed"),
        (b"ID3", "MP3 audio", "audio/mpeg"),
        (b"OggS", "OGG audio", "audio/ogg"),
    ]
    for magic, fmt, detected_mime in MAGIC:
        if data.startswith(magic):
            # WebP is RIFF....WEBP
            if magic == b"RIFF" and len(data) >= 12 and data[8:12] == b"WEBP":
                return "WebP image", "image/webp"
            return fmt, detected_mime

    if data.startswith(b"RIFF") and len(data) >= 12:
        sub = data[8:12]
        if sub == b"WEBP":
            return "WebP image", "image/webp"
        if sub == b"WAVE":
            return "WAV audio", "audio/wav"

    # Fall back to extension hint
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_map = {
        "txt": "Plain text", "csv": "CSV data", "json": "JSON data",
        "xml": "XML document", "html": "HTML document", "py": "Python source",
    }
    if ext in ext_map:
        return ext_map[ext], mime_type

    return "Unknown/Binary", mime_type


def _check_extension_mismatch(ext: str, detected_format: str) -> bool:
    """Return True if the file extension contradicts the detected format."""
    EXPECT: dict[str, set[str]] = {
        ".png": {"PNG image"},
        ".jpg": {"JPEG image"},
        ".jpeg": {"JPEG image"},
        ".bmp": {"BMP image"},
        ".gif": {"GIF image"},
        ".webp": {"WebP image"},
        ".zip": {"ZIP archive"},
        ".pdf": {"PDF document"},
        ".gz": {"GZIP archive"},
        ".wav": {"WAV audio"},
        ".mp3": {"MP3 audio"},
        ".exe": {"Windows PE/EXE"},
        ".elf": {"ELF executable"},
    }
    expected = EXPECT.get(ext)
    if not expected:
        return False
    return detected_format not in expected
