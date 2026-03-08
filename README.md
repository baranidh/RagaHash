# RagaHash

**Carnatic Music inspired Mathematics !**

A hash function and checksum algorithm inspired by the mathematical structure of the 72 Melakarta raga system in Carnatic classical music — with interactive audio-visual demonstration.

---

## What is RagaHash?

**RagaHash-256** maps arbitrary bytes to a 256-bit digest using:
- The 72 Melakarta ragas as distinct hash-function variants (each raga = different initialization + rotation schedule)
- Raga note frequencies as initialization constants
- Interval vectors (gaps between consecutive scale degrees) as rotation schedules
- Gamaka-concept-inspired mixing operations (cyclic rotations, XOR mixing, prime injection)

Every byte of input activates a specific swara (musical note) from the chosen raga. The full hash computation can be played as a **melody** — giving each piece of data a unique musical identity.

---

## Quick Start

```bash
# Run demo (no extra deps needed for core hash)
python demo.py

# Run interactive visualizer
pip install flask flask-socketio
python visualizer/app.py
# Sender:   http://localhost:5000/sender
# Receiver: http://localhost:5000/receiver
```

---

## Usage

```python
from ragahash import ragahash, ragachecksum, verify_checksum

# 256-bit hash (default: Raga 29 — Dheerashankarabharanam)
digest = ragahash(b"Hello, Carnatic world!")
print(digest)  # 64-char hex

# Choose a specific raga
digest_kharaharapriya = ragahash(b"Hello", raga_id=22)  # Kharaharapriya

# 32-bit checksum (auto-selects raga from message length)
cs = ragachecksum(b"Some data")
print(cs["hex"])        # e.g. "ab651f13"
print(cs["raga_name"])  # e.g. "Gourimanohari"

# Verify integrity
ok = verify_checksum(b"Some data", cs["hex"])
print(ok)  # True

# hashlib-style stateful interface
from ragahash import RagaHash
h = RagaHash(raga_id=29)
h.update(b"Hello, ")
h.update(b"world!")
print(h.hexdigest())

# Step-by-step trace (for visualization / audio)
from ragahash import ragahash_steps
steps = ragahash_steps(b"Sa Ri Ga")
for s in steps:
    print(s["swara_name"], s["note_freq"], "Hz")
```

---

## Generate Music

```python
from ragahash import ragahash_steps
from ragahash.music import save_melody

steps = ragahash_steps(b"Om Namah Shivaya")
save_melody(steps, "hash_melody.wav", tempo_bpm=108)
```

---

## Project Structure

```
RagaHash/
├── paper/
│   └── ragahash_paper.md      # Technical paper
├── ragahash/
│   ├── __init__.py
│   ├── raga_data.py            # 72 Melakarta ragas + swara frequencies
│   ├── core.py                 # RagaHash-256 algorithm
│   ├── checksum.py             # RagaChecksum-32
│   └── music.py                # WAV melody generation
├── visualizer/
│   ├── app.py                  # Flask + SocketIO server
│   ├── templates/
│   │   ├── sender.html         # Hash input + animated swara circle
│   │   └── receiver.html       # Real-time verification + audio
│   └── static/
│       ├── style.css
│       └── raga_viz.js         # Canvas animation + Web Audio API
├── demo.py                     # CLI demonstration
└── requirements.txt
```

---

## The 72 Melakarta System

Carnatic music's 72 Melakarta ragas are a mathematically exhaustive enumeration of all valid 7-note scales from a 12-tone system:

- **6** valid Ri×Ga combinations (lower tetrachord)
- **× 2** Ma variants (Suddha Ma / Prati Ma)
- **× 6** Dha×Ni combinations (upper tetrachord)
- **= 72** ragas

Sa (0) and Pa (7) are invariant in all ragas. This combinatorial completeness makes the system a natural basis for a parameterized hash family.

---

## Disclaimer

RagaHash is an **educational research prototype**. It has not been formally cryptanalysed. Do not use it in security-critical applications. See the technical paper (`paper/ragahash_paper.md`) for a full comparison with SHA-256, SHA-3, BLAKE2, and BLAKE3.

---

## License

MIT License — Copyright (c) 2026 baranidh
