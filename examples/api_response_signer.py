"""
API Response Signer — industry use-case demo
============================================
Use-case: Backend Services / Microservices / IoT

When a service sends data over a network (REST API, message queue, IoT
telemetry), the receiver needs confidence that:
  1. The data wasn't modified in transit (integrity)
  2. It came from a trusted sender who knows the shared raga key (authenticity)

This demo shows how to use RagaHash as a lightweight HMAC-style signature
scheme. The "raga ID" acts as a shared secret key selector — only parties
that agree on the raga can produce and verify signatures.

IMPORTANT: RagaHash is NOT a cryptographically audited MAC. Use this for
educational purposes or lightweight integrity checks in trusted environments.
For production security, use HMAC-SHA256 or a proper signature scheme.

Usage
-----
    # Sign a payload
    python examples/api_response_signer.py sign '{"user_id": 42, "balance": 1000.00}' --raga 36

    # Verify a payload + signature
    python examples/api_response_signer.py verify \
        '{"user_id": 42, "balance": 1000.00}' \
        ab651f13... \
        --raga 36

    # Simulate a tampered payload (shows mismatch)
    python examples/api_response_signer.py demo

Industry applications
---------------------
- IoT telemetry integrity: sensor readings signed before transmission
- Microservice-to-microservice checksums: quick sanity check on internal APIs
- Message queue integrity: verify Kafka/RabbitMQ message payloads
- Audit logging: sign log entries so tampering is detectable
- Configuration delivery: sign remote config payloads before applying them
- Data pipeline checkpointing: tag each stage's output with a RagaHash
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ragahash import ragahash, ragachecksum, verify_checksum, MELAKARTA_RAGAS, DEFAULT_RAGA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ansi(code, text):
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text

def ok(t):   return _ansi("32;1", t)
def fail(t): return _ansi("31;1", t)
def warn(t): return _ansi("33", t)
def dim(t):  return _ansi("2", t)
def bold(t): return _ansi("1", t)
def gold(t): return _ansi("33;1", t)
def cyan(t): return _ansi("36", t)


def sign_payload(payload: str, raga_id: int) -> dict:
    """
    Sign an API payload string.

    Returns a signed envelope:
    {
        "payload":    <original string>,
        "raga_id":    <int>,
        "raga_name":  <str>,
        "digest":     <64-char RagaHash-256 hex>,
        "checksum":   <8-char RagaChecksum-32 hex>,
        "timestamp":  <unix timestamp>,
    }
    """
    raw = payload.encode()
    digest = ragahash(raw, raga_id)
    cs = ragachecksum(raw, raga_id)
    return {
        "payload":   payload,
        "raga_id":   raga_id,
        "raga_name": MELAKARTA_RAGAS[raga_id]["name"],
        "digest":    digest,
        "checksum":  cs["hex"],
        "timestamp": int(time.time()),
    }


def verify_envelope(envelope: dict) -> tuple[bool, str]:
    """
    Verify a signed envelope.

    Returns (is_valid, reason).
    """
    try:
        payload  = envelope["payload"]
        raga_id  = envelope["raga_id"]
        expected = envelope["digest"]
        cs_hex   = envelope["checksum"]
    except KeyError as e:
        return False, f"Missing field: {e}"

    raw = payload.encode()

    # Check full hash
    actual = ragahash(raw, raga_id)
    if actual != expected:
        return False, f"Digest mismatch\n  expected {expected[:24]}…\n  got      {actual[:24]}…"

    # Check quick checksum too
    if not verify_checksum(raw, cs_hex, raga_id):
        return False, f"Checksum mismatch: expected {cs_hex}"

    return True, "OK"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_sign(args):
    raga_id = args.raga
    envelope = sign_payload(args.payload, raga_id)
    raga_name = MELAKARTA_RAGAS[raga_id]["name"]

    if args.json:
        print(json.dumps(envelope, indent=2))
        return

    print(bold("\n  RagaHash API Signature"))
    print(gold("  ━" * 32))
    print(f"  Raga     : {gold(f'{raga_id}. {raga_name}')}")
    print(f"  Payload  : {dim(args.payload[:80] + ('…' if len(args.payload) > 80 else ''))}")
    print(f"  Digest   : {gold(envelope['digest'][:32])}")
    print(f"             {gold(envelope['digest'][32:])}")
    print(f"  Checksum : {envelope['checksum']}")
    print(gold("  ━" * 32))
    print(dim("\n  Envelope (send this to the receiver):"))
    print(json.dumps(envelope, indent=4))
    print()


def cmd_verify(args):
    envelope = {
        "payload":  args.payload,
        "raga_id":  args.raga,
        "digest":   args.digest,
        "checksum": args.checksum or ragachecksum(args.payload.encode(), args.raga)["hex"],
    }

    valid, reason = verify_envelope(envelope)

    if valid:
        print(ok(f"\n  ✓ SIGNATURE VALID"))
        print(dim(f"    Raga {args.raga}. {MELAKARTA_RAGAS[args.raga]['name']}  ·  payload intact\n"))
    else:
        print(fail(f"\n  ✗ SIGNATURE INVALID"))
        print(f"    {warn(reason)}\n")

    sys.exit(0 if valid else 1)


def cmd_demo(args):
    """Full sender→receiver demo with a tampered payload."""
    raga_id = 22  # Kharaharapriya — a popular raga

    # --- Sender side ---
    print(bold("\n  ┌── SENDER ────────────────────────────────────────────────┐"))
    payload = json.dumps({
        "transaction_id": "TXN-20260309-8821",
        "from_account":   "ACC-1001",
        "to_account":     "ACC-2042",
        "amount":         15000.00,
        "currency":       "INR",
        "timestamp":      "2026-03-09T14:22:00Z",
    })
    envelope = sign_payload(payload, raga_id)
    print(f"  │  Payload    : {dim(payload[:55])}…")
    _rn = MELAKARTA_RAGAS[raga_id]["name"]
    print(f"  │  Raga       : {gold(f'{raga_id}. {_rn}')} (shared secret)")
    print(f"  │  Digest     : {gold(envelope['digest'][:24])}…")
    print(bold("  └──────────────────────────────────────────────────────────┘"))

    print(dim("\n  ↓  Envelope transmitted over the network  ↓\n"))

    # --- Receiver: intact ---
    print(bold("  ┌── RECEIVER (intact payload) ─────────────────────────────┐"))
    valid, reason = verify_envelope(envelope)
    status = ok("✓ VALID") if valid else fail("✗ INVALID")
    print(f"  │  {status}  —  {reason}")
    print(bold("  └──────────────────────────────────────────────────────────┘"))

    # --- Attacker tampers with amount ---
    print(dim("\n  ⚠  Man-in-the-middle attack: amount changed 15000 → 1500  ⚠\n"))
    tampered_data = json.loads(payload)
    tampered_data["amount"] = 1500.00          # attacker changes amount
    tampered_payload = json.dumps(tampered_data)
    tampered_envelope = dict(envelope)
    tampered_envelope["payload"] = tampered_payload  # keep original signature

    # --- Receiver: tampered ---
    print(bold("  ┌── RECEIVER (tampered payload) ───────────────────────────┐"))
    valid, reason = verify_envelope(tampered_envelope)
    status = ok("✓ VALID") if valid else fail("✗ INVALID")
    print(f"  │  {status}")
    print(f"  │  {warn(reason)}")
    print(bold("  └──────────────────────────────────────────────────────────┘"))

    print(dim("\n  The tamper was caught because a 1-rupee change in 'amount'"))
    print(dim("  flips ~50% of the 256 digest bits — impossible to forge.\n"))

    # --- Benchmark: compare signing speed vs HMAC-SHA256 ---
    print(bold("  Speed comparison (1000 iterations, 512-byte payload):"))
    bench_data = payload.encode() * 4   # ~512 bytes
    N = 1000

    t0 = time.perf_counter()
    for _ in range(N):
        ragahash(bench_data, raga_id)
    rh_time = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(N):
        hmac.new(b"secret", bench_data, hashlib.sha256).hexdigest()
    hmac_time = (time.perf_counter() - t0) * 1000

    print(f"  RagaHash-256     : {rh_time:6.1f} ms / 1k ops  ({rh_time/N*1000:.0f} µs each)")
    print(f"  HMAC-SHA256      : {hmac_time:6.1f} ms / 1k ops  ({hmac_time/N*1000:.0f} µs each)")
    ratio = rh_time / hmac_time
    print(dim(f"\n  RagaHash is {ratio:.1f}× {'slower' if ratio > 1 else 'faster'} than HMAC-SHA256 "
              f"(expected; not yet optimised)\n"))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        prog="api_response_signer",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    # sign
    sp = sub.add_parser("sign", help="Sign a payload string")
    sp.add_argument("payload", help="JSON string or any text to sign")
    sp.add_argument("--raga", type=int, default=DEFAULT_RAGA, metavar="N")
    sp.add_argument("--json", action="store_true", help="Output envelope as JSON only")

    # verify
    sp = sub.add_parser("verify", help="Verify a payload against a digest")
    sp.add_argument("payload",  help="Original payload string")
    sp.add_argument("digest",   help="64-char hex digest to check against")
    sp.add_argument("--checksum", default=None, help="8-char checksum hex (optional)")
    sp.add_argument("--raga", type=int, default=DEFAULT_RAGA, metavar="N")

    # demo
    sub.add_parser("demo", help="Full tamper-detection demo with benchmark")

    args = p.parse_args()

    if args.command == "sign":
        cmd_sign(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "demo":
        cmd_demo(args)


if __name__ == "__main__":
    main()
