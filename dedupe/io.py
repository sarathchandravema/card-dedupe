from __future__ import annotations

import csv
from pathlib import Path

from .models import Record


def load_records(path: str | Path) -> list[Record]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return [
            Record(
                id=(row.get("id") or "").strip(),
                name=row.get("name") or "",
                atm_used=row.get("atm_used") or "",
                mobile=row.get("mobile") or "",
                email=row.get("email") or "",
                ip_address=row.get("ip_address") or "",
                bank=row.get("bank") or "",
                channel=row.get("channel") or "",
            )
            for row in csv.DictReader(fh)
        ]


def load_truth(path: str | Path) -> dict[str, str]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return {r["id"]: r["true_person"] for r in csv.DictReader(fh)}
