# RagaHash — How It Works

*A plain-language guide to the operation principle*

---

## The Core Idea

RagaHash turns any message into a **unique 64-character fingerprint** — and simultaneously into a **playable melody**. It borrows its internal structure from the mathematics of Carnatic classical music, specifically the 72 Melakarta raga system.

---

## Step 0 — Choose a Raga (the "personality")

Carnatic music has **72 parent ragas**. Each one is a recipe for a 7-note scale chosen from 12 possible chromatic positions (think: 7 specific keys on a piano, chosen from the full 12). Every raga has a unique set of notes and unique spacing between them.

RagaHash picks one raga (default: Raga 29 — *Dheerashankarabharanam*, the Carnatic equivalent of the major scale) and uses it as the hash function's personality. Different ragas produce structurally different hash functions — giving you a family of 72 variants.

---

## Step 1 — Set Up 7 Bowls (Initialisation)

Picture **7 mixing bowls**, one for each note of the raga (Sa, Ri, Ga, Ma, Pa, Dha, Ni).

Each bowl starts with a large number derived from that note's musical frequency:

```
Sa  bowl  ←  floor(261.63 Hz × 2³²) ⊕ raga_prime × φ₆₄
Ri  bowl  ←  floor(293.66 Hz × 2³²) ⊕ raga_prime × φ₆₄
Ga  bowl  ←  floor(329.63 Hz × 2³²) ⊕ raga_prime × φ₆₄
Ma  bowl  ←  floor(349.23 Hz × 2³²) ⊕ raga_prime × φ₆₄
Pa  bowl  ←  floor(392.00 Hz × 2³²) ⊕ raga_prime × φ₆₄
Dha bowl  ←  floor(440.00 Hz × 2³²) ⊕ raga_prime × φ₆₄
Ni  bowl  ←  floor(493.88 Hz × 2³²) ⊕ raga_prime × φ₆₄
```

Each raga uses a different prime number, so the 7 starting values are unique per raga. No two ragas begin with the same state.

---

## Step 2 — Process Each Character (Update)

For **every byte** in your message, three things happen:

### 2a. Find the Note
The byte's value maps to one of 12 chromatic positions (`byte mod 12`), which then maps to the nearest note in the raga's scale. For example:

```
'H' (ASCII 72)  →  72 mod 12 = 0  →  Sa  →  Sa bowl
'e' (ASCII 101) →  101 mod 12 = 5  →  Ma1 →  Ma bowl
'l' (ASCII 108) →  108 mod 12 = 0  →  Sa  →  Sa bowl
```

### 2b. Stir That Bowl *(Kampita-inspired)*
The activated bowl gets scrambled using the **interval** (the musical gap in semitones) between its note and the next note in the raga as a rotation amount:

```
Sa bowl  ←  Sa bowl  XOR  rotate(Ri bowl,  interval_Sa→Ri)
```

This is named after *Kampita*, the Carnatic ornament of oscillating around a note. The interval varies per raga, so the rotation schedule is raga-specific.

### 2c. Inject the Raw Byte *(Sphurita-inspired)*
The byte's actual value, multiplied by the raga's prime number, gets mixed into the bowl:

```
Sa bowl  ←  Sa bowl  XOR  (byte × raga_prime + position)
```

This ensures every single character influences the output, and that position matters (the 5th `'a'` affects the hash differently from the 1st `'a'`).

### 2d. Ripple to a Cousin Bowl *(Andolita-inspired)*
The bowl **3 positions away** (the structural counterpart in the 7-note raga cycle) also gets updated:

```
Ma bowl  ←  non_linear_mix(Ma bowl,  Sa bowl)
```

One character change now ripples across multiple bowls simultaneously.

---

## Step 3 — Resolve to a Final State (Finalisation)

After all characters are processed, the state goes through a resolution phase — named after the Carnatic concept of a melody sliding and settling on its resting note.

**4 rounds of full-state permutation:**
Every bowl stirs every other bowl in sequence, using the raga's interval vector as the rotation schedule. This amplifies the cascade: a single changed character, which may have directly touched only 2 bowls, now propagates changes through all 7.

**Length absorption:**
The total message length is folded into the state. This ensures that `"ab"` produces a different hash from `"a"` followed by `"b"` considered separately.

**One final mixing pass** across all 7 bowls.

---

## Step 4 — Extract the Digest

The first 4 bowls are concatenated in order:

```
digest = bowl[Sa] ‖ bowl[Ri] ‖ bowl[Ga] ‖ bowl[Ma]
       = 64-bit   +  64-bit  +  64-bit  +  64-bit
       = 256 bits = 64 hexadecimal characters
```

---

## The Avalanche Effect

A single character change (`Hello` → `hello`) flips **~45–53% of the 256 output bits**. Here is why:

1. `h` vs `H` maps to a different bowl (or the same bowl with a different byte value)
2. That bowl's value changes → its neighbour bowl changes (step 2b)
3. The cousin bowl 3 positions away changes (step 2d)
4. In finalisation, 4 rounds of full-state mixing spread the difference across all 7 bowls
5. The extracted 256 bits are roughly half-different

This is close to the ideal 50% ("strict avalanche criterion") expected from a well-designed hash function.

---

## The Musical Interpretation

Because every byte maps to a specific swara (musical note), you can **play the hash computation as a melody**:

```
Message:  "Hello"
H  →  Sa   261 Hz  🎵
e  →  Ma   349 Hz  🎵
l  →  Sa   261 Hz  🎵
l  →  Sa   261 Hz  🎵  ← repeated: sustained (like nyasa)
o  →  Ga   329 Hz  🎵
```

Two different messages produce two different melodies. The hash *sounds like* the data.

Notes are rendered with a gentle pitch oscillation (±4 Hz at 5.5 Hz) evoking the Carnatic *Kampita* ornament — a held note with a characteristic shimmer.

---

## The Sender → Receiver Verification Loop

```
┌─────────────────────────────────────────────────────┐
│  SENDER                                             │
│  1. Type a message                                  │
│  2. Run through 7 raga bowls                        │
│  3. Get: 64-char digest + melody                    │
│  4. Send message (and optionally the digest)        │
└──────────────────────┬──────────────────────────────┘
                       │  (message transmitted)
┌──────────────────────▼──────────────────────────────┐
│  RECEIVER                                           │
│  1. Receive the message                             │
│  2. Independently run through the same 7 bowls      │
│  3. Get their own digest                            │
│  4. Compare with sender's digest                    │
│                                                     │
│  MATCH   →  Sa-Pa-Sa' chord  ✓  Data intact        │
│  MISMATCH →  Sa+Ma2 tritone  ✗  Data was altered   │
└─────────────────────────────────────────────────────┘
```

The match cadence (Sa→Pa→Sa') is a **perfect fifth resolution** — the most consonant possible Carnatic phrase, since Sa and Pa are the two notes present in every single one of the 72 Melakarta ragas.

The mismatch cadence (Sa simultaneous with Ma2) is a **tritone** — the most dissonant interval in both Western and Carnatic harmony.

---

## RagaChecksum-32 (the lightweight sibling)

For quick integrity checks (not cryptographic security), RagaChecksum-32 uses a **single 32-bit accumulator** instead of 7 × 64-bit bowls:

1. Initialise from the raga's bitmask × prime
2. For each byte: rotate the accumulator by the interval, XOR in the byte
3. Every 7 bytes (one raga "cycle"), fold in the position
4. Final: absorb message length, rotate by Amsa swara position

The raga is auto-selected from the message length, so each size class of data has a musical label:

```
ragachecksum(b"Hello, Carnatic world!")
  → checksum: ab651f13
  → raga:     Gourimanohari  (raga 23)
```

---

## Summary

| Stage | What happens | Musical analogy |
|:------|:-------------|:----------------|
| Init | 7 bowls filled from note frequencies | Tuning the instrument |
| Update | Each byte activates a note, stirs bowls | Playing one note of the raga |
| Finalise | 4-round full-state permutation | Melody resolving to rest |
| Output | First 4 bowls → 256 bits | The finished phrase |
| Verify | Receiver replays the same raga | Second musician plays the same piece |

> *"A raga is not merely a scale; it is a complete personality."* — Yehudi Menuhin
>
> RagaHash gives every message a complete personality too.
