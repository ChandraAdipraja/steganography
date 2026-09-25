import hashlib

import numpy as np
import pytest

from src.prng import derive_prng_seed, generate_positions


def test_deterministic_same_seed():
    first = generate_positions(1000, 100, b"seed-abc")
    second = generate_positions(1000, 100, b"seed-abc")
    assert first == second


def test_different_seed_gives_different_order():
    first = generate_positions(1000, 100, b"seed-abc")
    second = generate_positions(1000, 100, b"seed-abd")
    assert first != second


def test_result_length_matches_request():
    assert len(generate_positions(500, 50, b"k")) == 50


def test_no_duplicates():
    result = generate_positions(1000, 300, b"unique")
    assert len(set(result)) == len(result)


def test_over_capacity_raises():
    with pytest.raises(ValueError):
        generate_positions(10, 11, b"k")


def test_zero_positions_returns_empty():
    assert generate_positions(100, 0, b"k") == []


def test_full_permutation():
    result = generate_positions(50, 50, b"full")
    assert sorted(result) == list(range(50))


def test_empty_seed_raises():
    with pytest.raises(ValueError):
        generate_positions(100, 10, b"")


@pytest.mark.parametrize("bad_seed", ["str", 123, None, bytearray(b"k")])
def test_non_bytes_seed_raises(bad_seed):
    with pytest.raises(TypeError):
        generate_positions(100, 10, bad_seed)


def test_positions_within_range():
    total = 200
    result = generate_positions(total, 80, b"range")
    assert all(0 <= p < total for p in result)


def test_negative_and_nonpositive_inputs_raise():
    with pytest.raises(ValueError):
        generate_positions(100, -1, b"k")
    with pytest.raises(ValueError):
        generate_positions(0, 0, b"k")
    with pytest.raises(ValueError):
        generate_positions(-5, 1, b"k")


def test_small_image_smoke():
    total_slots = 64 * 64 * 3
    result = generate_positions(total_slots, 1000, b"smoke")
    assert len(result) == 1000
    assert len(set(result)) == 1000
    assert all(0 <= p < total_slots for p in result)


def test_results_are_pure_python_int():
    result = generate_positions(500, 100, b"types")
    assert all(type(p) is int for p in result)
    assert not any(isinstance(p, np.integer) for p in result)


def test_derive_prng_seed_length_and_type():
    seed = derive_prng_seed("kunci-rahasia")
    assert isinstance(seed, bytes)
    assert len(seed) == 32


def test_derive_prng_seed_deterministic():
    assert derive_prng_seed("kunci-sama") == derive_prng_seed("kunci-sama")


def test_derive_prng_seed_differs_per_key():
    assert derive_prng_seed("kunci-a") != derive_prng_seed("kunci-b")


def test_derive_prng_seed_domain_separation():
    aes_like = hashlib.sha256("kunci-sama|AES".encode("utf-8")).digest()
    assert derive_prng_seed("kunci-sama") != aes_like


def test_derive_prng_seed_rejects_blank():
    with pytest.raises(ValueError):
        derive_prng_seed("")
    with pytest.raises(ValueError):
        derive_prng_seed("   ")


@pytest.mark.parametrize("bad_key", [b"bytes-key", 123, None])
def test_derive_prng_seed_rejects_non_str(bad_key):
    with pytest.raises(TypeError):
        derive_prng_seed(bad_key)


def test_derived_seed_drives_deterministic_positions():
    total_slots = 64 * 64 * 3
    first = generate_positions(total_slots, 500, derive_prng_seed("stego-key"))
    second = generate_positions(total_slots, 500, derive_prng_seed("stego-key"))
    assert first == second


def test_wrong_key_gives_different_positions():
    total_slots = 64 * 64 * 3
    right = generate_positions(total_slots, 500, derive_prng_seed("key-benar"))
    wrong = generate_positions(total_slots, 500, derive_prng_seed("key-salah"))
    assert right != wrong
