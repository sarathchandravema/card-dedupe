"""Command line: python -m dedupe.cli [--csv data/customers.csv] [--generate]"""
from __future__ import annotations

import argparse
from pathlib import Path

from .evaluate import evaluate
from .generate_data import DATA_DIR, main as generate_main
from .io import load_records, load_truth
from .matcher import Cluster, MatchConfig, find_duplicates


def format_cluster(number: int, cluster: Cluster) -> str:
    lines = [f"Customer group {number}: {len(cluster.records)} records"]
    for r in cluster.records:
        lines.append(
            f"  {r.id}  {r.bank:<9} {r.name:<18} {r.mobile:<16} {r.email:<30} "
            f"{r.ip_address:<16} {r.atm_used}"
        )
    for ev in cluster.evidence:
        fields = ", ".join(f"{f}" for f in ev.matched)
        lines.append(f"    {ev.a.id[-4:]} <-> {ev.b.id[-4:]}: matched [{fields}] score={ev.score}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Find the same customer across bank ids.")
    p.add_argument("--csv", default=str(DATA_DIR / "customers.csv"))
    p.add_argument("--generate", action="store_true", help="regenerate sample data first")
    p.add_argument("--min-matches", type=int, default=3)
    p.add_argument("--min-score", type=float, default=4.5)
    args = p.parse_args(argv)

    if args.generate or not Path(args.csv).exists():
        generate_main()

    records = load_records(args.csv)
    config = MatchConfig(min_matches=args.min_matches, min_score=args.min_score)
    clusters = find_duplicates(records, config)

    print(f"{len(records)} records, {len(clusters)} customer groups with multiple ids\n")
    for n, c in enumerate(clusters, 1):
        print(format_cluster(n, c), end="\n\n")

    truth_path = Path(args.csv).with_name("ground_truth.csv")
    if truth_path.exists():
        print("Accuracy vs ground truth:", evaluate(clusters, load_truth(truth_path)))


if __name__ == "__main__":
    main()
