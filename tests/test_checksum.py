"""Tests for ragahash.checksum — RagaChecksum-32."""

import pytest
from ragahash import ragachecksum, verify_checksum


class TestRagaChecksum:
    def test_output_fields(self):
        cs = ragachecksum(b"hello")
        assert "checksum" in cs
        assert "hex" in cs
        assert "raga_id" in cs
        assert "raga_name" in cs

    def test_hex_length(self):
        cs = ragachecksum(b"hello")
        assert len(cs["hex"]) == 8

    def test_hex_is_lowercase_hex(self):
        cs = ragachecksum(b"hello")
        assert all(c in "0123456789abcdef" for c in cs["hex"])

    def test_checksum_matches_hex(self):
        cs = ragachecksum(b"hello")
        assert f"{cs['checksum']:08x}" == cs["hex"]

    def test_deterministic(self):
        data = b"repeat"
        results = {ragachecksum(data)["hex"] for _ in range(5)}
        assert len(results) == 1

    def test_different_inputs_differ(self):
        a = ragachecksum(b"hello")["hex"]
        b = ragachecksum(b"Hello")["hex"]
        assert a != b

    def test_explicit_raga(self):
        cs = ragachecksum(b"test", raga_id=1)
        assert cs["raga_id"] == 1

    def test_auto_raga_from_length(self):
        data = b"x" * 10   # len=10 → raga (10%72)+1 = 11
        cs = ragachecksum(data)
        assert cs["raga_id"] == 11

    def test_invalid_raga_raises(self):
        with pytest.raises(ValueError):
            ragachecksum(b"data", raga_id=0)
        with pytest.raises(ValueError):
            ragachecksum(b"data", raga_id=73)

    def test_empty_input(self):
        cs = ragachecksum(b"")
        assert len(cs["hex"]) == 8

    def test_all_72_ragas(self):
        data = b"testing all ragas"
        hexes = [ragachecksum(data, r)["hex"] for r in range(1, 73)]
        # All 72 should produce valid 8-char hex
        assert all(len(h) == 8 for h in hexes)
        # At least most should be distinct
        assert len(set(hexes)) > 60


class TestVerifyChecksum:
    def test_correct_checksum_verifies(self):
        data = b"important data"
        cs = ragachecksum(data)
        assert verify_checksum(data, cs["hex"])

    def test_tampered_data_fails(self):
        data = b"important data"
        cs = ragachecksum(data)
        tampered = b"Important data"
        assert not verify_checksum(tampered, cs["hex"])

    def test_wrong_checksum_fails(self):
        data = b"hello"
        assert not verify_checksum(data, "deadbeef")

    def test_case_insensitive(self):
        data = b"case"
        cs = ragachecksum(data)
        assert verify_checksum(data, cs["hex"].upper())

    def test_whitespace_stripped(self):
        data = b"whitespace"
        cs = ragachecksum(data)
        assert verify_checksum(data, "  " + cs["hex"] + "\n")

    def test_explicit_raga_roundtrip(self):
        data = b"raga specific"
        cs = ragachecksum(data, raga_id=7)
        assert verify_checksum(data, cs["hex"], raga_id=7)

    def test_explicit_raga_wrong_raga_fails(self):
        data = b"raga specific"
        cs = ragachecksum(data, raga_id=7)
        # Using a different raga should (almost certainly) fail
        assert not verify_checksum(data, cs["hex"], raga_id=8)
