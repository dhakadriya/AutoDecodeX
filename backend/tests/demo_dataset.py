"""
Programmatic demo dataset generator for tests and experiments.
Generates encoded text samples, ciphers, and a real steganographic image.
"""
import io
import zlib
import gzip
import base64
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np

# Ground truth samples for evaluation
DATASET_SAMPLES = [
    # 1. Plaintext
    {
        "type": "plaintext",
        "input": "AutoDecodeX digital forensics framework version 2.0.",
        "expected": "AutoDecodeX digital forensics framework version 2.0.",
        "depth": 0
    },
    # 2. Base64
    {
        "type": "base64",
        "input": "QXV0b0RlY29kZVggZnJhbWV3b3JrIGlzIGFjdGl2ZS4=",
        "expected": "AutoDecodeX framework is active.",
        "depth": 1
    },
    # 3. Hex
    {
        "type": "hex",
        "input": "4365727461696e206465636f64652073756363657373",
        "expected": "Certain decode success",
        "depth": 1
    },
    # 4. URL encoding
    {
        "type": "url",
        "input": "AutoDecodeX%20CTF%20mode%20enabled%20%26%20active",
        "expected": "AutoDecodeX CTF mode enabled & active",
        "depth": 1
    },
    # 5. ROT13
    {
        "type": "rot13",
        "input": "Uryyb Sberafvpf naq Fgrtb",
        "expected": "Hello Forensics and Stego",
        "depth": 1
    },
    # 6. UUEncoding
    {
        "type": "uuencoding",
        "input": "begin 666 dummy.txt\n&2&5L;&\\`\nend",
        "expected": "Hello",
        "depth": 1
    },
    # 7. Zlib Deflate
    {
        "type": "zlib",
        "input": base64.b64encode(zlib.compress(b"zlib compression payload test")).decode(),
        "expected": "zlib compression payload test",
        "depth": 2 # Base64 then Zlib
    },
    # 8. Gzip
    {
        "type": "gzip",
        "input": base64.b64encode(gzip.compress(b"gzip compressed string output")).decode(),
        "expected": "gzip compressed string output",
        "depth": 2 # Base64 then Gzip
    },
    # 9. Multi-layer Base64 -> Hex
    {
        "type": "base64_hex",
        "input": base64.b64encode(b"48656c6c6f20576f726c64").decode(), # "Hello World" -> hex -> base64
        "expected": "Hello World",
        "depth": 2
    },
    # 10. Triple layer: Hex -> Base64 -> ROT13
    {
        "type": "triple_layer",
        "input": "Gur pqaSg9NfN2N5TjM5", # "flag{test}" -> hex -> base64 -> rot13
        "expected": "flag{test}",
        "depth": 3
    }
]

def generate_test_image() -> bytes:
    """
    Generate a 64x64 PNG image containing:
    - Custom metadata tEXt chunks (with base64 and hex ciphers)
    - LSB steganographic payload containing a flag
    """
    # 1. Create clean base image
    img = Image.new("RGB", (64, 64), color=(120, 150, 180))
    arr = np.array(img)

    # 2. Hide LSB Steganography payload
    # Payload is "flag{lsb_stego_extracted_successfully}"
    payload = b"flag{lsb_stego_extracted_successfully}\x00\x00\x00\x00"
    bits = []
    for b in payload:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)

    # Inject bits into R channel LSB
    flat_pixels = arr[:, :, 0].ravel()
    for idx, bit in enumerate(bits):
        if idx < len(flat_pixels):
            flat_pixels[idx] = (flat_pixels[idx] & ~1) | bit

    img_stego = Image.fromarray(arr)

    # 3. Add tEXt metadata chunk with Base64 encoded comment flag
    info = PngInfo()
    info.add_text("Comment", "ZmxhZ3toaWRkZW5faW5fbWV0YWRhdGF9") # flag{hidden_in_metadata}
    info.add_text("Author", "AutoDecodeX-Forensics")
    info.add_text("Description", "4379626572536563757269747920416e616c79736973") # "CyberSecurity Analysis" in hex

    # Save to memory buffer
    buf = io.BytesIO()
    img_stego.save(buf, format="PNG", pnginfo=info)
    return buf.getvalue()
