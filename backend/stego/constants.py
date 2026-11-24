"""
Magic byte signatures, MIME types, and file format constants for forensic analysis.
"""
from typing import Dict, List, Set

# Image Magic Bytes
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_BMP = b"BM"
MAGIC_GIF87A = b"GIF87a"
MAGIC_GIF89A = b"GIF89a"
MAGIC_RIFF = b"RIFF"
MAGIC_WEBP_SUBTYPE = b"WEBP"

# Audio Magic Bytes
MAGIC_WAV_SUBTYPE = b"WAVE"

# Archive and Document Magic Bytes
MAGIC_ZIP = b"PK\x03\x04"
MAGIC_ZIP_EMPTY = b"PK\x05\x06"
MAGIC_ZIP_SPANNED = b"PK\x07\x08"
MAGIC_PDF = b"%PDF-"
MAGIC_GZIP = b"\x1f\x8b"
MAGIC_7Z = b"7z\xbc\xaf\x27\x1c"
MAGIC_TAR_USTAR = b"ustar"

# PNG Chunk Identifiers (ASCII encoded bytes)
PNG_CHUNK_IHDR = b"IHDR"
PNG_CHUNK_PLTE = b"PLTE"
PNG_CHUNK_IDAT = b"IDAT"
PNG_CHUNK_IEND = b"IEND"
PNG_CHUNK_TEXT = b"tEXt"
PNG_CHUNK_ZTXT = b"zTXt"
PNG_CHUNK_ITXT = b"iTXt"

# Mapping of file format identifiers to their initial magic byte signatures
MAGIC_SIGNATURES: Dict[str, bytes] = {
    "png": MAGIC_PNG,
    "jpeg": MAGIC_JPEG,
    "bmp": MAGIC_BMP,
    "gif87a": MAGIC_GIF87A,
    "gif89a": MAGIC_GIF89A,
    "riff": MAGIC_RIFF,
    "zip": MAGIC_ZIP,
    "pdf": MAGIC_PDF,
    "gzip": MAGIC_GZIP,
    "7z": MAGIC_7Z,
}

# Allowed stego image types: PNG, JPEG, BMP, WebP
STEGO_ALLOWED_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
STEGO_ALLOWED_MIME_TYPES: Set[str] = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/bmp",
    "image/webp",
}
STEGO_ALLOWED_MAGICS: List[bytes] = [
    MAGIC_PNG,
    MAGIC_JPEG,
    MAGIC_BMP,
    MAGIC_RIFF,
]

# Allowed metadata forensic types (Images + ZIP + PDF + WAV)
METADATA_ALLOWED_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".bmp", ".webp",
    ".zip", ".pdf", ".wav",
}
METADATA_ALLOWED_MIME_TYPES: Set[str] = {
    "image/png", "image/jpeg", "image/jpg", "image/bmp", "image/webp",
    "application/zip", "application/x-zip-compressed",
    "application/pdf", "audio/wav", "audio/x-wav",
}
