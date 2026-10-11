"""Pairwise matching and grouping of records that belong to the same customer.

Two records are flagged as the same customer when BOTH hold:
  1. at least ``min_matches`` fields match (default 3), and
  2. the weighted score of the matching fields reaches ``min_score``.

Mobile and email are strong identifiers (weighted higher). IP address and ATM
are weak because strangers share ATMs, and households / offices / mobile
carriers share IPs. So three weak matches alone are not enough.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable

from rapidfuzz.distance import JaroWinkler

from .models import Record
from .normalize import (
    normalize_atm,
    normalize_email,
    normalize_ip,
    normalize_mobile,
    normalize_name,
)

DEFAULT_WEIGHTS = {
    "mobile": 2.0,
    "email": 2.0,
    "name": 1.5,
    "atm_used": 1.0,
    "ip_address": 1.0,
}


@dataclass(frozen=True)
class MatchConfig:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    min_matches: int = 3
    min_score: float = 4.5
    name_threshold: float = 0.90  # Jaro-Winkler similarity on normalised names


@dataclass(frozen=True)
class PairResult:
    a: Record
    b: Record
    matched: dict[str, float]  # field -> similarity (1.0 for exact matches)
    score: float
    is_match: bool


def name_similarity(a: str | None, b: str | None) -> float:
    """0..1 similarity tolerant of typos, e.g. 'Jonn' ~ 'Jon', and word order."""
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    # Sort tokens so "Smith John" == "John Smith"; then compare the whole string.
    sa, sb = " ".join(sorted(na.split())), " ".join(sorted(nb.split()))
    return JaroWinkler.similarity(sa, sb)


def _exact(a: str, b: str) -> float:
    return 1.0 if a and a == b else 0.0


def field_similarities(a: Record, b: Record) -> dict[str, float]:
    return {
        "name": name_similarity(a.name, b.name),
        "mobile": _exact(normalize_mobile(a.mobile), normalize_mobile(b.mobile)),
        "email": _exact(normalize_email(a.email), normalize_email(b.email)),
        "atm_used": _exact(normalize_atm(a.atm_used), normalize_atm(b.atm_used)),
        "ip_address": _exact(normalize_ip(a.ip_address), normalize_ip(b.ip_address)),
    }


def compare(a: Record, b: Record, config: MatchConfig | None = None) -> PairResult:
    cfg = config or MatchConfig()
    sims = field_similarities(a, b)
    matched = {
        f: s
        for f, s in sims.items()
        if s >= (cfg.name_threshold if f == "name" else 1.0)
    }
    score = sum(cfg.weights[f] for f in matched)
    is_match = len(matched) >= cfg.min_matches and score >= cfg.min_score
    return PairResult(a, b, matched, round(score, 2), is_match)


@dataclass
class Cluster:
    records: list[Record]
    evidence: list[PairResult]  # only the matching pairs inside this cluster


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        self.parent[self.find(x)] = self.find(y)


def find_duplicates(
    records: Iterable[Record], config: MatchConfig | None = None
) -> list[Cluster]:
    """Return clusters (size >= 2) of records believed to be the same customer.

    All pairs are compared, which is fine for small data sets. For millions of
    rows, add blocking (e.g. index by mobile / email / name phonetic key) so
    only candidate pairs are compared.
    """
    cfg = config or MatchConfig()
    recs = list(records)
    uf = _UnionFind(len(recs))
    hits: list[tuple[int, int, PairResult]] = []
    for i, j in combinations(range(len(recs)), 2):
        result = compare(recs[i], recs[j], cfg)
        if result.is_match:
            uf.union(i, j)
            hits.append((i, j, result))

    members: dict[int, list[int]] = {}
    for idx in range(len(recs)):
        members.setdefault(uf.find(idx), []).append(idx)

    clusters = []
    for root, idxs in members.items():
        if len(idxs) < 2:
            continue
        evidence = [r for i, _, r in hits if uf.find(i) == root]
        clusters.append(Cluster([recs[i] for i in idxs], evidence))
    clusters.sort(key=lambda c: (-len(c.records), c.records[0].id))
    return clusters
