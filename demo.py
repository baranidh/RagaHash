#!/usr/bin/env python3
"""
demo.py — RagaHash-256 command-line demonstration.

Shows:
  1. Basic hash computation
  2. Determinism check
  3. Avalanche effect table  (small input change → large hash change)
  4. RagaChecksum examples
  5. Step-by-step trace for a short message
  6. Comparison with hashlib (MD5, SHA-1, SHA-256)
  7. Music: generates demo_output.wav

Usage:
  python demo.py
  python demo.py --wav demo.wav   (specify output WAV path)
"""

import sys
import os
import hashlib
import time
import argparse

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))

from ragahash import ragahash, ragahash_steps, ragachecksum, verify_checksum, MELAKARTA_RAGAS
from ragahash.music import steps_to_melody, save_melody


# ── Terminal colour helpers ────────────────────────────────────────────────
def _c(text, code): return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text
def gold(t):  return _c(t, "33")
def green(t): return _c(t, "32")
def red(t):   return _c(t, "31")
def dim(t):   return _c(t, "2")
def bold(t):  return _c(t, "1")


def section(title: str) -> None:
    print()
    print(gold("━" * 60))
    print(bold(f"  {title}"))
    print(gold("━" * 60))


def bit_diff(h1: str, h2: str) -> int:
    """Count differing bits between two hex digests."""
    a = int(h1, 16)
    b = int(h2, 16)
    return bin(a ^ b).count("1")


# ── Demo sections ──────────────────────────────────────────────────────────

def demo_basic():
    section("1. Basic Hash Computation")
    test_inputs = [
        b"Hello, Carnatic world!",
        b"Sa Ri Ga Ma Pa Dha Ni",
        b"The quick brown fox jumps over the lazy dog",
        b"",
        b"\x00" * 32,
    ]
    for data in test_inputs:
        label = repr(data) if len(data) <= 30 else repr(data[:27]) + "...'"
        digest = ragahash(data)
        print(f"  {dim(label[:42]+'…' if len(str(label))>42 else label)}")
        print(f"  {gold(digest)}")
        print()


def demo_determinism():
    section("2. Determinism Check")
    msg = b"Dheerashankarabharanam"
    runs = [ragahash(msg) for _ in range(5)]
    all_same = len(set(runs)) == 1
    print(f"  Input : {repr(msg)}")
    print(f"  Hash  : {gold(runs[0])}")
    print(f"  5 runs identical: {green('YES ✓') if all_same else red('NO ✗')}")


def demo_avalanche():
    section("3. Avalanche Effect — Small Change, Big Hash Difference")
    pairs = [
        (b"Hello",       b"hello"),
        (b"abc",         b"abd"),
        (b"AAAA",        b"AAAB"),
        (b"Kanakangi",   b"Kanakangj"),
        (b"1234567890",  b"1234567891"),
    ]
    print(f"  {'Input A':<22} {'Input B':<22} {'Bits diff':>10}  {'%':>6}")
    print(f"  {'-'*22} {'-'*22} {'-'*10}  {'-'*6}")
    for a, b in pairs:
        ha = ragahash(a)
        hb = ragahash(b)
        diff = bit_diff(ha, hb)
        pct  = diff / 256 * 100
        bar  = gold("█" * int(pct / 5)) + dim("░" * (20 - int(pct / 5)))
        print(f"  {repr(a):<22} {repr(b):<22} {diff:>10}  {pct:>5.1f}%  {bar}")


def demo_raga_variants():
    section("4. Same Message, Different Ragas")
    msg = b"Om"
    ragas_to_show = [1, 15, 22, 29, 36, 65, 72]
    print(f"  Message: {repr(msg)}")
    print()
    print(f"  {'#':>3}  {'Raga Name':<25}  {'First 16 chars of digest'}")
    print(f"  {'-'*3}  {'-'*25}  {'-'*32}")
    for rid in ragas_to_show:
        h = ragahash(msg, raga_id=rid)
        name = MELAKARTA_RAGAS[rid]["name"]
        print(f"  {rid:>3}  {name:<25}  {gold(h[:32])}")


def demo_checksum():
    section("5. RagaChecksum-32")
    test_cases = [
        b"Hello, Carnatic world!",
        b"Kharaharapriya is the natural scale",
        b"",
        b"A" * 72,
    ]
    print(f"  {'Data (truncated)':<40}  {'Checksum':<10}  {'Raga'}")
    print(f"  {'-'*40}  {'-'*10}  {'-'*25}")
    for data in test_cases:
        cs = ragachecksum(data)
        label = repr(data[:35] + b"..." if len(data) > 35 else data)
        print(f"  {label:<40}  {gold(cs['hex']):<10}  {cs['raga_name']}")

    # Verify round-trip
    print()
    data = b"Integrity test payload"
    cs = ragachecksum(data)
    ok      = verify_checksum(data,          cs["hex"])
    tampered = verify_checksum(data + b"!",  cs["hex"])
    print(f"  Verify original  : {green('PASS ✓') if ok       else red('FAIL ✗')}")
    print(f"  Verify tampered  : {red('FAIL ✗ (correct)') if not tampered else green('PASS (unexpected!)')}")


def demo_steps(message: bytes = b"Sa Ri Ga"):
    section("6. Step-by-Step Hash Trace")
    print(f"  Message: {repr(message)}")
    print()
    steps = ragahash_steps(message)
    print(f"  {'Step':>4}  {'Byte':>4}  {'Char':>4}  {'Swara':<22}  {'Freq (Hz)':>10}  State[0][:16]")
    print(f"  {'-'*4}  {'-'*4}  {'-'*4}  {'-'*22}  {'-'*10}  {'-'*16}")
    for s in steps:
        print(
            f"  {s['step_index']:>4}  "
            f"{s['byte']:>4}  "
            f"  {s['char']:>2}  "
            f"{s['swara_name']:<22}  "
            f"{s['note_freq']:>10.2f}  "
            f"{gold(s['state_snapshot'][0][:16])}"
        )


def demo_comparison():
    section("7. Comparison with Standard Hash Functions")
    msg = b"Carnatic Music inspired Mathematics!"

    algorithms = [
        ("MD5",         lambda d: hashlib.md5(d).hexdigest(),          128, "Broken"),
        ("SHA-1",       lambda d: hashlib.sha1(d).hexdigest(),         160, "Deprecated"),
        ("SHA-256",     lambda d: hashlib.sha256(d).hexdigest(),       256, "Strong"),
        ("SHA-3-256",   lambda d: hashlib.sha3_256(d).hexdigest(),     256, "Strong"),
        ("BLAKE2b-256", lambda d: hashlib.blake2b(d, digest_size=32).hexdigest(), 256, "Strong"),
        ("RagaHash-256",ragahash,                                       256, "Unaudited"),
    ]

    print(f"  Input: {repr(msg)}\n")
    print(f"  {'Algorithm':<16}  {'Bits':>4}  {'Status':<12}  Digest (first 32 chars)")
    print(f"  {'-'*16}  {'-'*4}  {'-'*12}  {'-'*32}")

    timings = {}
    for name, fn, bits, status in algorithms:
        t0 = time.perf_counter()
        for _ in range(100):
            digest = fn(msg)
        elapsed = (time.perf_counter() - t0) / 100
        timings[name] = elapsed

        status_str = (green if status == "Strong" else red if status in ("Broken","Deprecated") else gold)(status)
        print(f"  {name:<16}  {bits:>4}  {status_str:<21}  {gold(digest[:32])}")

    print()
    print(f"  Relative timing (100 calls, μs per call):")
    base = timings.get("SHA-256", 1e-6)
    for name, t in timings.items():
        bar_len = max(1, min(30, int(t / base * 10)))
        bar = "█" * bar_len
        print(f"    {name:<16}  {t*1e6:>8.1f} μs  {dim(bar)}")


def demo_music(wav_path: str):
    section("8. Music Generation")
    msg = b"Dheerashankarabharanam"
    print(f"  Generating melody for: {repr(msg)}")
    steps = ragahash_steps(msg)

    note_names = [s['swara_name'].split('(')[0] for s in steps]
    print(f"  Note sequence: {' → '.join(note_names[:12])}{'…' if len(steps)>12 else ''}")

    save_melody(steps, wav_path, tempo_bpm=108)
    size_kb = os.path.getsize(wav_path) / 1024
    print(f"  WAV written: {green(wav_path)} ({size_kb:.1f} KB)")
    print(f"  Duration: ~{len(steps)*0.2:.1f}s (approx)")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RagaHash-256 Demo")
    parser.add_argument("--wav", default="demo_output.wav",
                        help="Output WAV file path (default: demo_output.wav)")
    args = parser.parse_args()

    print()
    print(bold(gold("  ██████╗  █████╗  ██████╗  █████╗ ██╗  ██╗ █████╗ ███████╗██╗  ██╗")))
    print(bold(gold("  ██╔══██╗██╔══██╗██╔════╝ ██╔══██╗██║  ██║██╔══██╗██╔════╝██║  ██║")))
    print(bold(gold("  ██████╔╝███████║██║  ███╗███████║███████║███████║███████╗███████║")))
    print(bold(gold("  ██╔══██╗██╔══██║██║   ██║██╔══██║██╔══██║██╔══██║╚════██║██╔══██║")))
    print(bold(gold("  ██║  ██║██║  ██║╚██████╔╝██║  ██║██║  ██║██║  ██║███████║██║  ██║")))
    print(bold(gold("  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝")))
    print()
    print(f"  {bold('RagaHash-256')} — Carnatic Melakarta-Inspired Hash Function")
    print(f"  {dim('An educational research prototype. Not for security-critical use.')}")

    demo_basic()
    demo_determinism()
    demo_avalanche()
    demo_raga_variants()
    demo_checksum()
    demo_steps()
    demo_comparison()
    demo_music(args.wav)

    section("Done")
    print(f"  To run the interactive visualizer:")
    print(f"  {gold('  pip install flask flask-socketio')}")
    print(f"  {gold('  python visualizer/app.py')}")
    print(f"  Then open: http://localhost:5000/sender  and  http://localhost:5000/receiver")
    print()


if __name__ == "__main__":
    main()
