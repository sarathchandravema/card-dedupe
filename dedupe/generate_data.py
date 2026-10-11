"""Generate a small synthetic data set (~50 records) with known duplicates.

Ground truth is written to ``data/ground_truth.csv`` so the matcher can be checked.
Run:  python -m dedupe.generate_data
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

from .models import CSV_FIELDS, Record

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BANKS = ["HDFC", "SBI", "ICICI", "AXIS", "KOTAK", "CITI", "CHASE", "BARCLAYS"]
CHANNELS = ["MOBILE_APP", "WEB"]

# Customers who hold cards at several banks, with slightly different spellings of the name.
PEOPLE_WITH_DUPES = [
    ("John Smith", ["Jon Smith", "Jonn Smith"]),
    ("Priya Sharma", ["Priyaa Sharma", "Priya Sharmaa"]),
    ("Michael Johnson", ["Micheal Johnson", "Michael Jonson"]),
    ("Catherine Brown", ["Katherine Brown", "Cathrine Brown"]),
    ("Mohammed Khan", ["Muhammed Khan", "Mohamed Khan"]),
    ("Sarah Williams", ["Sara Williams", "Sarah Wiliams"]),
    ("Rajesh Kumar", ["Rajeshh Kumar", "Kumar Rajesh"]),
    ("Stephen Davis", ["Steven Davis", "Stephen Davies"]),
    ("Anita Desai", ["Anitha Desai", "Anita Desay"]),
    ("Robert Miller", ["Robert Mller", "Roberts Miller"]),
]
SINGLES = [
    "Alice Walker", "David Lee", "Emma Thompson", "Farhan Ali", "Grace Taylor",
    "Hari Prasad", "Isabel Garcia", "Jack Wilson", "Kavita Nair", "Liam Anderson",
    "Meera Iyer", "Noah Martinez", "Olivia Clark", "Pranav Mehta", "Quinn Harris",
    "Rohan Gupta", "Sophia Lewis", "Tarun Joshi", "Uma Reddy", "Victor Young",
]
# Which identifiers a duplicate shares with the original (the name is always similar,
# so each duplicate matches on at least 3 fields in total).
SHARING_PATTERNS = [
    {"mobile", "email"},
    {"mobile", "ip"},
    {"email", "atm"},
    {"mobile", "atm"},
    {"mobile", "email", "ip"},
]


def _digits(rng: random.Random, n: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def _mobile(rng: random.Random) -> str:
    return str(rng.choice([6, 7, 8, 9])) + _digits(rng, 9)


def _ip(rng: random.Random) -> str:
    return f"{rng.choice([49, 103, 117, 182, 203])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def _atm(rng: random.Random) -> str:
    return f"ATM-{rng.choice('ABCDEFGH')}{rng.randint(1000, 9999)}"


def _email(name: str, rng: random.Random) -> str:
    parts = name.lower().replace(".", "").split()
    domain = rng.choice(["gmail.com", "yahoo.com", "outlook.com", "mail.com"])
    return f"{parts[0]}.{parts[-1]}{rng.randint(1, 99)}@{domain}"


def _mobile_format(m: str, rng: random.Random) -> str:
    """Banks store the same number in different formats."""
    return rng.choice([m, f"+91{m}", f"+91 {m[:5]} {m[5:]}", f"0{m}"])


def generate(seed: int = 7) -> tuple[list[Record], list[tuple[str, str]]]:
    """Return (records, ground_truth) where ground_truth = [(record_id, person_key)]."""
    rng = random.Random(seed)
    records: list[Record] = []
    truth: list[tuple[str, str]] = []
    used_ids: set[str] = set()

    def add(person: str, name: str, bank: str, mobile: str, email: str, ip: str, atm: str) -> None:
        card_id = _digits(rng, 16)
        while card_id in used_ids:
            card_id = _digits(rng, 16)
        used_ids.add(card_id)
        records.append(Record(card_id, name, atm, mobile, email, ip, bank, rng.choice(CHANNELS)))
        truth.append((card_id, person))

    for original, variants in PEOPLE_WITH_DUPES:
        mobile, email, ip, atm = _mobile(rng), _email(original, rng), _ip(rng), _atm(rng)
        banks = rng.sample(BANKS, len(variants) + 1)
        add(original, original, banks[0], mobile, email, ip, atm)
        for variant, bank in zip(variants, banks[1:]):
            shared = rng.choice(SHARING_PATTERNS)
            add(
                original,
                variant,
                bank,
                _mobile_format(mobile, rng) if "mobile" in shared else _mobile(rng),
                email if "email" in shared else _email(variant, rng),
                ip if "ip" in shared else _ip(rng),
                atm if "atm" in shared else _atm(rng),
            )

    # Hard negatives: look-alike names and shared public IP / popular ATM, but different people.
    shared_ip, shared_atm = _ip(rng), _atm(rng)
    add("John Smyth", "John Smyth", rng.choice(BANKS), _mobile(rng), "john.smyth@mail.com", shared_ip, shared_atm)
    add("Priya Sharma (other)", "Priya Sharma", rng.choice(BANKS), _mobile(rng), "priya.s@yahoo.com", shared_ip, shared_atm)

    for name in SINGLES:
        ip = shared_ip if rng.random() < 0.15 else _ip(rng)
        atm = shared_atm if rng.random() < 0.15 else _atm(rng)
        add(name, name, rng.choice(BANKS), _mobile(rng), _email(name, rng), ip, atm)

    order = list(range(len(records)))
    rng.shuffle(order)
    return [records[i] for i in order], [truth[i] for i in order]


def write_csv(path: Path, records: list[Record]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_row())


def main() -> None:
    records, truth = generate()
    write_csv(DATA_DIR / "customers.csv", records)
    with (DATA_DIR / "ground_truth.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "true_person"])
        w.writerows(truth)
    print(f"Wrote {len(records)} records to {DATA_DIR / 'customers.csv'}")


if __name__ == "__main__":
    main()

