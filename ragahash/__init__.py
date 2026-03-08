"""
ragahash — Carnatic Melakarta-inspired hash and checksum library.

Quick start::

    from ragahash import ragahash, ragachecksum

    digest = ragahash(b"Hello, Carnatic world!")
    print(digest)           # 64-char hex

    cs = ragachecksum(b"Some data")
    print(cs["hex"])        # 8-char hex
    print(cs["raga_name"])  # e.g. "Kharaharapriya"
"""

from .core import RagaHash, ragahash, ragahash_steps, DEFAULT_RAGA
from .checksum import ragachecksum, verify_checksum
from .raga_data import MELAKARTA_RAGAS, CHROMATIC_FREQUENCIES

__version__ = "0.1.0"
SWARA_FREQUENCIES = CHROMATIC_FREQUENCIES  # convenient alias

__all__ = [
    "RagaHash",
    "ragahash",
    "ragahash_steps",
    "ragachecksum",
    "verify_checksum",
    "MELAKARTA_RAGAS",
    "SWARA_FREQUENCIES",
    "DEFAULT_RAGA",
]
