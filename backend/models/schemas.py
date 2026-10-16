"""
Normalized data models for AutoDecodeX case management and findings.

Terminology used throughout:
  Observation   – a measurable or directly extracted result.
  Indicator     – a heuristic suggesting further investigation.
  Interpretation – an explanation of what the result may mean.
  Conclusion    – a carefully scoped statement supported by available evidence.

Result statuses:
  CONFIRMED_ARTIFACT   – a specific artifact or defined property was successfully verified.
  SUSPICIOUS_INDICATOR – a heuristic/rule produced a finding requiring investigation.
  NO_INDICATOR_DETECTED – the configured methods found no supported indicator.
  INCONCLUSIVE         – the available methods could not support a reliable conclusion.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

# ── Application version ────────────────────────────────────────────────────
APP_VERSION = "2.0.0"
ENGINE_VERSION = "2.0.0"


# ── Enumerations ───────────────────────────────────────────────────────────

class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class FindingStatus(str, Enum):
    CONFIRMED_ARTIFACT = "CONFIRMED_ARTIFACT"
    SUSPICIOUS_INDICATOR = "SUSPICIOUS_INDICATOR"
    NO_INDICATOR_DETECTED = "NO_INDICATOR_DETECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class Severity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ArtifactKind(str, Enum):
    ORIGINAL_EVIDENCE = "original_evidence"
    EXTRACTED_DATA = "extracted_data"
    DECODED_CONTENT = "decoded_content"
    DERIVED_ARTIFACT = "derived_artifact"


# ── Artifact model ─────────────────────────────────────────────────────────

class Artifact(BaseModel):
    """
    Represents a piece of evidence or a derived artifact within a case.
    Original evidence and derived artifacts are always kept separate.
    """
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    kind: ArtifactKind
    filename: str                      # sanitized display name
    size_bytes: int
    sha256: str
    md5: str
    mime_type: Optional[str] = None    # detected MIME/format, not trusted from upload
    detected_format: Optional[str] = None
    parent_artifact_id: Optional[str] = None   # None → original evidence
    parent_operation: Optional[str] = None     # e.g. "base64_decode", "lsb_extract"
    recursion_depth: int = 0
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: Optional[str] = None


# ── Finding model ──────────────────────────────────────────────────────────

class Finding(BaseModel):
    """
    Normalized finding produced by any analysis module.
    Optional fields must be None/omitted when the detector cannot supply them.
    Do not invent evidence values.
    """
    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    artifact_id: str

    # Classification
    category: str                     # e.g. "steganalysis", "decoder", "metadata", "file"
    title: str
    summary: str
    status: FindingStatus
    severity: Severity

    # Evidence
    observed_value: Optional[str] = None
    expected_value: Optional[str] = None
    evidence_details: Optional[dict[str, Any]] = None

    # Method
    detection_method: str             # algorithm / module name
    rule_id: Optional[str] = None
    detector_version: Optional[str] = None

    # Explanation (keep these fields distinct)
    explanation: str                  # what the result means
    limitations: str                  # what the result does NOT prove
    recommended_next_step: Optional[str] = None

    # Relationships
    parent_finding_ids: list[str] = Field(default_factory=list)

    # Location
    supporting_offsets: Optional[list[int]] = None
    image_region: Optional[dict[str, int]] = None   # {x, y, w, h}

    # Hashes
    input_artifact_hash: Optional[str] = None
    output_artifact_hash: Optional[str] = None

    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Transformation step (recursive decoder graph) ─────────────────────────

class TransformationStep(BaseModel):
    """
    Records one edge in the recursive decoding graph.
    Parent → child via a named decoder operation.
    """
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    source_artifact_id: str
    source_sha256: str
    decoder_name: str
    input_size_bytes: int
    output_size_bytes: int
    output_artifact_id: Optional[str] = None
    output_sha256: Optional[str] = None
    detected_output_type: Optional[str] = None
    recursion_depth: int
    duration_ms: float
    status: str                # "success" | "failed" | "skipped"
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Module execution record ────────────────────────────────────────────────

class ModuleResult(BaseModel):
    """
    Records what happened when a single analysis module ran.
    Partial results are preserved even when one module fails.
    """
    module_name: str
    artifact_id: str
    status: str              # "completed" | "failed" | "skipped" | "not_applicable"
    duration_ms: float = 0.0
    findings: list[Finding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    config_snapshot: Optional[dict[str, Any]] = None


# ── Correlation record ─────────────────────────────────────────────────────

class CorrelationResult(BaseModel):
    """
    Records a correlation rule evaluation result.
    Explains why a rule fired, what it does not prove, and what to examine next.
    """
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    rule_id: str
    rule_description: str
    triggered_by_finding_ids: list[str]
    status: FindingStatus
    severity: Severity
    match_reason: str               # why the rule matched
    supporting_evidence: str        # what additional evidence supports interpretation
    what_this_does_not_prove: str   # explicit scope limitation
    next_step: str
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Case model ─────────────────────────────────────────────────────────────

class Case(BaseModel):
    """
    Top-level investigation container.

    Integrity properties implemented:
      - SHA-256 and MD5 computed from actual uploaded bytes
      - Original evidence never overwritten
      - All derived artifacts linked to their parent via parent_artifact_id
      - Creation and completion timestamps in UTC
      - Analysis module status recorded per module

    Properties NOT claimed:
      - This is NOT a formal chain-of-custody system
      - Hashes are computed in-process; physical media integrity is not verified
      - There is no tamper-evident audit log
      - Storage is ephemeral (in-process dict); data does not survive restarts
    """
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at_utc: Optional[str] = None

    # Evidence file identity
    original_filename: str          # sanitized for display
    file_size_bytes: int
    detected_format: Optional[str] = None
    mime_type: Optional[str] = None
    sha256: str                     # computed from actual bytes
    md5: str                        # labelled as non-cryptographically-secure identifier

    # Status
    status: AnalysisStatus = AnalysisStatus.QUEUED
    enabled_modules: list[str] = Field(default_factory=list)
    completed_modules: list[str] = Field(default_factory=list)

    # Results
    artifacts: list[Artifact] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    correlations: list[CorrelationResult] = Field(default_factory=list)
    transformation_graph: list[TransformationStep] = Field(default_factory=list)
    module_results: list[ModuleResult] = Field(default_factory=list)

    # Summary
    summary: Optional[str] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Versions
    app_version: str = APP_VERSION
    engine_version: str = ENGINE_VERSION


# ── Safety limits for recursive decoder ────────────────────────────────────

class SafetyLimits(BaseModel):
    max_recursion_depth: int = 10
    max_artifacts: int = 50
    max_cumulative_bytes: int = 100 * 1024 * 1024   # 100 MB total
    max_decompressed_size: int = 50 * 1024 * 1024   # 50 MB per artifact
    max_processing_seconds: float = 60.0
    max_input_file_bytes: int = 50 * 1024 * 1024    # 50 MB upload

    class Config:
        frozen = True


DEFAULT_LIMITS = SafetyLimits()


# ── Report model ────────────────────────────────────────────────────────────

class ForensicReport(BaseModel):
    """
    Canonical exportable report. JSON is the source of truth; PDF is derived from it.
    """
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    generated_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Evidence summary
    original_filename: str
    file_size_bytes: int
    sha256: str
    md5: str
    detected_format: Optional[str] = None

    # Versions
    app_version: str
    engine_version: str

    # Analysis
    modules_run: list[str]
    modules_failed: list[str]
    findings: list[Finding]
    correlations: list[CorrelationResult]
    transformation_graph: list[TransformationStep]
    artifacts: list[Artifact]

    # Narrative
    scope_statement: str
    verified_observations: list[str]
    analyst_interpretations: list[str]
    limitations: list[str]
    errors: list[str]
    warnings: list[str]
    final_summary: str
