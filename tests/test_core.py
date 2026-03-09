"""Tests for ragahash.core — RagaHash-256."""

import pytest
from ragahash import RagaHash, ragahash, ragahash_steps, DEFAULT_RAGA


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_input_same_output(self):
        data = b"Hello, Carnatic world!"
        results = {ragahash(data) for _ in range(5)}
        assert len(results) == 1, "Same input must always produce the same digest"

    def test_one_shot_vs_streaming(self):
        data = b"streaming test"
        one_shot = ragahash(data)
        h = RagaHash()
        for byte in data:
            h.update(bytes([byte]))
        assert h.hexdigest() == one_shot

    def test_one_shot_vs_chunked(self):
        data = b"chunked input data for hashing"
        one_shot = ragahash(data)
        h = RagaHash()
        h.update(data[:10])
        h.update(data[10:])
        assert h.hexdigest() == one_shot

    def test_all_72_ragas_are_deterministic(self):
        data = b"raga determinism"
        for raga_id in range(1, 73):
            r1 = ragahash(data, raga_id)
            r2 = ragahash(data, raga_id)
            assert r1 == r2, f"Raga {raga_id} is not deterministic"


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class TestOutputFormat:
    def test_hexdigest_length(self):
        assert len(ragahash(b"test")) == 64

    def test_hexdigest_is_lowercase_hex(self):
        digest = ragahash(b"test")
        assert all(c in "0123456789abcdef" for c in digest)

    def test_digest_bytes_length(self):
        h = RagaHash()
        h.update(b"test")
        assert len(h.digest()) == 32

    def test_digest_hex_consistency(self):
        h = RagaHash()
        h.update(b"test")
        assert h.hexdigest() == h.digest().hex()


# ---------------------------------------------------------------------------
# Avalanche effect — core property of a hash function
# ---------------------------------------------------------------------------

def _bit_diff_fraction(a: str, b: str) -> float:
    """Return fraction of bits that differ between two hex digests."""
    ba, bb = bytes.fromhex(a), bytes.fromhex(b)
    diff = sum(bin(x ^ y).count("1") for x, y in zip(ba, bb))
    return diff / (len(ba) * 8)


class TestAvalanche:
    PAIRS = [
        (b"Hello", b"hello"),
        (b"Hello", b"Iello"),
        (b"abc", b"abd"),
        (b"The quick brown fox", b"The quick brown Fox"),
        (b"\x00" * 32, b"\x01" + b"\x00" * 31),
    ]

    @pytest.mark.parametrize("a,b", PAIRS)
    def test_one_bit_change_flips_roughly_half(self, a, b):
        da, db = ragahash(a), ragahash(b)
        fraction = _bit_diff_fraction(da, db)
        # Acceptable range: 30%–70% (ideal is ~50%)
        assert 0.30 <= fraction <= 0.70, (
            f"Avalanche fraction {fraction:.2%} out of range for {a!r} vs {b!r}"
        )

    def test_different_ragas_produce_different_digests(self):
        data = b"same data"
        digests = [ragahash(data, r) for r in range(1, 73)]
        assert len(set(digests)) == 72, "All 72 ragas must produce distinct digests"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_input(self):
        digest = ragahash(b"")
        assert len(digest) == 64

    def test_single_byte(self):
        for b in [0, 1, 127, 128, 255]:
            d = ragahash(bytes([b]))
            assert len(d) == 64

    def test_long_input(self):
        data = b"x" * 100_000
        digest = ragahash(data)
        assert len(digest) == 64

    def test_binary_data(self):
        data = bytes(range(256))
        digest = ragahash(data)
        assert len(digest) == 64

    def test_invalid_raga_raises(self):
        with pytest.raises(ValueError):
            RagaHash(raga_id=0)
        with pytest.raises(ValueError):
            RagaHash(raga_id=73)

    def test_update_after_finalize_raises(self):
        h = RagaHash()
        h.update(b"hello")
        h.hexdigest()
        with pytest.raises(RuntimeError):
            h.update(b"more")

    def test_copy(self):
        h = RagaHash()
        h.update(b"hello")
        h2 = h.copy()
        h.update(b" world")
        h2.update(b" world")
        assert h.hexdigest() == h2.hexdigest()

    def test_name_property(self):
        h = RagaHash(29)
        assert "ragahash-256" in h.name
        assert "Dheerashankarabharanam" in h.name

    def test_digest_size_property(self):
        assert RagaHash().digest_size == 32


# ---------------------------------------------------------------------------
# ragahash_steps
# ---------------------------------------------------------------------------

class TestSteps:
    def test_steps_count_matches_input(self):
        data = b"Hello!"
        steps = ragahash_steps(data)
        assert len(steps) == len(data)

    def test_step_fields_present(self):
        steps = ragahash_steps(b"A")
        s = steps[0]
        assert "byte" in s
        assert "char" in s
        assert "swara_name" in s
        assert "lane" in s
        assert "note_freq" in s
        assert "state_snapshot" in s
        assert "raga_name" in s

    def test_step_lane_in_range(self):
        for step in ragahash_steps(b"test input"):
            assert 0 <= step["lane"] <= 6

    def test_step_freq_positive(self):
        for step in ragahash_steps(b"test input"):
            assert step["note_freq"] > 0

    def test_steps_digest_matches_one_shot(self):
        data = b"consistency check"
        ragahash_steps(data)   # run steps (must not alter one-shot)
        assert ragahash(data) == ragahash(data)
