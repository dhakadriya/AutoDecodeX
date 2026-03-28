"""
Core decoding orchestrator.
Uses BFS to explore multi-layer decoding paths.
Returns the best decoding path with step-by-step explanation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import hashlib

from backend.detectors.detector import detect_all
from backend.decoders.decoders import DECODERS, CaesarDecoder, XORDecoder
from backend.scoring.scorer import score_text

MAX_DEPTH = 10
SCORE_THRESHOLD = 0.75
TOP_DETECTIONS = 3  # Try top N detected encodings per step


@dataclass
class DecodingStep:
    step_number: int
    encoding_type: str
    confidence: float
    input_text: str
    output_text: str
    score: float


@dataclass
class DecodingResult:
    success: bool
    final_output: str
    steps: list[DecodingStep]
    total_score: float
    path_description: str
    is_ctf_flag: bool = False


@dataclass
class _Node:
    text: str
    steps: list[DecodingStep]
    depth: int
    score: float
    visited_hashes: set = field(default_factory=set)


def _text_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8', errors='replace')).hexdigest()


def decode(input_text: str, ctf_mode: bool = False) -> DecodingResult:
    """
    Main entry point. Runs BFS over possible decoding paths.
    Returns the best result found.
    """
    input_text = input_text.strip()
    initial_score = score_text(input_text)

    # If already readable, return as-is
    if initial_score >= SCORE_THRESHOLD:
        return DecodingResult(
            success=True,
            final_output=input_text,
            steps=[],
            total_score=initial_score,
            path_description="Input appears to already be plaintext.",
            is_ctf_flag=_is_flag(input_text),
        )

    initial_hash = _text_hash(input_text)
    queue: list[_Node] = [_Node(
        text=input_text,
        steps=[],
        depth=0,
        score=initial_score,
        visited_hashes={initial_hash},
    )]

    best: Optional[DecodingResult] = None

    while queue:
        node = queue.pop(0)  # BFS

        if node.depth >= MAX_DEPTH:
            continue

        detections = detect_all(node.text)

        # In CTF mode, boost common CTF encodings
        if ctf_mode:
            detections = _boost_ctf(detections)

        # Try top N detections
        for detection in detections[:TOP_DETECTIONS]:
            enc_type = detection['type']
            confidence = detection['confidence']

            # Skip brute-force types in main loop (handled separately)
            if enc_type in ('caesar', 'xor'):
                continue

            decoder = DECODERS.get(enc_type)
            if not decoder:
                continue

            decoded = decoder.decode(node.text)
            if not decoded or decoded == node.text:
                continue

            decoded_hash = _text_hash(decoded)
            if decoded_hash in node.visited_hashes:
                continue  # Loop detected

            new_score = score_text(decoded)
            step = DecodingStep(
                step_number=node.depth + 1,
                encoding_type=enc_type,
                confidence=confidence,
                input_text=node.text,
                output_text=decoded,
                score=new_score,
            )
            new_steps = node.steps + [step]
            new_hashes = node.visited_hashes | {decoded_hash}

            result = DecodingResult(
                success=new_score >= SCORE_THRESHOLD or _is_flag(decoded),
                final_output=decoded,
                steps=new_steps,
                total_score=new_score,
                path_description=_build_path_desc(new_steps),
                is_ctf_flag=_is_flag(decoded),
            )

            # Update best if this is better
            if best is None or new_score > best.total_score:
                best = result

            if result.success:
                return result  # Early exit on high-confidence result

            # Continue exploring
            queue.append(_Node(
                text=decoded,
                steps=new_steps,
                depth=node.depth + 1,
                score=new_score,
                visited_hashes=new_hashes,
            ))

    if best:
        return best

    # Nothing worked — return original with no steps
    return DecodingResult(
        success=False,
        final_output=input_text,
        steps=[],
        total_score=initial_score,
        path_description="No encoding detected or decoding failed.",
    )


def brute_force_caesar(text: str) -> list[dict]:
    """Return all 26 Caesar shifts ranked by readability score."""
    decoder = CaesarDecoder()
    results = decoder.brute_force(text)
    for r in results:
        r['score'] = score_text(r['decoded'])
    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def brute_force_xor(text: str) -> list[dict]:
    """Single-byte XOR brute force."""
    decoder = XORDecoder()
    return decoder.brute_force(text)


def _is_flag(text: str) -> bool:
    import re
    return bool(re.search(r'[a-zA-Z0-9_]{2,10}\{[^}]+\}', text))


def _build_path_desc(steps: list[DecodingStep]) -> str:
    if not steps:
        return "No transformations applied."
    parts = [f"{s.encoding_type.upper()} ({int(s.confidence * 100)}%)" for s in steps]
    return " → ".join(parts) + " → Plaintext"


def _boost_ctf(detections: list[dict]) -> list[dict]:
    """In CTF mode, boost base64, hex, rot13 confidence."""
    ctf_priority = {'base64', 'hex', 'rot13', 'base32', 'binary'}
    for d in detections:
        if d['type'] in ctf_priority:
            d['confidence'] = min(1.0, d['confidence'] * 1.1)
    detections.sort(key=lambda x: x['confidence'], reverse=True)
    return detections
