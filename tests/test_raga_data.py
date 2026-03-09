"""Tests for ragahash.raga_data — Melakarta raga definitions."""

import pytest
from ragahash import MELAKARTA_RAGAS
from ragahash.raga_data import chromatic_to_lane, CHROMATIC_FREQUENCIES, RAGA_PRIMES


class TestMelakartas:
    def test_exactly_72_ragas(self):
        assert len(MELAKARTA_RAGAS) == 72

    def test_raga_ids_one_to_72(self):
        assert set(MELAKARTA_RAGAS.keys()) == set(range(1, 73))

    def test_each_raga_has_7_notes(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            assert len(raga["notes"]) == 7, f"Raga {rid} has {len(raga['notes'])} notes"

    def test_sa_and_pa_always_present(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            assert 0 in raga["notes"], f"Raga {rid} missing Sa (0)"
            assert 7 in raga["notes"], f"Raga {rid} missing Pa (7)"

    def test_notes_within_octave(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            for note in raga["notes"]:
                assert 0 <= note <= 11, f"Raga {rid} has out-of-range note {note}"

    def test_notes_are_sorted(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            assert raga["notes"] == sorted(raga["notes"]), f"Raga {rid} notes not sorted"

    def test_notes_are_unique(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            assert len(raga["notes"]) == len(set(raga["notes"])), \
                f"Raga {rid} has duplicate notes"

    def test_intervals_span_note_range(self):
        # 6 intervals between 7 notes: sum = notes[-1] - notes[0]
        for rid, raga in MELAKARTA_RAGAS.items():
            expected = raga["notes"][-1] - raga["notes"][0]
            got = sum(raga["intervals"])
            assert got == expected, \
                f"Raga {rid}: intervals sum {got} != note range {expected}"

    def test_each_raga_has_a_name(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            assert isinstance(raga["name"], str) and len(raga["name"]) > 0

    def test_all_raga_names_unique(self):
        names = [r["name"] for r in MELAKARTA_RAGAS.values()]
        assert len(names) == len(set(names))

    def test_ragas_1_to_36_use_ma1(self):
        for rid in range(1, 37):
            assert 5 in MELAKARTA_RAGAS[rid]["notes"], \
                f"Raga {rid} (first half) should contain Ma1 (5)"

    def test_ragas_37_to_72_use_ma2(self):
        for rid in range(37, 73):
            assert 6 in MELAKARTA_RAGAS[rid]["notes"], \
                f"Raga {rid} (second half) should contain Ma2 (6)"

    def test_bitmask_encodes_notes(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            expected = sum(1 << n for n in raga["notes"])
            assert raga["bitmask"] == expected, f"Raga {rid} bitmask mismatch"

    def test_amsa_is_in_notes(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            assert raga["amsa"] in raga["notes"], \
                f"Raga {rid} amsa {raga['amsa']} not in notes"

    def test_nyasa_is_in_notes(self):
        for rid, raga in MELAKARTA_RAGAS.items():
            assert raga["nyasa"] in raga["notes"], \
                f"Raga {rid} nyasa {raga['nyasa']} not in notes"


class TestChromaticToLane:
    def test_direct_hits_return_correct_lane(self):
        # Raga 29: Dheerashankarabharanam = [0,2,4,5,7,9,11]
        raga = MELAKARTA_RAGAS[29]
        for lane, pos in enumerate(raga["notes"]):
            assert chromatic_to_lane(pos, 29) == lane

    def test_result_always_in_range(self):
        for raga_id in range(1, 73):
            for pos in range(12):
                lane = chromatic_to_lane(pos, raga_id)
                assert 0 <= lane <= 6, \
                    f"Lane {lane} out of range for raga {raga_id}, pos {pos}"

    def test_sa_always_lane_0(self):
        for raga_id in range(1, 73):
            lane = chromatic_to_lane(0, raga_id)
            assert lane == 0, f"Sa should always be lane 0 in raga {raga_id}"

    def test_pa_always_lane_4(self):
        for raga_id in range(1, 73):
            lane = chromatic_to_lane(7, raga_id)
            assert lane == 4, f"Pa should always be lane 4 in raga {raga_id}"

    def test_bidirectional_search(self):
        # In raga 36 (Chalanata), notes = [0,3,4,5,7,10,11]
        # pos=2 is not in notes; nearest is 3 (1 up) not 0 (2 down)
        raga36_notes = MELAKARTA_RAGAS[36]["notes"]
        assert 2 not in raga36_notes
        lane = chromatic_to_lane(2, 36)
        note_at_lane = raga36_notes[lane]
        # Should map to 3 (distance 1 up) not 0 (distance 2 down)
        assert note_at_lane == 3, \
            f"Expected nearest note 3, got {note_at_lane} (bidirectional search failed)"


class TestChromatic:
    def test_12_chromatic_positions(self):
        assert len(CHROMATIC_FREQUENCIES) == 12

    def test_sa_is_c4(self):
        assert abs(CHROMATIC_FREQUENCIES[0] - 261.63) < 0.1

    def test_pa_is_g4(self):
        assert abs(CHROMATIC_FREQUENCIES[7] - 392.00) < 0.1

    def test_frequencies_ascending(self):
        freqs = [CHROMATIC_FREQUENCIES[i] for i in range(12)]
        assert freqs == sorted(freqs)


class TestRagaPrimes:
    def test_exactly_72_primes(self):
        assert len(RAGA_PRIMES) == 72

    def test_all_are_prime(self):
        def is_prime(n):
            if n < 2: return False
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0: return False
            return True
        for p in RAGA_PRIMES:
            assert is_prime(p), f"{p} is not prime"

    def test_all_unique(self):
        assert len(RAGA_PRIMES) == len(set(RAGA_PRIMES))
