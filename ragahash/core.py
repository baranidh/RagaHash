"""
core.py — RagaHash-256: a Carnatic Melakarta-inspired hash function.

Algorithm overview
------------------
State:  S[7] — seven 64-bit lanes, one per swara of the chosen Melakarta raga.
Init:   S[i] = RAGA_CONSTANTS[raga_id][i]  (derived from note frequencies × prime)
Update: for each input byte b —
          lane  = chromatic_to_lane(b % 12, raga_id)
          shift = interval_vec[lane % 6]           (Kampita-inspired rotation)
          S[lane] ^= rotate_left64(S[(lane+1)%7], shift)
          S[lane] ^= (b * RAGA_PRIME) & MASK64
          S[(lane+3)%7] ^= _mix(S[(lane+3)%7], S[lane])  (Amsa/Nyasa cross-mixing)
Final:  4 rounds of full-state permutation (Jaaru-inspired slide to resolution)
        XOR in padded message length
        Digest = bytes(S[0]) + bytes(S[1]) + bytes(S[2]) + bytes(S[3])  → 32 bytes

Design notes
------------
- Gamaka-inspired operations are computational METAPHORS, not mathematical
  formalisations of the ornament practice in Carnatic music.
- The 7-lane width mirrors the 7 swaras of a Melakarta raga; each lane
  carries the "weight" of one degree of the scale.
- 256-bit output comes from concatenating the first four 64-bit lanes.
"""

import struct
from typing import Optional

from .raga_data import (
    MELAKARTA_RAGAS,
    RAGA_CONSTANTS,
    RAGA_PRIMES,
    chromatic_to_lane,
    get_swara_name,
    CHROMATIC_FREQUENCIES,
)

MASK64 = 0xFFFFFFFFFFFFFFFF
DEFAULT_RAGA = 29  # Dheerashankarabharanam — the Carnatic equivalent of the major scale


# ---------------------------------------------------------------------------
# Bit-level helpers
# ---------------------------------------------------------------------------

def _rotate_left64(x: int, n: int) -> int:
    n = n % 64
    if n == 0:
        return x & MASK64
    return ((x << n) | (x >> (64 - n))) & MASK64


def _mix(a: int, b: int) -> int:
    """Non-linear mixing of two 64-bit words."""
    x = (a ^ b) & MASK64
    x = (x ^ _rotate_left64(x, 17)) & MASK64
    x = (x + _rotate_left64(b, 31)) & MASK64
    return x & MASK64


# ---------------------------------------------------------------------------
# Core RagaHash class
# ---------------------------------------------------------------------------

class RagaHash:
    """
    Stateful hasher following the hashlib-style interface.

    Usage::

        h = RagaHash(raga_id=29)
        h.update(b"Hello, world!")
        print(h.hexdigest())

    Or one-shot::

        print(ragahash(b"Hello, world!"))
    """

    def __init__(self, raga_id: int = DEFAULT_RAGA):
        if not 1 <= raga_id <= 72:
            raise ValueError(f"raga_id must be in [1..72], got {raga_id}")
        self.raga_id = raga_id
        self._raga = MELAKARTA_RAGAS[raga_id]
        self._prime = RAGA_PRIMES[raga_id - 1]
        self._intervals = self._raga["intervals"]  # 6 values
        # Copy initial state from raga constants
        self._state: list[int] = list(RAGA_CONSTANTS[raga_id])
        self._length: int = 0
        self._finalized: bool = False
        self._final_state: Optional[list[int]] = None

    @property
    def name(self) -> str:
        return f"ragahash-256/{self._raga['name']}"

    @property
    def digest_size(self) -> int:
        return 32  # bytes

    def update(self, data: bytes) -> "RagaHash":
        """Process bytes into the hash state."""
        if self._finalized:
            raise RuntimeError("Cannot update a finalized RagaHash.")
        for b in data:
            self._process_byte(b)
            self._length += 1  # increment per byte so _length == position inside _process_byte
        return self

    def _process_byte(self, b: int) -> None:
        """Core per-byte transformation."""
        lane = chromatic_to_lane(b % 12, self.raga_id)
        shift = self._intervals[lane % 6]

        # Kampita-inspired: rotate neighbour lane into current
        self._state[lane] ^= _rotate_left64(self._state[(lane + 1) % 7], shift)

        # Sphurita-inspired: mix in the raw byte via raga prime
        self._state[lane] ^= (b * self._prime + self._length) & MASK64

        # Andolita-inspired: oscillation between Amsa and cross-lane
        cross = (lane + 3) % 7
        self._state[cross] = _mix(self._state[cross], self._state[lane])

    def _finalize(self) -> list[int]:
        """Apply finalisation permutation and return the 7-lane state."""
        S = list(self._state)  # copy — don't mutate

        # Jaaru-inspired: 4-round full-state permutation ("slide to resolution")
        for rnd in range(4):
            for i in range(7):
                shift = self._intervals[(i + rnd) % 6]
                S[i] ^= _rotate_left64(S[(i + 1) % 7], shift)
                S[i] = _mix(S[i], S[(i + 6) % 7])

        # Absorb message length (prevents length-extension in spirit)
        amsa_lane = self._raga["notes"].index(self._raga["amsa"]) if self._raga["amsa"] in self._raga["notes"] else 0
        nyasa_lane = self._raga["notes"].index(self._raga["nyasa"]) if self._raga["nyasa"] in self._raga["notes"] else 3
        S[amsa_lane] ^= (self._length * self._prime) & MASK64
        S[nyasa_lane] ^= _rotate_left64(self._length, 32)

        # One final mixing pass
        for i in range(7):
            S[(i + 1) % 7] ^= _rotate_left64(S[i], self._intervals[i % 6])

        return S

    def digest(self) -> bytes:
        """Return the 32-byte (256-bit) raw digest."""
        if not self._finalized:
            self._final_state = self._finalize()
            self._finalized = True
        # First 4 lanes → 32 bytes
        return struct.pack(">4Q", *self._final_state[:4])

    def hexdigest(self) -> str:
        """Return the 64-character hex digest string."""
        return self.digest().hex()

    def copy(self) -> "RagaHash":
        """Return a copy of the current hasher state."""
        if self._finalized:
            raise RuntimeError("Cannot copy a finalized RagaHash.")
        new = RagaHash.__new__(RagaHash)
        new.raga_id = self.raga_id
        new._raga = self._raga
        new._prime = self._prime
        new._intervals = self._intervals
        new._state = list(self._state)
        new._length = self._length
        new._finalized = False
        new._final_state = None
        return new


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def ragahash(data: bytes, raga_id: int = DEFAULT_RAGA) -> str:
    """One-shot RagaHash-256. Returns 64-character hex digest."""
    h = RagaHash(raga_id)
    h.update(data)
    return h.hexdigest()


def ragahash_steps(data: bytes, raga_id: int = DEFAULT_RAGA) -> list[dict]:
    """
    Process data and return a list of step-by-step trace records.
    Each record describes what happened when one byte was processed.
    Used by the visualizer and demo to animate the hash computation.

    Returns list of dicts:
        {
          "byte": int,           raw byte value
          "char": str,           printable character or '.'
          "swara_name": str,     e.g. "Ga(Ri3/Ga2)"
          "lane": int,           0-6
          "note_freq": float,    Hz of the activated swara
          "state_snapshot": list[str],  7 hex strings (64-bit each)
          "raga_name": str,
        }
    """
    h = RagaHash(raga_id)
    steps = []
    raga = MELAKARTA_RAGAS[raga_id]

    for i, b in enumerate(data):
        h._length = i  # track position before processing
        lane = chromatic_to_lane(b % 12, raga_id)
        note_pos = raga["notes"][lane]
        freq = CHROMATIC_FREQUENCIES[note_pos]
        swara_name = get_swara_name(lane, raga_id)

        h._process_byte(b)
        h._length = i + 1

        steps.append({
            "byte": b,
            "char": chr(b) if 32 <= b < 127 else ".",
            "swara_name": swara_name,
            "lane": lane,
            "note_freq": freq,
            "state_snapshot": [f"{v:016x}" for v in h._state],
            "raga_name": raga["name"],
            "step_index": i,
        })

    return steps
