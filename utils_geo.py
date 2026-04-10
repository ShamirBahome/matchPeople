from __future__ import annotations

import math


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlamb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def language_overlap(a: list[str], b: list[str]) -> list[str]:
    la = {x.lower() for x in a}
    lb = {x.lower() for x in b}
    return sorted(la & lb)
