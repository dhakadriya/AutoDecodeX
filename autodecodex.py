#!/usr/bin/env python3
"""
AutoDecodeX CLI — autodecodex "encoded_string"
Usage:
    python autodecodex.py "SGVsbG8gV29ybGQ="
    python autodecodex.py "SGVsbG8gV29ybGQ=" --ctf
    python autodecodex.py "Uryyb Jbeyq" --brute-force caesar
"""
import sys
import os
import click

# Ensure backend is importable from project root
sys.path.insert(0, os.path.dirname(__file__))

from backend.engine.orchestrator import decode, brute_force_caesar, brute_force_xor
from backend.detectors.detector import detect_all


def _color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def green(t): return _color(t, "92")
def cyan(t): return _color(t, "96")
def yellow(t): return _color(t, "93")
def magenta(t): return _color(t, "95")
def red(t): return _color(t, "91")
def bold(t): return _color(t, "1")


@click.command()
@click.argument("input_text")
@click.option("--ctf", is_flag=True, default=False, help="Enable CTF mode (aggressive decoding)")
@click.option("--brute-force", "brute_force", type=click.Choice(["caesar", "xor"]), default=None,
              help="Run brute force module")
@click.option("--detect-only", is_flag=True, default=False, help="Only run detection, no decoding")
def main(input_text: str, ctf: bool, brute_force: str, detect_only: bool):
    """AutoDecodeX — Intelligent encoding detection and decoding."""
    print(bold(cyan("\n╔══════════════════════════════════════╗")))
    print(bold(cyan("║         AutoDecodeX v1.0.0           ║")))
    print(bold(cyan("╚══════════════════════════════════════╝\n")))

    print(f"{yellow('Input:')} {input_text[:120]}{'...' if len(input_text) > 120 else ''}\n")

    if detect_only:
        detections = detect_all(input_text)
        print(bold("Detection Results:"))
        for d in detections:
            bar = "█" * int(d['confidence'] * 20)
            print(f"  {cyan(d['type'].upper()): <20} {green(bar): <22} {yellow(str(int(d['confidence']*100)) + '%')}")
        return

    if brute_force == "caesar":
        print(bold(magenta("[ Caesar Cipher Brute Force ]")))
        results = brute_force_caesar(input_text)
        for r in results[:5]:
            score_bar = "█" * int(r['score'] * 20)
            print(f"  Shift {r['shift']:>2}: {green(r['decoded'][:80]): <85} Score: {yellow(score_bar)}")
        return

    if brute_force == "xor":
        print(bold(magenta("[ Single-Byte XOR Brute Force ]")))
        results = brute_force_xor(input_text)
        for r in results[:5]:
            print(f"  Key {r['key_hex']}: {green(r['decoded'][:80])} (score: {r['score']:.2f})")
        return

    # Main decode
    if ctf:
        print(bold(yellow("⚡ CTF Mode Enabled\n")))

    result = decode(input_text, ctf_mode=ctf)

    if result.steps:
        print(bold("Decoding Pipeline:"))
        for step in result.steps:
            bar = "█" * int(step.confidence * 20)
            print(f"  Step {step.step_number}: {cyan(step.encoding_type.upper()): <15} "
                  f"Confidence: {green(bar)} {yellow(str(int(step.confidence*100))+'%')}")
            print(f"           → {step.output_text[:100]}")
        print()

    print(bold("Path: ") + magenta(result.path_description))
    print(bold("Score: ") + yellow(f"{int(result.total_score * 100)}%"))

    if result.is_ctf_flag:
        print(bold(green("\n🚩 CTF FLAG DETECTED!")))

    print(bold("\nFinal Output:"))
    print(green(result.final_output))
    print()


if __name__ == "__main__":
    main()
