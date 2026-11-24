"""
Secure file validation and temporary storage utilities.
"""
import os
import tempfile
import uuid
import re
from fastapi import HTTPException, UploadFile

from backend.stego.constants import (
    STEGO_ALLOWED_EXTENSIONS,
    STEGO_ALLOWED_MIME_TYPES,
    STEGO_ALLOWED_MAGICS,
    METADATA_ALLOWED_EXTENSIONS,
    METADATA_ALLOWED_MIME_TYPES,
    MAGIC_RIFF,
    MAGIC_WEBP_SUBTYPE,
    MAGIC_WAV_SUBTYPE,
    MAGIC_ZIP,
    MAGIC_ZIP_EMPTY,
    MAGIC_PDF,
)


def sanitize_filename(filename: str) -> str:
    """Never trust user-supplied filenames. Strip path traversal elements."""
    base = os.path.basename(filename)
    # Remove any non-alphanumeric, dot, dash or underscore characters
    sanitized = re.sub(r"[^\w\.\-]", "_", base)
    return sanitized


async def validate_and_save_temp_file(
    file: UploadFile,
    max_size: int,
    allowed_extensions: set = None,
    allowed_mime_types: set = None,
    validate_magic: bool = False
) -> tuple[str, bytes]:
    """
    Validates uploaded file size, extensions, MIME types, and magic bytes.
    Saves the file securely to a temporary file and returns (temp_path, content).
    """
    # 1. Read content
    content = await file.read()
    size = len(content)

    # 2. Check empty
    if size == 0:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Empty file uploaded."}
        )

    # 3. Check size
    if size > max_size:
        raise HTTPException(
            status_code=413,
            detail={
                "status": "error",
                "message": f"File too large. Max size allowed is {max_size / (1024 * 1024):.1f}MB."
            }
        )

    # 4. Check extension
    filename = file.filename or "unknown_file"
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if allowed_extensions and ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Unsupported file extension: {ext}. Allowed: {', '.join(allowed_extensions)}"
            }
        )

    # 5. Check MIME type
    if allowed_mime_types and file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Unsupported MIME type: {file.content_type}."
            }
        )

    # 6. Check magic bytes where appropriate
    if validate_magic:
        magic_match = False
        # Check standard headers
        for magic in STEGO_ALLOWED_MAGICS:
            if content.startswith(magic):
                # Specialize RIFF to WebP/WAV checks
                if magic == MAGIC_RIFF:
                    header = content[8:12]
                    if header in (MAGIC_WEBP_SUBTYPE, MAGIC_WAV_SUBTYPE):
                        magic_match = True
                        break
                else:
                    magic_match = True
                    break

        # ZIP & PDF checks
        if ext in (".zip", ".pdf", ".wav") or (file.content_type and "zip" in file.content_type) or (file.content_type and "pdf" in file.content_type):
            if content.startswith(MAGIC_ZIP) or content.startswith(MAGIC_ZIP_EMPTY) or content.startswith(MAGIC_PDF):
                magic_match = True

        if not magic_match:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "File signature/magic bytes do not match expected format."
                }
            )

    # 7. Write to a secure temporary file
    safe_ext = "".join(c for c in ext if c.isalnum() or c == ".")
    safe_name = f"{uuid.uuid4()}{safe_ext}"
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, safe_name)

    try:
        with open(temp_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Failed to store file temporarily: {str(e)}"}
        )

    return temp_path, content


def cleanup_temp_file(temp_path: str):
    """Safely deletes temporary file."""
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass
