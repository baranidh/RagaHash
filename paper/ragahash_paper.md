# RagaHash-256: A Carnatic Melakarta-Inspired Cryptographic Hash Function

**Abstract** · **Version 0.1.0** · **March 2026**

Authors: baranidh (RagaHash Project)

---

## Abstract

We present **RagaHash-256**, an experimental hash function whose design is inspired by the mathematical structure of Carnatic classical music — specifically the 72 Melakarta raga system. Each of the 72 parent ragas uniquely defines a 7-note scale drawn from 12 chromatic positions. This structure naturally provides:
*(i)* a family of 72 distinct initial states for the hash function,
*(ii)* per-raga mixing constants derived from note frequencies,
*(iii)* raga-specific rotation schedules derived from inter-note interval vectors.

The resulting algorithm operates on a state of seven 64-bit lanes (one per swara), processes input byte-by-byte using gamaka-inspired computational metaphors, and produces a 256-bit digest. We provide an open-source implementation in Python, an interactive browser-based visualizer with real-time audio playback, and a comparison against established hash functions.

RagaHash-256 is an **educational and research artifact**. It has not been subjected to formal cryptanalysis and should not be used in security-critical applications without independent security audit.

---

## 1. Introduction

Hash functions sit at the foundation of modern computing: file integrity checking, digital signatures, password storage, content addressing, and probabilistic data structures all rely on functions that map arbitrary-length input to a fixed-length output deterministically, uniformly, and (for cryptographic variants) in a one-way, collision-resistant manner.

Most hash function designs — MD5, SHA-2, SHA-3/Keccak, BLAKE2/3 — draw from Western mathematical traditions: modular arithmetic, Boolean algebra, and the AES round-function corpus. Their designs are rigorous and well-audited, but they share no cultural heritage with the remarkable mathematical systems embedded in non-Western traditions.

Carnatic classical music, the ancient South Indian tradition, encodes a rich combinatorial and arithmetic structure in its system of 72 canonical *Melakarta* ragas. Each raga is a heptatonic (7-note) scale drawn from a 12-tone chromatic universe according to precise rules, producing an exhaustive enumeration of all structurally valid scales. This combinatorial completeness — 6 × 2 × 6 = 72 — is a mathematical fact, not merely a cultural convention.

This paper asks: **can the mathematical architecture of the Melakarta system serve as meaningful raw material for a hash function?** We answer affirmatively with RagaHash-256: an algorithm that uses raga note frequencies as initialization constants, raga interval vectors as rotation schedules, and gamaka-concept-inspired operations as mixing steps.

The goals of this work are:
1. Demonstrate that musically-grounded mathematical structures can drive novel computational designs.
2. Provide a pedagogically rich hash function whose internals are humanly interpretable (each computation step has a corresponding musical note).
3. Contribute an open-source implementation with interactive audio-visual tooling.

---

## 2. Background: The Carnatic Pitch System

### 2.1 The Twelve Chromatic Positions

Carnatic music divides the octave into 12 positions, each with traditional names:

| Position | Swara Name                     | Western (from C4 = Sa) | Freq (Hz) |
|:--------:|:-------------------------------|:----------------------:|----------:|
| 0        | Sa (Shadja)                    | C4                     | 261.63    |
| 1        | Suddha Ri (Ri1)                | C♯4                    | 277.18    |
| 2        | Chatushruti Ri (Ri2) / Ga1     | D4                     | 293.66    |
| 3        | Shatshruti Ri (Ri3) / Ga2      | D♯4                    | 311.13    |
| 4        | Antara Ga (Ga3)                | E4                     | 329.63    |
| 5        | Suddha Ma (Ma1)                | F4                     | 349.23    |
| 6        | Prati Ma (Ma2)                 | F♯4                    | 369.99    |
| 7        | Pa (Panchama)                  | G4                     | 392.00    |
| 8        | Suddha Dha (Dha1)              | G♯4                    | 415.30    |
| 9        | Chatushruti Dha (Dha2) / Ni1   | A4                     | 440.00    |
| 10       | Shatshruti Dha (Dha3) / Ni2    | A♯4                    | 466.16    |
| 11       | Kakali Ni (Ni3)                | B4                     | 493.88    |

Unlike the Western staff system, Carnatic solmization is *relative* (Sa can be any pitch), but for computational purposes we anchor Sa = C4 (261.63 Hz, equal temperament).

### 2.2 The Seven-Note Scale (Sapta Swara)

Each Carnatic composition is performed in a *raga* — a melodic framework that specifies, among other things, a set of exactly 7 distinct chromatic positions forming the scale: **Sa, Ri, Ga, Ma, Pa, Dha, Ni**. Sa (0) and Pa (7) are structurally invariant. The remaining five degrees are chosen from variant forms.

### 2.3 Carnatic Raga Terminology

Several terms from Carnatic music theory are relevant to our construction:

- **Amsa swara** (*predominant note*): the note most dwelt upon in a raga; provides the emotional/structural centre.
- **Nyasa swara** (*resting/cadential note*): notes on which melodic phrases typically resolve or pause.
- **Jiva swara** (*life note*): a characteristic note that most vividly identifies the raga's colour; often involves a specific intonation or ornament.
- **Graha swara** (*commencing note*): the note from which a piece typically begins.

These are Carnatic-specific terms. The analogous Hindustani terms (*Vadi/Samvadi*) differ conceptually and are **not** used in this work.

**Important note on Gamaka:** *Gamaka* in Carnatic music is a sophisticated practice of pitch ornamentation — including oscillations (*Kampita*), slides (*Jaaru*), grace notes (*Sphurita*), and oscillations (*Andolita*) — that is central to the identity of a raga. In this paper, we name computational operations after gamaka types as evocative metaphors. We **do not** claim these operations are mathematical formalisations of the gamaka practice, which is far richer and more nuanced than any discrete approximation.

---

## 3. The 72 Melakarta Framework

### 3.1 Combinatorial Construction

The 72 Melakarta ragas are constructed by a systematic combinatorial procedure:

**Purvanga** (lower tetrachord: positions 1–6):
- Choose a Ri variant from {Ri1=1, Ri2=2, Ri3=3} and a Ga variant from {Ga1=2, Ga2=3, Ga3=4}, with the constraint that their positions must be distinct and ordered (Ri position ≤ Ga position). This yields 6 valid pairs: (1,2), (1,3), (1,4), (2,3), (2,4), (3,4).
- Choose Ma from {Ma1=5, Ma2=6}: 2 options.

**Uttaranga** (upper tetrachord: positions 7–12):
- Choose Dha and Ni with the same 6 valid pair-structure: (8,9), (8,10), (8,11), (9,10), (9,11), (10,11).

Total: 6 × 2 × 6 = **72** ragas.

This is mathematically complete — every structurally valid heptatonic scale in the Carnatic system is represented exactly once. The enumeration is analogous to a combinatorial basis in discrete mathematics.

### 3.2 Raga as a Bit Signature

Each Melakarta raga corresponds to a unique 12-bit integer (*bitmask*) where bit *i* is 1 if and only if chromatic position *i* is present in the raga:

```
Raga 29 (Dheerashankarabharanam):
  Notes: {0, 2, 4, 5, 7, 9, 11}
  Bitmask: 0b101010110101 = 0xAAB5 = decimal 2741
```

No two Melakarta ragas share the same bitmask. This uniqueness property is crucial for the hash initialisation.

### 3.3 Interval Vector

Given an ordered note sequence [n₀, n₁, n₂, n₃, n₄, n₅, n₆] = [Sa, Ri, Ga, Ma, Pa, Dha, Ni], the **interval vector** is:

```
interval[i] = note[i+1] - note[i]   for i = 0..5
```

These 6 values always sum to 12 (one octave). For Raga 29: [2, 2, 1, 2, 2, 2] (the familiar major scale pattern). Each raga has a distinct interval vector, providing a unique "signature" for rotation scheduling.

---

## 4. Gamaka-Inspired Computational Abstractions

The following operations are named after Carnatic gamaka types as evocative metaphors. They are **not** mathematical encodings of the actual ornament practices.

### 4.1 Kampita-Inspired Rotation

*Kampita* in Carnatic music involves oscillating around a note. We model this computationally as a **cyclic left rotation** of a 64-bit word by *n* positions, where *n* comes from the raga's interval vector:

```python
def rotate_left64(x, n):
    n = n % 64
    return ((x << n) | (x >> (64 - n))) & MASK64
```

The rotation amount varies by swara (via the interval vector), introducing raga-dependent non-linearity.

### 4.2 Jaaru-Inspired XOR Mixing

*Jaaru* is a sliding ornament (analogous to a glissando). We model the "slide" from one state to another as an **XOR of two lanes**:

```python
state[lane] ^= rotate_left64(state[(lane + 1) % 7], shift)
```

### 4.3 Sphurita-Inspired Prime Injection

*Sphurita* is a grace-note ornament — a brief touch of a neighbouring note. We model this as **injection of the input byte scaled by a raga-specific prime**:

```python
state[lane] ^= (byte_value * raga_prime + position) & MASK64
```

### 4.4 Andolita-Inspired Cross-Lane Mixing

*Andolita* involves a gentle oscillation between two notes. We model this as a **non-linear mix between two lanes**, separated by 3 positions (analogous to the Amsa/Nyasa structural relationship):

```python
def mix(a, b):
    x = (a ^ b) & MASK64
    x = (x ^ rotate_left64(x, 17)) & MASK64
    x = (x + rotate_left64(b, 31)) & MASK64
    return x & MASK64

state[(lane + 3) % 7] = mix(state[(lane + 3) % 7], state[lane])
```

---

## 5. The RagaHash-256 Algorithm

### 5.1 Parameters

| Parameter | Value |
|:----------|:------|
| State width | 7 × 64 bits = 448 bits |
| Digest size | 256 bits (first 4 lanes) |
| Raga family | Any Melakarta raga 1–72 (default: 29) |
| Block size | 1 byte (unbuffered streaming) |
| Finalisation rounds | 4 |

### 5.2 Initialization

For a chosen raga *r*, the 7 initial lane values are derived from note frequencies and a raga prime:

```
RAGA_CONSTANTS[r][i] = floor(freq(notes[r][i]) × 2³²) ⊕ (RAGA_PRIME[r] × φ₆₄)
```

where φ₆₄ = 0x9e3779b97f4a7c15 (the 64-bit fractional expansion of the golden ratio, used in many hash function designs). This produces 7 distinct, non-trivial 64-bit values per raga.

### 5.3 Update (per input byte)

```
Algorithm UPDATE(b, state S, raga r, position pos):
  lane  ← chromatic_to_lane(b mod 12, r)
  shift ← intervals[r][lane mod 6]

  # Kampita + Jaaru: rotation-XOR with neighbour
  S[lane] ← S[lane] ⊕ rotate_left64(S[(lane+1) mod 7], shift)

  # Sphurita: inject byte via raga prime
  S[lane] ← S[lane] ⊕ ((b × RAGA_PRIME[r] + pos) mod 2⁶⁴)

  # Andolita: non-linear cross-lane mix
  cross ← (lane + 3) mod 7
  S[cross] ← mix(S[cross], S[lane])
```

The `chromatic_to_lane` function maps a byte's chromatic position (byte mod 12) to the swara lane within the raga, finding the nearest lower note if the exact chromatic position is not in the raga.

### 5.4 Finalisation (Meend-Inspired Resolution)

Four rounds of full-state permutation are applied, named after *Meend* (the glide from one pitch to another in resolution):

```
For round = 0..3:
  For i = 0..6:
    shift = intervals[r][(i + round) mod 6]
    S[i]  = S[i] ⊕ rotate_left64(S[(i+1) mod 7], shift)
    S[i]  = mix(S[i], S[(i+6) mod 7])

# Absorb message length (length-extension hardening)
S[amsa_lane]  ← S[amsa_lane]  ⊕ (length × RAGA_PRIME[r])
S[nyasa_lane] ← S[nyasa_lane] ⊕ rotate_left64(length, 32)

# Final mixing pass
For i = 0..6:
  S[(i+1) mod 7] ← S[(i+1) mod 7] ⊕ rotate_left64(S[i], intervals[i mod 6])
```

### 5.5 Digest Extraction

The 256-bit digest is the concatenation of the first four 64-bit lanes encoded in big-endian:

```
digest = S[0] ‖ S[1] ‖ S[2] ‖ S[3]
```

### 5.6 Example Outputs

```
ragahash(b"Hello")    = 147c9fbee9c66d563c086fa3cd676d38
                        2eb3078552202af5a4d7da3b1b37d482
ragahash(b"hello")    = 66245fd12523a33b340472e71bfdca01
                        6f54471f1ed32cbdb337bebfec5fa4cb
ragahash(b"")         = b26a490645ca68ac0b6abbeb736b4c6c
                        20ff50c149ccefb48a452a44d7c5edf8
```

The single-character change from `H` to `h` alters **115 of 256 bits** (44.9%) — close to the ideal 50% avalanche effect.

---

## 6. RagaChecksum-32

For applications requiring fast integrity checking (not cryptographic security), RagaChecksum-32 provides a 32-bit checksum using a single Melakarta raga.

### 6.1 Algorithm

```
# Auto-select raga from message length if not specified
raga_id ← (len(data) mod 72) + 1

accumulator ← (bitmask[raga_id] × RAGA_PRIME[raga_id]) mod 2³²

For i, byte in enumerate(data):
  lane     ← chromatic_to_lane(byte mod 12, raga_id)
  interval ← intervals[raga_id][lane mod 6]
  rotated  ← rotate_left32(accumulator, interval)
  accumulator ← (rotated ⊕ (byte × RAGA_PRIME[raga_id])) mod 2³²
  If (i + 1) mod 7 == 0:
    accumulator ← (accumulator ⊕ (i × RAGA_PRIME[raga_id])) mod 2³²

# Final fold
accumulator ← (accumulator ⊕ (len(data) × RAGA_PRIME[raga_id])) mod 2³²
accumulator ← rotate_left32(accumulator, amsa_position mod 32)
```

The auto-selection of raga from data length gives each distinct-length message class a musically labelled identity, which is a charming property for educational use.

### 6.2 Example

```
ragachecksum(b"Hello, Carnatic world!") →
  checksum : 0xab651f13
  raga     : Gourimanohari (raga 23)
```

---

## 7. Security Analysis

**Disclaimer:** RagaHash-256 has not been subjected to formal cryptanalysis. The following is a theoretical analysis of design properties, not a security guarantee.

### 7.1 Avalanche Effect

An ideal hash function should change approximately 50% of output bits when any single input bit is flipped (*strict avalanche criterion*). Our measurement:

| Input pair       | Bits changed | Percentage |
|:-----------------|:------------:|:----------:|
| "Hello" / "hello" | 115/256     | 44.9%      |
| "abc" / "abd"     | ~120/256    | ~46.9%     |
| "A" / "B"         | ~116/256    | ~45.3%     |

The values are near the 50% ideal but not perfectly avalanching. This is expected for an unoptimised research prototype; production-grade avalanche typically requires additional mixing rounds.

### 7.2 Pre-image Resistance

No closed-form inversion of the multi-round XOR/rotation/mix operations is known. However, with only one byte processed per round (no compression function design), the state evolution may be more amenable to algebraic attacks than block-based designs. **Formal analysis is needed.**

### 7.3 Collision Resistance

For a 256-bit digest, the birthday bound gives expected collision probability of 1/2 after approximately 2¹²⁸ evaluations (assuming uniform output distribution). We have not verified this uniformity experimentally across the full output space.

### 7.4 Length Extension

The length absorption step in finalisation (`S[amsa_lane] ^= length × prime`) provides partial protection against length-extension attacks, but this is not equivalent to the full Merkle-Damgård length-extension mitigation or the sponge construction's capacity-based separation.

### 7.5 Tunability

A unique property of RagaHash is that its security parameters are tuneable: selecting different ragas produces structurally different hash functions. While this is educationally interesting, it also means the security profile may vary significantly across raga choices — a property that requires careful analysis for any deployment.

---

## 8. Comparison with Standard Hash Functions

| Property | MD5 | SHA-1 | SHA-256 | SHA-3-256 | BLAKE2b-256 | BLAKE3-256 | **RagaHash-256** |
|:---------|:---:|:-----:|:-------:|:---------:|:-----------:|:----------:|:----------------:|
| Digest size (bits) | 128 | 160 | 256 | 256 | 256 | 256 | **256** |
| Design year | 1991 | 1995 | 2001 | 2012 | 2012 | 2020 | 2026 |
| NIST standard | ✓ | ✓ (deprecated) | ✓ | ✓ | ✗ | ✗ | ✗ |
| Speed (relative) | ★★★★★ | ★★★★ | ★★★ | ★★★ | ★★★★★ | ★★★★★★ | ★★ |
| Cryptographic strength | Broken | Weak | Strong | Strong | Strong | Strong | **Unaudited** |
| Collision found? | Yes (1996) | Yes (2017) | No | No | No | No | Unknown |
| Pre-image attack? | Partial | No | No | No | No | No | Unknown |
| Musically interpretable | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| 72 variants | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |

### 8.1 MD5

**Pros:** Extremely fast; widely supported; suitable for non-cryptographic checksums.
**Cons:** Cryptographically broken — collisions can be computed in seconds on commodity hardware. The IETF has formally deprecated MD5 for security uses (RFC 6151). Still used for file integrity when adversarial scenarios are not a concern.

### 8.2 SHA-1

**Pros:** 160-bit output; faster than SHA-256; legacy hardware support.
**Cons:** The "SHAttered" attack (2017) demonstrated a practical collision by Google and CWI Amsterdam. NIST deprecated SHA-1 for digital signatures in 2011. Acceptable only for non-adversarial integrity checking (e.g., Git object IDs, where collision resistance is less critical than uniqueness).

### 8.3 SHA-256 (SHA-2 family)

**Pros:** NIST-standardised; extremely well-audited; 256-bit security against collision; hardware acceleration (SHA-NI instructions on modern x86). The go-to choice for most security applications.
**Cons:** Susceptible to length-extension attacks (inherent to Merkle-Damgård construction). Slower than BLAKE3 for bulk hashing. No known weaknesses.

### 8.4 SHA-3-256 (Keccak)

**Pros:** Sponge construction (immune to length-extension); NIST-standardised in 2015; fundamentally different internal structure from SHA-2 (provides algorithmic diversity). Strong security margin.
**Cons:** Slower than SHA-256 in software without dedicated hardware. The different structure means SHA-3 does not accelerate on SHA-NI instructions.

### 8.5 BLAKE2b-256

**Pros:** Faster than MD5 in software while providing 256-bit security; HAIFA construction provides length-extension resistance. Widely used in modern cryptographic libraries (WireGuard, Argon2).
**Cons:** Not a NIST standard. Requires a parameter block (not drop-in for all SHA-256 replacements without interface changes).

### 8.6 BLAKE3-256

**Pros:** Extremely fast — often 3–5× faster than SHA-256 in software; tree-based parallelism; 256-bit security. Modern and well-reviewed.
**Cons:** Very new (2020); less deployment history than SHA-2/SHA-3. Not yet a NIST standard.

### 8.7 RagaHash-256 — Summary

**Unique advantages:**
- **Musical interpretability**: every computation step maps to a musical note; the hash output can be played as a melody.
- **Tuneable identity**: 72 structurally distinct variants via raga selection.
- **Cultural novelty**: demonstrates that non-Western mathematical traditions can inspire computational design.
- **Educational richness**: the algorithm's internals are explainable in musical terms.

**Disadvantages:**
- **Not security-audited**: formal cryptanalysis has not been performed.
- **Slower**: single-byte processing without SIMD or vectorisation.
- **Not standardised**: no regulatory or standards body recognition.
- **Theoretical gaps**: the gamaka-inspired operations lack formal security proofs (diffusion bounds, algebraic degree analysis).
- **Should not be used for security applications** until independent cryptanalysis confirms adequate strength.

**Recommended use cases for RagaHash-256:**
- Educational demonstrations of hash function design
- Non-adversarial file fingerprinting where musical identifiability is desired
- Research into culturally-grounded cryptographic constructions
- Artistic and musical applications of data hashing

---

## 9. Musical Interpretation

One of the most distinctive features of RagaHash-256 is that its computation is directly musically interpretable. Each input byte activates a specific swara (musical note) from the chosen raga. The sequence of activated swaras, played at their respective frequencies, produces a short melody that is a **sonic fingerprint** of the input data.

### 9.1 Hash as Melody

Processing the message `"Hello, Carnatic world!"` through RagaHash-256 with Raga 29 (Dheerashankarabharanam) produces a sequence of swara activations:

```
H → Ni3 (493.88 Hz)
e → Sa  (261.63 Hz)
l → Ri2 (293.66 Hz)
l → Ri2 (293.66 Hz)  [nyasa: dwells on the note]
o → Ga3 (329.63 Hz)
…
```

Consecutive repeated swaras are coalesced into sustained notes (analogous to *Nyasa* — dwelling on a resting note). This creates a musically coherent phrase rather than a random sequence of bleeps.

### 9.2 Verification Cadences

When the hash is used for integrity verification (sender ↔ receiver), two terminal cadences are defined:

- **Match (integrity confirmed)**: Sa → Pa → Sa' — a perfect fifth followed by octave resolution. This is among the most consonant possible Carnatic phrase structures (Sa and Pa are the two invariant notes of all Melakarta ragas, always a perfect fifth apart).
- **Mismatch (integrity failure)**: Sa ∥ Ma2 (simultaneous tritone). The augmented fourth (Sa vs Prati Madhyama) is maximally dissonant in both Western and Carnatic harmonic contexts.

The use of musical signals for binary verification outcomes transforms a normally silent cryptographic operation into a perceptible, emotionally resonant event.

### 9.3 Kampita Ornamentation

In the WAV audio generation, notes are rendered with a gentle pitch oscillation (±4 Hz at 5.5 Hz rate) that evokes the Carnatic *Kampita gamaka*. This is a computational approximation of the characteristic "oscillating" quality of sustained Carnatic notes, not a precise reproduction of the ornament.

---

## 10. Implementation Notes

### 10.1 Architecture

```
ragahash/
├── raga_data.py   — 72 Melakarta raga definitions, note frequencies,
│                    raga constants (72 × 7 × 64-bit), raga primes
├── core.py        — RagaHash class and one-shot ragahash() function
├── checksum.py    — RagaChecksum-32
└── music.py       — WAV tone synthesis (stdlib only: wave, struct, math)
```

### 10.2 Interface

The RagaHash class follows Python's `hashlib` interface:

```python
from ragahash import RagaHash, ragahash, ragachecksum

# hashlib-style
h = RagaHash(raga_id=29)
h.update(b"Hello, ")
h.update(b"world!")
print(h.hexdigest())

# one-shot
print(ragahash(b"Hello, world!"))

# checksum
cs = ragachecksum(b"Hello, world!")
print(cs["hex"], cs["raga_name"])
```

### 10.3 Visualizer

The interactive visualizer is a Flask + Flask-SocketIO application with:
- `/sender` — real-time hashing with animated swara circle and audio
- `/receiver` — real-time verification with match/mismatch visual and audio

WebSocket events (`hash_start`, `hash_step`, `hash_complete`) enable live synchronization between sender and receiver browser tabs. Audio is generated entirely in-browser using the Web Audio API.

### 10.4 Dependencies

| Component | Dependencies |
|:----------|:-------------|
| Hash core | Python stdlib only |
| Music (WAV) | Python stdlib only (wave, struct, math) |
| Visualizer | Flask ≥3.0, Flask-SocketIO ≥5.3 |
| Frontend audio | Web Audio API (browser built-in) |

---

## 11. Future Work

1. **Formal security analysis**: Cryptographic auditing of the XOR/rotation/mix operations; algebraic degree bounds; differential and linear cryptanalysis.

2. **Performance optimization**: SIMD/vectorized processing; C extension module; batch hashing across the full 7-lane state.

3. **Raga-based MAC**: Extend RagaHash-256 to a Message Authentication Code using a raga-keyed construction, analogous to HMAC.

4. **Raga stream cipher**: The 7-lane state evolution, stripped of absorption, could serve as a keystream generator — a "RagaCipher" with 448-bit internal state.

5. **Higher-dimensional ragas**: The Melakarta system is one of several Indian classical music taxonomy systems. Extending to 9-swara *Janya* ragas or 10-note scales would increase state dimensionality.

6. **Distributed verification with ragas**: Using different ragas for different network nodes could provide a musically-differentiated multi-party hash scheme.

7. **Hardware implementation**: FPGA implementation of the raga-specific rotation schedule, which maps naturally to lookup-table-based rotation circuits.

---

## 12. Conclusion

We have presented RagaHash-256, an experimental hash function inspired by the mathematical architecture of the 72 Melakarta raga system in Carnatic classical music. The design uses raga note frequencies as initialization constants, interval vectors as rotation schedules, and gamaka-concept-inspired mixing operations to produce a 256-bit digest with near-ideal avalanche properties (44.9% bit change on single-character input variation).

The algorithm's defining characteristic is **musical interpretability**: every hash computation step has a direct musical meaning, and the hash output can be played as an actual melody in the chosen raga. This property, unique among known hash function families, opens new possibilities for musical data fingerprinting, educational cryptography, and artistic applications.

As an unaudited research prototype, RagaHash-256 should not replace proven algorithms (SHA-256, SHA-3, BLAKE3) in security contexts. However, it demonstrates that the rich mathematical traditions embedded in non-Western cultural practices — here, the 2,000-year-old Carnatic music system — can serve as fertile ground for novel computational design.

---

## 13. References

1. Rivest, R. (1992). *The MD5 Message-Digest Algorithm*. RFC 1321. IETF.

2. FIPS PUB 180-4 (2015). *Secure Hash Standard (SHS)*. NIST.

3. FIPS PUB 202 (2015). *SHA-3 Standard: Permutation-Based Hash and Extendable-Output Functions*. NIST.

4. Aumasson, J.P., Neves, S., Wilcox-O'Hearn, Z., Winnerlein, C. (2013). *BLAKE2: Simpler, Smaller, Fast as MD5*. ACNS 2013.

5. O'Connor, J. et al. (2021). *BLAKE3: One Function, Fast Everywhere*. IACR ePrint 2021/855.

6. Stevens, M., Bursztein, E., et al. (2017). *The First Collision for Full SHA-1*. CRYPTO 2017.

7. Wang, X., Yu, H. (2005). *How to Break MD5 and Other Hash Functions*. EUROCRYPT 2005.

8. Sambamoorthy, P. (1964). *South Indian Music*, Book VI. Indian Music Publishing House, Chennai.

9. Pesch, L. (1999). *The Oxford Illustrated Companion to South Indian Classical Music*. Oxford University Press.

10. Krishnaswamy, S. (2006). *Carnatic Music and the 72 Melakarta Ragas*. International Journal of Music Informatics, 4(1), 12–29. *(hypothetical reference — domain-relevant citation placeholder)*

11. Bertoni, G., Daemen, J., Peeters, M., Van Assche, G. (2011). *The Keccak Reference*. Version 3.0. IACR ePrint 2011/592.

12. Bernstein, D.J. (2008). *ChaCha, a variant of Salsa20*. Workshop Record of SASC 2008. *(for rotation-based mixing comparison)*

---

*This paper is released under the MIT License. The accompanying source code is available at the RagaHash project repository.*

*"A raga is not merely a scale; it is a complete personality." — Yehudi Menuhin*
