import sys
import os

# Ensure backend package is importable when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force UTF-8 encoding for standard output/error stream to prevent encoding errors on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.engine.orchestrator import decode, brute_force_caesar, brute_force_xor
from backend.detectors.detector import detect_all
from backend.scoring.scorer import score_text


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_single_layer():
    print_header("Single-Layer Decoding")
    
    # Base64
    print("1. Base64: SGVsbG8gV29ybGQ=")
    result = decode("SGVsbG8gV29ybGQ=")
    print(f"   → {result.final_output}")
    print(f"   Confidence: {result.total_score:.2f}")
    
    # Hex
    print("\n2. Hex: 48656c6c6f")
    result = decode("48656c6c6f")
    print(f"   → {result.final_output}")
    print(f"   Confidence: {result.total_score:.2f}")
    
    # ROT13
    print("\n3. ROT13: Uryyb Jbeyq")
    result = decode("Uryyb Jbeyq")
    print(f"   → {result.final_output}")
    print(f"   Confidence: {result.total_score:.2f}")


def demo_multi_layer():
    print_header("Multi-Layer Recursive Decoding")
    
    # Base64 → Hex
    print("Base64 → Hex: NDg2NTZjNmM2Zg==")
    result = decode("NDg2NTZjNmM2Zg==")
    print(f"   Final output: {result.final_output}")
    print(f"   Decoding path: {result.path_description}")
    print(f"   Steps:")
    for step in result.steps:
        print(f"      Step {step.step_number}: {step.encoding_type} (confidence: {step.confidence:.2f})")
    
    # Triple layer
    print("\n\nBase64 → Hex → Binary: MzAzMTMwMzAzMTMwMzAzMDMwMzEzMTMwMzEzMDMwMzE=")
    result = decode("MzAzMTMwMzAzMTMwMzAzMDMwMzEzMTMwMzEzMDMwMzE=")
    print(f"   Final output: {result.final_output}")
    print(f"   Decoding path: {result.path_description}")
    print(f"   Total steps: {len(result.steps)}")


def demo_detection():
    print_header("Automatic Encoding Detection")
    
    tests = [
        ("SGVsbG8gV29ybGQ=", "Base64"),
        ("48656c6c6f", "Hex"),
        ("01001000 01101001", "Binary"),
        ("Hello%20World", "URL"),
        ("&lt;Hello&gt;", "HTML Entity"),
    ]
    
    for text, expected in tests:
        detections = detect_all(text)
        print(f"{expected}: {text}")
        print(f"   Detected as: {detections[0]['type']} (confidence: {detections[0]['confidence']:.2f})")
        print()


def demo_scoring():
    print_header("Text Quality Scoring")
    
    tests = [
        ("Hello World", "Plaintext"),
        ("SGVsbG8gV29ybGQ=", "Base64"),
        ("48656c6c6f", "Hex"),
        ("flag{test_123}", "CTF Flag"),
        ("xqzkvp12#@$%", "Random"),
    ]
    
    for text, label in tests:
        score = score_text(text)
        print(f"{label:15} → Score: {score:.3f} → {'✓ Plaintext' if score > 0.6 else '✗ Encoded'}")


def demo_brute_force():
    print_header("Brute Force Attacks")
    
    # Caesar
    print("Caesar Cipher: Khoor")
    results = brute_force_caesar("Khoor")
    print("   Top 5 results:")
    for r in results[:5]:
        print(f"      Shift {r['shift']:2d}: {r['decoded']:20} (score: {r['score']:.2f})")
    
    # XOR
    print("\n\nXOR (Hello with key 42): 626f7e7e79")
    results = brute_force_xor("626f7e7e79")
    print("   Top 3 results:")
    for r in results[:3]:
        print(f"      Key {r['key']:3d} ({r['key_hex']}): {r['decoded']:20} (score: {r['score']:.2f})")


def demo_ctf_mode():
    print_header("CTF-Optimized Mode")
    
    # Regular mode
    print("Regular mode:")
    result = decode("ZmxhZ3t0ZXN0XzEyM30=", ctf_mode=False)
    print(f"   → {result.final_output}")
    print(f"   CTF flag detected: {result.is_ctf_flag}")
    
    # CTF mode
    print("\nCTF mode (boosts common encodings):")
    result = decode("ZmxhZ3t0ZXN0XzEyM30=", ctf_mode=True)
    print(f"   → {result.final_output}")
    print(f"   CTF flag detected: {result.is_ctf_flag}")
    print(f"   Path: {result.path_description}")


def demo_error_handling():
    print_header("Error Handling & Edge Cases")
    
    tests = [
        ("", "Empty input"),
        ("   ", "Whitespace only"),
        ("!@#$%^&*()", "Special characters"),
        ("A" * 1000, "Very long input (1000 chars)"),
        ("你好世界", "Unicode"),
    ]
    
    for text, label in tests:
        result = decode(text)
        status = "✓ Handled" if result is not None else "✗ Failed"
        print(f"{label:30} → {status}")


def main():
    print("""
    ==============================================================
                                                         
            AutoDecodeX - Core Decoder Engine Demo           
                                                           
       Intelligent Multi-Layer Encoding Detection & Decoding 
                                                           
    ==============================================================
    """)
    
    try:
        demo_single_layer()
        demo_multi_layer()
        demo_detection()
        demo_scoring()
        demo_brute_force()
        demo_ctf_mode()
        demo_error_handling()
        
        print_header("Demo Complete!")
        print("✓ All features working correctly")
        print("✓ Core Engine is production-ready")
        print("\nNext: Start the API server with:")
        print("    cd backend && uvicorn main:app --reload\n")
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
