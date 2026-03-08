"""
checksum.py — RagaChecksum-32: lightweight data-integrity checksum.

Lighter than RagaHash-256, designed for fast integrity checking (not
cryptographic security). Uses a single Melakarta raga's bitmask and
interval structure for accumulation.

Auto-selects raga from data length if none specified, giving the checksum
a pleasant musical identity for each distinct-length message.
"""

from .raga_data import MELAKARTA_RAGAS, RAGA_PRIMES, chromatic_to_lane

MASK32 = 0xFFFFFFFF


def _select_raga(data: bytes, raga_id: int | None) -> int:
    """Pick raga_id from data length if not explicitly provided."""
    if raga_id is not None:
        if not 1 <= raga_id <= 72:
            raise ValueError(f"raga_id must be in [1..72], got {raga_id}")
        return raga_id
    # Map length to a raga: distribute across 72 ragas
    return (len(data) % 72) + 1


def ragachecksum(data: bytes, raga_id: int | None = None) -> dict:
    """
    Compute a 32-bit RagaChecksum over data.

    Returns a dict with:
        checksum  : int   — raw 32-bit integer
        hex       : str   — 8-character hex string
        raga_id   : int   — which raga was used
        raga_name : str   — human-readable raga name
    """
    rid = _select_raga(data, raga_id)
    raga = MELAKARTA_RAGAS[rid]
    prime = RAGA_PRIMES[rid - 1]
    bitmask = raga["bitmask"]
    intervals = raga["intervals"]

    # Accumulator: start from raga bitmask spread into 32 bits
    acc = (bitmask * prime) & MASK32

    for i, b in enumerate(data):
        lane = chromatic_to_lane(b % 12, rid)
        interval = intervals[lane % 6]
        # Rotate accumulator by the interval, then mix in byte
        rotated = ((acc << interval) | (acc >> (32 - interval))) & MASK32
        acc = (rotated ^ (b * prime)) & MASK32
        # Every 7 bytes (one raga "cycle"), fold position in
        if (i + 1) % 7 == 0:
            acc = (acc ^ (i * prime)) & MASK32

    # Final fold: absorb length
    length_mix = (len(data) * prime) & MASK32
    acc = (acc ^ length_mix) & MASK32
    # One last rotation by Amsa position
    amsa_pos = raga["amsa"]
    acc = ((acc << (amsa_pos % 32)) | (acc >> (32 - (amsa_pos % 32)))) & MASK32

    return {
        "checksum": acc,
        "hex": f"{acc:08x}",
        "raga_id": rid,
        "raga_name": raga["name"],
    }


def verify_checksum(data: bytes, expected_hex: str, raga_id: int | None = None) -> bool:
    """
    Verify data against an expected checksum hex string.
    Returns True if the checksum matches, False otherwise.

    If raga_id is not provided, the raga is inferred from data length
    (same rule as ragachecksum).
    """
    result = ragachecksum(data, raga_id)
    return result["hex"].lower() == expected_hex.lower().strip()
