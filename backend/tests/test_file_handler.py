"""
Tests for file handler validation, custom metadata extractors, and edge cases.
"""
import io
import zipfile
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.tests.demo_dataset import generate_test_image
from backend.engine.file_handler import (
    sanitize_filename,
    validate_and_save_temp_file,
    cleanup_temp_file
)
from backend.stego.metadata_analyzer import extract_metadata

client = TestClient(app)


def test_sanitize_filename():
    assert sanitize_filename("normal.png") == "normal.png"
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("a/b/c.jpeg") == "c.jpeg"
    assert sanitize_filename("test space;$.png") == "test_space__.png"


class MockUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self._content = content
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._content


@pytest.mark.asyncio
async def test_file_validation_success():
    png_bytes = generate_test_image()
    mock_file = MockUploadFile("test.png", png_bytes, "image/png")
    
    # Normal PNG Validation
    temp_path, content = await validate_and_save_temp_file(
        mock_file,
        max_size=10 * 1024 * 1024,
        allowed_extensions={".png"},
        allowed_mime_types={"image/png"},
        validate_magic=True
    )
    assert temp_path is not None
    assert len(content) > 0
    cleanup_temp_file(temp_path)


@pytest.mark.asyncio
async def test_file_validation_empty():
    mock_file = MockUploadFile("empty.png", b"", "image/png")
    with pytest.raises(HTTPException) as exc:
        await validate_and_save_temp_file(mock_file, max_size=1024)
    assert exc.value.status_code == 400
    assert "Empty file" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_file_validation_large():
    mock_file = MockUploadFile("large.png", b"A" * 200, "image/png")
    with pytest.raises(HTTPException) as exc:
        await validate_and_save_temp_file(mock_file, max_size=100)
    assert exc.value.status_code == 413
    assert "File too large" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_file_validation_wrong_extension():
    png_bytes = generate_test_image()
    mock_file = MockUploadFile("test.txt", png_bytes, "image/png")
    with pytest.raises(HTTPException) as exc:
        await validate_and_save_temp_file(
            mock_file,
            max_size=10 * 1024 * 1024,
            allowed_extensions={".png"}
        )
    assert exc.value.status_code == 400
    assert "Unsupported file extension" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_file_validation_wrong_magic():
    # File has PNG name and MIME type, but contains random text
    mock_file = MockUploadFile("test.png", b"Not a PNG file", "image/png")
    with pytest.raises(HTTPException) as exc:
        await validate_and_save_temp_file(
            mock_file,
            max_size=10 * 1024 * 1024,
            allowed_extensions={".png"},
            allowed_mime_types={"image/png"},
            validate_magic=True
        )
    assert exc.value.status_code == 400
    assert "File signature" in exc.value.detail["message"]


def test_pdf_metadata_extractor():
    pdf_content = b"%PDF-1.5\n1 0 obj\n<< /Title (CTF Flag PDF) /Author (CyberAgent) >>\nendobj\n%%EOF"
    meta = extract_metadata(pdf_content)
    assert meta["file_info"]["format"] == "PDF Document"
    assert meta["exif"]["Title"] == "CTF Flag PDF"
    assert meta["exif"]["Author"] == "CyberAgent"
    assert meta["exif"]["PDF Version"] == "1.5"


def test_zip_metadata_extractor():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as z:
        z.writestr("flag.txt", "flag{zip_extracted_secret}")
    zip_bytes = zip_buffer.getvalue()
    
    meta = extract_metadata(zip_bytes)
    assert meta["file_info"]["format"] == "ZIP Archive"
    assert meta["file_info"]["files_count"] == 1
    # Check if files list is populated
    assert "ArchiveFile_0" in meta["exif"]
    assert "flag.txt" in meta["exif"]["ArchiveFile_0"]


def test_wav_metadata_extractor():
    # Simple valid WAV header (44 bytes format)
    wav_header = (
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    meta = extract_metadata(wav_header)
    assert meta["file_info"]["format"] == "WAV Audio"
    assert meta["file_info"]["channels"] == 1
    assert meta["exif"]["Sample Rate"] == "44100 Hz"


def test_appended_zip_detection():
    # Create PNG bytes
    png_bytes = generate_test_image()
    # Create ZIP bytes
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as z:
        z.writestr("hidden.txt", "flag{appended_zip_in_image}")
    zip_bytes = zip_buffer.getvalue()
    
    combined = png_bytes + zip_bytes
    
    # Run full metadata scan on combined bytes
    meta = extract_metadata(combined)
    # The scan_embedded_files (called by full scan endpoint) checks for PK\x03\x04 signature
    # Let's test the signature scanner directly
    from backend.stego.metadata_analyzer import scan_embedded_files
    embedded = scan_embedded_files(combined)
    
    assert len(embedded) > 0
    assert any(x["file_type"] == "ZIP archive" for x in embedded)


def test_api_file_analyze_png():
    png_bytes = generate_test_image()
    response = client.post(
        "/api/file/analyze",
        files={"file": ("evidence.png", png_bytes, "image/png")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sha256"] is not None
    assert data["entropy"] is not None
    assert data["magicBytes"].startswith("89 50 4E 47")
    assert len(data["strings"]) > 0
    assert "metadata" in data
    assert data["metadata"]["summary"]["flags_found"] is not None


def test_api_file_analyze_unsupported():
    response = client.post(
        "/api/file/analyze",
        files={"file": ("evidence.unknown", b"Some raw binary data here", "application/octet-stream")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "Unknown/Binary"
    assert data["entropy"] is not None
    assert len(data["strings"]) > 0


def test_api_stego_analyze_wrong_extension():
    # Upload PNG content, but name it test.txt
    png_bytes = generate_test_image()
    response = client.post(
        "/api/stego/analyze",
        files={"file": ("test.txt", png_bytes, "text/plain")},
        data={"bits": 1, "channels": "RGB"}
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]["message"]
