"""
Metadata extraction and analysis — ExifTool-like functionality.
Extracts all EXIF/metadata fields, scans for encoded content,
auto-decodes suspicious values, detects embedded file signatures.
"""
from __future__ import annotations
import io
import re
import math
import struct
import string
from collections import Counter
from typing import Any
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


# ── Flag patterns ──────────────────────────────────────────────────────────
FLAG_PATTERNS = [
    r'flag\{[^}]+\}',
    r'ctf\{[^}]+\}',
    r'htb\{[^}]+\}',
    r'picoctf\{[^}]+\}',
    r'thm\{[^}]+\}',
    r'[a-z0-9_]{2,8}\{[^}]{3,}\}',
]

# ── Known file magic bytes ─────────────────────────────────────────────────
FILE_SIGNATURES = {
    b'\x89PNG\r\n\x1a\n': 'PNG image',
    b'\xff\xd8\xff':       'JPEG image',
    b'PK\x03\x04':         'ZIP archive',
    b'PK\x05\x06':         'ZIP archive (empty)',
    b'Rar!':               'RAR archive',
    b'\x1f\x8b':           'GZIP archive',
    b'BZh':                'BZIP2 archive',
    b'7z\xbc\xaf':         '7-Zip archive',
    b'%PDF':               'PDF document',
    b'GIF87a':             'GIF image',
    b'GIF89a':             'GIF image',
    b'BM':                 'BMP image',
    b'\x00\x00\x01\x00':   'ICO image',
    b'RIFF':               'RIFF/WAV/AVI',
    b'ID3':                'MP3 audio',
    b'\x7fELF':            'ELF executable',
    b'MZ':                 'Windows PE/EXE',
    b'OggS':               'OGG audio',
    b'\x00\x00\x00\x0cftyp': 'MP4/MOV video',
}


# ── Entropy helper ─────────────────────────────────────────────────────────
def _entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


# ── Flag detector ──────────────────────────────────────────────────────────
def _find_flags(text: str) -> list[str]:
    found = []
    for pat in FLAG_PATTERNS:
        found.extend(re.findall(pat, text, re.IGNORECASE))
    return list(set(found))


# ── Encoding detector (lightweight, no import of full detector) ────────────
def _detect_encoding(value: str) -> dict:
    """Quick heuristic encoding detection for a metadata value."""
    v = value.strip()
    detections = []

    if re.fullmatch(r'[A-Za-z0-9+/]+=*', v) and len(v) % 4 == 0 and len(v) >= 8:
        detections.append({"type": "base64", "confidence": 0.90})

    if re.fullmatch(r'[A-Z2-7]+=*', v.upper()) and len(v) % 8 == 0 and len(v) >= 8:
        detections.append({"type": "base32", "confidence": 0.85})

    clean_hex = v.replace(' ', '').replace('0x', '').replace('\\x', '')
    if re.fullmatch(r'[0-9a-fA-F]+', clean_hex) and len(clean_hex) % 2 == 0 and len(clean_hex) >= 6:
        detections.append({"type": "hex", "confidence": 0.88})

    parts = v.split()
    if len(parts) >= 3 and all(re.fullmatch(r'[01]{8}', p) for p in parts):
        detections.append({"type": "binary", "confidence": 0.95})

    if re.fullmatch(r'[.\-/ ]+', v) and len(v) >= 5:
        detections.append({"type": "morse", "confidence": 0.90})

    if '%' in v and re.search(r'%[0-9a-fA-F]{2}', v):
        detections.append({"type": "url", "confidence": 0.92})

    detections.sort(key=lambda x: x["confidence"], reverse=True)
    return detections[0] if detections else {}


# ── Auto-decode a value ────────────────────────────────────────────────────
def _auto_decode_value(value: str) -> dict | None:
    """Run value through the AutoDecode engine."""
    try:
        from backend.engine.orchestrator import decode as engine_decode
        result = engine_decode(value.strip())
        if result.steps or result.is_ctf_flag:
            return {
                "final_output": result.final_output,
                "path_description": result.path_description,
                "total_score": round(result.total_score, 3),
                "is_ctf_flag": result.is_ctf_flag,
                "steps": [
                    {
                        "step_number": s.step_number,
                        "encoding_type": s.encoding_type,
                        "confidence": round(s.confidence, 3),
                        "output_text": s.output_text[:200],
                    }
                    for s in result.steps
                ],
            }
    except Exception:
        pass
    return None


# ── EXIF value normalizer ──────────────────────────────────────────────────
def _normalize(val: Any) -> str:
    """Convert any EXIF value to a clean string."""
    if isinstance(val, bytes):
        try:
            decoded = val.decode('utf-8', errors='replace').strip('\x00').strip()
            if decoded:
                return decoded
        except Exception:
            pass
        return val.hex()
    if isinstance(val, tuple):
        return " / ".join(_normalize(v) for v in val)
    if isinstance(val, dict):
        return str({k: _normalize(v) for k, v in val.items()})
    return str(val).strip()


# ── Main metadata extractor ────────────────────────────────────────────────
def extract_metadata(image_bytes: bytes) -> dict:
    """
    Extract all metadata from image bytes.
    Returns structured dict with all fields, file info, and GPS data.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Basic file info
    file_info = {
        "format":     img.format or "Unknown",
        "mode":       img.mode,
        "width":      img.width,
        "height":     img.height,
        "size_bytes": len(image_bytes),
        "size_kb":    round(len(image_bytes) / 1024, 2),
    }

    # PNG text chunks (iTXt, tEXt, zTXt) — rich source of hidden data
    png_text = {}
    if hasattr(img, 'text') and img.text:
        png_text = {k: str(v) for k, v in img.text.items()}

    # EXIF data
    exif_fields = {}
    gps_fields = {}
    raw_exif = {}

    try:
        exif_data = img._getexif()  # type: ignore
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                norm = _normalize(value)
                raw_exif[tag_name] = norm

                if tag_name == "GPSInfo" and isinstance(value, dict):
                    for gps_tag, gps_val in value.items():
                        gps_name = GPSTAGS.get(gps_tag, f"GPS_{gps_tag}")
                        gps_fields[gps_name] = _normalize(gps_val)
                else:
                    exif_fields[tag_name] = norm
    except Exception:
        pass

    # Also try PIL info dict (covers more formats)
    pil_info = {}
    for k, v in (img.info or {}).items():
        if k not in ('exif', 'icc_profile', 'dpi'):
            try:
                pil_info[str(k)] = _normalize(v)
            except Exception:
                pass

    return {
        "file_info": file_info,
        "exif": exif_fields,
        "gps": gps_fields,
        "png_text": png_text,
        "pil_info": pil_info,
        "raw_exif": raw_exif,
    }


# ── Metadata analyzer ─────────────────────────────────────────────────────
def analyze_metadata(metadata: dict) -> dict:
    """
    Scan all metadata fields for:
    - Encoded content (Base64, Hex, Binary, etc.)
    - CTF flags
    - High entropy values
    - Suspicious patterns
    Returns list of findings with auto-decode results.
    """
    findings = []
    flags_found = []
    all_fields: dict[str, str] = {}

    # Flatten all metadata sections
    for section in ("exif", "png_text", "pil_info", "raw_exif"):
        for k, v in metadata.get(section, {}).items():
            all_fields[f"{section}.{k}"] = v

    for field_path, raw_value in all_fields.items():
        if not raw_value or len(raw_value) < 4:
            continue

        section, _, field_name = field_path.partition(".")
        finding: dict = {
            "field": field_name,
            "section": section,
            "raw_value": raw_value[:500],
            "length": len(raw_value),
            "entropy": round(_entropy(raw_value), 3),
            "flags": [],
            "encoding": {},
            "decode_result": None,
            "suspicious": False,
            "suspicious_reasons": [],
        }

        # Flag detection
        flags = _find_flags(raw_value)
        if flags:
            finding["flags"] = flags
            finding["suspicious"] = True
            finding["suspicious_reasons"].append("CTF flag pattern detected")
            flags_found.extend(flags)

        # Encoding detection
        enc = _detect_encoding(raw_value)
        if enc:
            finding["encoding"] = enc
            finding["suspicious"] = True
            finding["suspicious_reasons"].append(f"Possible {enc['type']} encoding ({int(enc['confidence']*100)}%)")

            # Auto-decode
            decode = _auto_decode_value(raw_value)
            if decode:
                finding["decode_result"] = decode
                if decode.get("is_ctf_flag"):
                    finding["suspicious"] = True
                    finding["suspicious_reasons"].append("Decoded value contains CTF flag")
                    flags_found.extend(_find_flags(decode.get("final_output", "")))

        # High entropy check
        if finding["entropy"] > 4.5 and len(raw_value) > 20:
            finding["suspicious"] = True
            finding["suspicious_reasons"].append(f"High entropy ({finding['entropy']})")

        # Long value in unusual field
        suspicious_fields = {
            "comment", "usercomment", "imagedescription", "artist",
            "copyright", "software", "make", "model", "xpcomment",
            "xpauthor", "xpkeywords", "xptitle", "xpsubject",
        }
        if field_name.lower() in suspicious_fields and len(raw_value) > 30:
            finding["suspicious"] = True
            finding["suspicious_reasons"].append("Suspicious field with long value")

        if finding["suspicious"] or enc or flags:
            findings.append(finding)

    # Sort: flags first, then by entropy desc
    findings.sort(key=lambda x: (
        -len(x["flags"]),
        -(x["decode_result"] or {}).get("is_ctf_flag", False),
        -x["entropy"],
    ))

    return {
        "findings": findings,
        "flags_found": list(set(flags_found)),
        "total_suspicious": sum(1 for f in findings if f["suspicious"]),
        "total_fields_scanned": len(all_fields),
    }


# ── Embedded file scanner ──────────────────────────────────────────────────
def scan_embedded_files(image_bytes: bytes) -> list[dict]:
    """
    Scan raw image bytes for embedded file signatures (binwalk-style).
    Returns list of detected embedded files with offset and type.
    """
    found = []
    for sig, file_type in FILE_SIGNATURES.items():
        offset = 0
        while True:
            idx = image_bytes.find(sig, offset)
            if idx == -1:
                break
            # Skip the very start (that's the image itself)
            if idx > 16:
                found.append({
                    "offset": idx,
                    "offset_hex": hex(idx),
                    "file_type": file_type,
                    "signature_hex": sig.hex(),
                    "context": image_bytes[idx:idx+32].hex(),
                })
            offset = idx + 1

    found.sort(key=lambda x: x["offset"])
    return found[:20]


# ── Full pipeline ──────────────────────────────────────────────────────────
def full_metadata_pipeline(image_bytes: bytes) -> dict:
    """
    Run the complete metadata analysis pipeline:
    1. Extract all metadata
    2. Analyze for hidden/encoded content
    3. Scan for embedded files
    Returns unified result.
    """
    metadata = extract_metadata(image_bytes)
    analysis = analyze_metadata(metadata)
    embedded = scan_embedded_files(image_bytes)

    return {
        "metadata": metadata,
        "analysis": analysis,
        "embedded_files": embedded,
        "summary": {
            "flags_found": analysis["flags_found"],
            "suspicious_fields": analysis["total_suspicious"],
            "total_fields": analysis["total_fields_scanned"],
            "embedded_files_count": len(embedded),
            "has_exif": bool(metadata["exif"]),
            "has_gps": bool(metadata["gps"]),
            "has_png_text": bool(metadata["png_text"]),
        },
    }
