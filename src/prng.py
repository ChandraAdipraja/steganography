from __future__ import annotations

import hashlib
import random


def generate_positions(
    total_slots: int,
    num_positions: int,
    seed: bytes,
) -> list[int]:
    if isinstance(total_slots, bool) or not isinstance(total_slots, int):
        raise TypeError("total_slots must be an int")
    if isinstance(num_positions, bool) or not isinstance(num_positions, int):
        raise TypeError("num_positions must be an int")
    if not isinstance(seed, bytes):
        raise TypeError("seed must be bytes")
    if len(seed) == 0:
        raise ValueError("seed must be non-empty bytes")
    if total_slots <= 0:
        raise ValueError("total_slots must be a positive integer")
    if num_positions < 0:
        raise ValueError("num_positions must be a non-negative integer")
    if num_positions > total_slots:
        raise ValueError(
            f"num_positions ({num_positions}) exceeds "
            f"total_slots ({total_slots})"
        )
    if num_positions == 0:
        return []

    rng = random.Random(seed)
    table: dict[int, int] = {}
    out: list[int] = []
    append = out.append
    get = table.get
    for i in range(num_positions):
        j = rng.randrange(i, total_slots)
        vi = get(i, i)
        vj = get(j, j)
        table[i] = vj
        table[j] = vi
        append(vj)
    return out


def derive_prng_seed(stego_key: str) -> bytes:
    if not isinstance(stego_key, str):
        raise TypeError("stego_key must be a str")
    if not stego_key.strip():
        raise ValueError("stego_key must be a non-empty string")
    return hashlib.sha256((stego_key + "|PRNG").encode("utf-8")).digest()