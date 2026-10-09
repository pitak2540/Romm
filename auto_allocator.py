"""Heuristic GBA ROM free-space scanner and safe allocation planning.

No ROM is modified by this module. FF/00 runs are candidates, not proof of unused space.
"""
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Candidate:
    start: int
    aligned_start: int
    end: int
    size: int
    fill: int
    pointer_hits_exact_start: int
    score: float

def next_power_of_two(size: int, cap: int = 64 * 1024 * 1024) -> int:
    if size <= 0:
        raise ValueError("size must be positive")
    n = 1
    while n < size and n < cap:
        n <<= 1
    if n < size:
        raise ValueError("requested size exceeds cap")
    return n

def scan_candidates(data: bytes, requested_size: int, alignment: int = 4,
                    min_run: int = 32, start_floor: int = 0xC0):
    if requested_size <= 0:
        raise ValueError("requested_size must be positive")
    if alignment <= 0:
        raise ValueError("alignment must be positive")
    candidates = []
    i = 0
    while i < len(data):
        fill = data[i]
        if fill not in (0x00, 0xFF):
            i += 1
            continue
        start = i
        while i < len(data) and data[i] == fill:
            i += 1
        end = i
        aligned = ((start + alignment - 1) // alignment) * alignment
        if end - start < max(min_run, requested_size) or start < start_floor:
            continue
        if aligned + requested_size > end:
            continue
        ptr = (0x08000000 + start).to_bytes(4, "little")
        hits = data.count(ptr)
        score = min(end-start, requested_size*8) / requested_size
        score += 0.5 if start % alignment == 0 else 0
        score -= hits * 0.25
        candidates.append(Candidate(start, aligned, end, end-start, fill, hits, round(score,3)))
    return sorted(candidates, key=lambda c: (c.score,c.size), reverse=True)

def make_plan(data: bytes, requested_size: int, alignment: int = 4):
    candidates = scan_candidates(data, requested_size, alignment)
    chosen = candidates[0] if candidates else None
    return {
        "rom_size": len(data),
        "requested_size": requested_size,
        "candidates": [asdict(c) for c in candidates],
        "allocation": ({"offset": chosen.aligned_start, "fill": chosen.fill,
                        "size": requested_size} if chosen else None),
        "requires_expansion": chosen is None,
        "expanded_size": None if chosen else next_power_of_two(len(data)+requested_size),
        "warning": "Heuristic only; validate references, compression and game-specific pointers."
    }
