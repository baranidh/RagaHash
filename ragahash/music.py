"""
music.py — Generate WAV audio from RagaHash computation steps.

Maps each swara activation during hash processing to a musical tone,
producing a short melody that is a sonic "fingerprint" of the input data.

Uses Python stdlib only (wave, struct, math) — no external audio libraries.

Carnatic touch: adds a slight kampita (oscillation) on sustained notes
to evoke the characteristic microtonal ornament of Carnatic music.
"""

import io
import math
import struct
import wave
from typing import Optional


SAMPLE_RATE = 44100
AMPLITUDE = 0.3       # 0.0–1.0  (avoid clipping)
KAMPITA_RATE = 5.5    # Hz of the pitch oscillation (vibrato-like)
KAMPITA_DEPTH = 4.0   # Hz deviation (±4 Hz around centre pitch)


# ---------------------------------------------------------------------------
# Low-level tone synthesis
# ---------------------------------------------------------------------------

def _sine_samples(
    freq: float,
    duration: float,
    sample_rate: int = SAMPLE_RATE,
    amplitude: float = AMPLITUDE,
    kampita: bool = True,
) -> list[float]:
    """
    Generate floating-point PCM samples for a tone at `freq` Hz.
    If `kampita` is True, applies a gentle pitch oscillation to the tone,
    inspired by the Kampita gamaka concept in Carnatic music.
    """
    n_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    phase_increment_base = 2.0 * math.pi * freq / sample_rate

    for i in range(n_samples):
        # Envelope: short attack + sustain + short release
        t = i / n_samples
        if t < 0.05:
            env = t / 0.05          # attack
        elif t > 0.85:
            env = (1.0 - t) / 0.15  # release
        else:
            env = 1.0               # sustain

        if kampita:
            # Modulate frequency slightly (oscillation around centre pitch)
            freq_mod = freq + KAMPITA_DEPTH * math.sin(2.0 * math.pi * KAMPITA_RATE * i / sample_rate)
            phase_increment = 2.0 * math.pi * freq_mod / sample_rate
        else:
            phase_increment = phase_increment_base

        phase += phase_increment
        samples.append(amplitude * env * math.sin(phase))

    return samples


def _samples_to_pcm16(samples: list[float]) -> bytes:
    """Convert float samples [-1, 1] to 16-bit signed PCM bytes."""
    return struct.pack(f"<{len(samples)}h", *(int(s * 32767) for s in samples))


def note_to_wav_bytes(
    freq: float,
    duration: float = 0.25,
    sample_rate: int = SAMPLE_RATE,
    kampita: bool = True,
) -> bytes:
    """
    Return WAV file bytes for a single note.
    Useful for downloading individual tones.
    """
    samples = _sine_samples(freq, duration, sample_rate, kampita=kampita)
    pcm = _samples_to_pcm16(samples)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Melody from hash steps
# ---------------------------------------------------------------------------

def steps_to_melody(
    steps: list[dict],
    tempo_bpm: float = 108.0,
    max_notes: int = 64,
    sample_rate: int = SAMPLE_RATE,
) -> bytes:
    """
    Convert a sequence of hash-step records (from ragahash_steps) into
    a WAV audio melody.

    Each step's swara frequency becomes one note. For readability, repeated
    consecutive swaras are coalesced into a single longer note (like a nyasa —
    dwelling on a note).

    Returns raw WAV file bytes.
    """
    beat_duration = 60.0 / tempo_bpm  # seconds per beat
    note_duration = beat_duration * 0.5  # each note = half a beat

    # Coalesce repeated consecutive swaras
    coalesced: list[tuple[float, int]] = []  # (freq, count)
    for step in steps[:max_notes]:
        freq = step["note_freq"]
        if coalesced and abs(coalesced[-1][0] - freq) < 0.1:
            coalesced[-1] = (freq, coalesced[-1][1] + 1)
        else:
            coalesced.append((freq, 1))

    all_samples: list[float] = []
    for freq, count in coalesced:
        # Longer dwelling on repeated notes (nyasa effect)
        duration = min(note_duration * count, note_duration * 3)
        samples = _sine_samples(freq, duration, sample_rate)
        # Small silence between notes (gap = 20% of note duration)
        gap_samples = int(sample_rate * note_duration * 0.2)
        all_samples.extend(samples)
        all_samples.extend([0.0] * gap_samples)

    if not all_samples:
        all_samples = [0.0] * 1024  # silence fallback

    pcm = _samples_to_pcm16(all_samples)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def save_melody(steps: list[dict], filepath: str, **kwargs) -> None:
    """Write the hash melody to a .wav file."""
    wav_bytes = steps_to_melody(steps, **kwargs)
    with open(filepath, "wb") as f:
        f.write(wav_bytes)
    print(f"[music] Melody saved to {filepath}")


# ---------------------------------------------------------------------------
# Verification / resolution cadences for the visualizer
# ---------------------------------------------------------------------------

def match_cadence(sample_rate: int = SAMPLE_RATE) -> bytes:
    """
    Sa–Pa–Sa ascending perfect fifth cadence: played when sender/receiver
    hashes MATCH. This is a classically resolved, consonant phrase.
    """
    sa = 261.63   # C4
    pa = 392.00   # G4
    sa2 = 523.25  # C5 (octave up)

    all_samples: list[float] = []
    for freq, dur in [(sa, 0.2), (pa, 0.2), (sa2, 0.4)]:
        all_samples.extend(_sine_samples(freq, dur, sample_rate, kampita=False))
        all_samples.extend([0.0] * int(sample_rate * 0.05))

    pcm = _samples_to_pcm16(all_samples)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def mismatch_cadence(sample_rate: int = SAMPLE_RATE) -> bytes:
    """
    Sa+Ma2 tritone clash: played when hashes MISMATCH.
    The augmented fourth (Sa vs Ma2 = F#) is maximally dissonant —
    historically called 'diabolus in musica'. In Carnatic contexts,
    Ma2 (Prati Madhyama) creates maximum tension against Sa.
    """
    sa = 261.63   # C4
    ma2 = 369.99  # F#4

    all_samples: list[float] = []
    # Play both simultaneously (mix)
    n = int(sample_rate * 0.5)
    s1 = _sine_samples(sa, 0.5, sample_rate, amplitude=0.2, kampita=False)
    s2 = _sine_samples(ma2, 0.5, sample_rate, amplitude=0.2, kampita=False)
    mixed = [a + b for a, b in zip(s1, s2)]
    all_samples.extend(mixed)

    pcm = _samples_to_pcm16(all_samples)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()
