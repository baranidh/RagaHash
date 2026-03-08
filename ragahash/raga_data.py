"""
raga_data.py — Carnatic Melakarta raga definitions and swara tables.

The 72 Melakarta system is a mathematically exhaustive enumeration of all
parent ragas in Carnatic music, based on combinatorial selection of note
variants across a 12-tone chromatic scale.

Terminology (Carnatic):
  Amsa swara  — the predominant/emphasized note of a raga
  Nyasa swara — the resting/cadential note (where phrases resolve)
  Jiva swara  — the "life" note that gives the raga its characteristic colour
  Graha swara — the commencing note of a composition in that raga

Note: "Vadi/Samvadi" are Hindustani terms and are NOT used here.
"""

import math

# ---------------------------------------------------------------------------
# 12-tone chromatic positions (Carnatic naming)
# ---------------------------------------------------------------------------
# Position : Swara name     : Western approx (from C4 = Sa)
#   0       Sa              C4
#   1       Suddha Ri (Ri1) C#4 / Db4
#   2       Chatushruti Ri (Ri2) / Suddha Ga (Ga1)  D4
#   3       Shatshruti Ri (Ri3) / Sadharana Ga (Ga2) D#4 / Eb4
#   4       Antara Ga (Ga3) E4
#   5       Suddha Ma (Ma1) F4
#   6       Prati Ma (Ma2)  F#4 / Gb4
#   7       Pa              G4
#   8       Suddha Dha (Dha1)  G#4 / Ab4
#   9       Chatushruti Dha (Dha2) / Suddha Ni (Ni1) A4
#  10       Shatshruti Dha (Dha3) / Kaisika Ni (Ni2)  A#4 / Bb4
#  11       Kakali Ni (Ni3) B4

CHROMATIC_NAMES = [
    "Sa", "Ri1", "Ri2/Ga1", "Ri3/Ga2", "Ga3",
    "Ma1", "Ma2", "Pa", "Dha1", "Dha2/Ni1", "Dha3/Ni2", "Ni3"
]

# Frequencies in Hz (equal temperament, A4=440Hz, Sa=C4)
CHROMATIC_FREQUENCIES = {
    0:  261.63,   # Sa   = C4
    1:  277.18,   # Ri1  = C#4
    2:  293.66,   # Ri2  = D4
    3:  311.13,   # Ri3/Ga2 = D#4
    4:  329.63,   # Ga3  = E4
    5:  349.23,   # Ma1  = F4
    6:  369.99,   # Ma2  = F#4
    7:  392.00,   # Pa   = G4
    8:  415.30,   # Dha1 = G#4
    9:  440.00,   # Dha2 = A4
    10: 466.16,   # Dha3/Ni2 = A#4
    11: 493.88,   # Ni3  = B4
}

# Short display names for the 7 swara positions within a raga
SWARA_POSITIONS = ["Sa", "Ri", "Ga", "Ma", "Pa", "Dha", "Ni"]

# ---------------------------------------------------------------------------
# 72 Melakarta Ragas
# Construction rule:
#   - Sa (0) and Pa (7) are always present (fixed)
#   - Purvanga (lower tetrachord): Sa + one of {Ri1,Ri2,Ri3} + one of {Ga1,Ga2,Ga3}
#     with constraint Ri_pos <= Ga_pos (no two notes share a chromatic position)
#     Valid (ri_chromatic, ga_chromatic) pairs:
#       (1,2), (1,3), (1,4), (2,3), (2,4), (3,4)  → 6 combinations
#   - Ma: either Ma1(5) or Ma2(6) → 2 variants
#   - Uttaranga (upper tetrachord): Pa + one of {Dha1,Dha2,Dha3} + one of {Ni1,Ni2,Ni3}
#     Same 6 valid combos: (8,9),(8,10),(8,11),(9,10),(9,11),(10,11)
#   Total: 6 × 2 × 6 = 72
# ---------------------------------------------------------------------------

def _build_melakarta():
    """Build all 72 Melakarta ragas programmatically."""
    # Purvanga pairs (ri_pos, ga_pos) — chromatic positions
    purvanga_pairs = [(1,2),(1,3),(1,4),(2,3),(2,4),(3,4)]
    # Uttaranga pairs (dha_pos, ni_pos)
    uttaranga_pairs = [(8,9),(8,10),(8,11),(9,10),(9,11),(10,11)]
    ma_variants = [5, 6]  # Ma1, Ma2

    # Traditional raga names (ordered by Melakarta number 1-72)
    raga_names = [
        "Kanakangi", "Ratnangi", "Ganamurthi", "Vanaspathi",
        "Manavathi", "Tanarupi", "Senavathi", "Hanumatodi",
        "Dhenuka", "Natakapriya", "Kokilapriya", "Rupavathi",
        "Gayakapriya", "Vakulabharanam", "Mayamalavagowla", "Chakravakam",
        "Suryakantam", "Hatakambari", "Jhankaradhwani", "Natabhairavi",
        "Keeravani", "Kharaharapriya", "Gourimanohari", "Varunapriya",
        "Mararanjani", "Charukesi", "Sarasangi", "Harikambhoji",
        "Dheerashankarabharanam", "Naganandini", "Yagapriya", "Ragavardhini",
        "Gangeyabhushani", "Vagadheeswari", "Shulini", "Chalanata",
        "Salagam", "Jalarnavam", "Jhalavarali", "Navaneetham",
        "Pavani", "Raghupriya", "Gavambodhi", "Bhavapriya",
        "Shubhapantuvarali", "Shadvidhamargini", "Suvarnangi", "Divyamani",
        "Dhavalambari", "Namanarayani", "Kamavardhini", "Ramapriya",
        "Gamanashrama", "Vishwambhari", "Shamalangi", "Shanmukhapriya",
        "Simhendramadhyamam", "Hemavathi", "Dharmavathi", "Neetimathi",
        "Kantamani", "Rishabhapriya", "Latangi", "Vachaspathi",
        "Mechakalyani", "Chitrambari", "Sucharitra", "Jyotiswarupini",
        "Dhatuvardani", "Nasikabhushani", "Kosalam", "Rasikapriya",
    ]

    ragas = {}
    idx = 1
    for ma in ma_variants:
        for ri, ga in purvanga_pairs:
            for dha, ni in uttaranga_pairs:
                notes = sorted([0, ri, ga, ma, 7, dha, ni])
                # Compute intervals between consecutive notes (6 gaps)
                intervals = [notes[i+1] - notes[i] for i in range(6)]

                # Amsa: note with largest interval above it (most "space" → emphasis)
                amsa_note_pos = notes[intervals.index(max(intervals))]

                # Nyasa: last note before Pa (cadence often resolves to Ga or Ma)
                nyasa_note_pos = notes[3]  # Ma position — common nyasa

                # Jiva: note with smallest interval (most chromatic tension)
                jiva_note_pos = notes[intervals.index(min(intervals))]

                # Graha: Sa (always 0 in Melakarta)
                graha_note_pos = 0

                ragas[idx] = {
                    "name": raga_names[idx - 1],
                    "notes": notes,           # 7 chromatic positions
                    "bitmask": sum(1 << n for n in notes),  # 12-bit
                    "intervals": intervals,    # 6 interval distances
                    "amsa": amsa_note_pos,
                    "nyasa": nyasa_note_pos,
                    "jiva": jiva_note_pos,
                    "graha": graha_note_pos,
                    "ma_variant": ma,
                }
                idx += 1
    return ragas


MELAKARTA_RAGAS = _build_melakarta()


# ---------------------------------------------------------------------------
# Raga constants for hash initialisation
# Derived from: floor(freq * 2^32) XOR prime
# Gives distinct, non-trivial 64-bit starting values per raga per swara lane
# ---------------------------------------------------------------------------

# 72 distinct primes (one per raga)
RAGA_PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
    31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
    127, 131, 137, 139, 149, 151, 157, 163, 167, 173,
    179, 181, 191, 193, 197, 199, 211, 223, 227, 229,
    233, 239, 241, 251, 257, 263, 269, 271, 277, 281,
    283, 293, 307, 311, 313, 317, 331, 337, 347, 349,
    353, 359,
]


def _build_raga_constants():
    """64-bit init values for each raga's 7 swara lanes."""
    constants = {}
    for raga_id, raga in MELAKARTA_RAGAS.items():
        prime = RAGA_PRIMES[raga_id - 1]
        lane_vals = []
        for note_pos in raga["notes"]:
            freq = CHROMATIC_FREQUENCIES[note_pos]
            val = int(freq * (2 ** 32)) ^ (prime * 0x9e3779b97f4a7c15)
            val &= 0xFFFFFFFFFFFFFFFF  # 64-bit mask
            lane_vals.append(val)
        constants[raga_id] = lane_vals
    return constants


RAGA_CONSTANTS = _build_raga_constants()


# ---------------------------------------------------------------------------
# Chromatic-position → swara-lane index mapper for a given raga
# ---------------------------------------------------------------------------

def chromatic_to_lane(chromatic_pos: int, raga_id: int) -> int:
    """
    Map a chromatic position to the swara lane index (0-6) within the raga.
    If the chromatic position is not in the raga, map to the nearest lower note.
    """
    notes = MELAKARTA_RAGAS[raga_id]["notes"]
    # Find nearest note in raga (modulo octave)
    pos = chromatic_pos % 12
    # Direct match
    if pos in notes:
        return notes.index(pos)
    # Find closest lower note (wrap around Sa if needed)
    for offset in range(1, 12):
        candidate = (pos - offset) % 12
        if candidate in notes:
            return notes.index(candidate)
    return 0  # fallback to Sa


def get_swara_name(lane_idx: int, raga_id: int) -> str:
    """Human-readable swara name for a lane index."""
    note_pos = MELAKARTA_RAGAS[raga_id]["notes"][lane_idx]
    base = SWARA_POSITIONS[lane_idx]
    chromatic = CHROMATIC_NAMES[note_pos]
    return f"{base}({chromatic})"
