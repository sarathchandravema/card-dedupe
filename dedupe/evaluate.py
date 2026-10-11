from __future__ import annotations

from itertools import combinations

from .matcher import Cluster


def evaluate(clusters: list[Cluster], truth: dict[str, str]) -> dict[str, float]:
    """Pairwise precision / recall of the predicted clusters against ground truth."""
    predicted = {
        frozenset((a.id, b.id))
        for c in clusters
        for a, b in combinations(c.records, 2)
    }
    by_person: dict[str, list[str]] = {}
    for rid, person in truth.items():
        by_person.setdefault(person, []).append(rid)
    actual = {
        frozenset(p) for ids in by_person.values() for p in combinations(ids, 2)
    }
    tp = len(predicted & actual)
    precision = tp / len(predicted) if predicted else 1.0
    recall = tp / len(actual) if actual else 1.0
    return {
        "true_positive_pairs": tp,
        "false_positive_pairs": len(predicted - actual),
        "false_negative_pairs": len(actual - predicted),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
    }
