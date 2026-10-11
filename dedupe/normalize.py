"""Field normalisers. Each returns "" when the value is missing or unusable."""
from __future__ import annotations

import ipaddress
import re
import unicodedata

_TITLES = {"mr", "mrs", "ms", "miss", "mx", "dr", "shri", "smt", "sri"}
_GMAIL_DOMAINS = {"gmail.com", "googlemail.com"}


def normalize_name(value: str | None) -> str:
    """Lower-case, strip accents/punctuation/titles, turn 'Last, First' into 'first last'."""
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    if "," in text:
        last, _, first = text.partition(",")
        text = f"{first} {last}"
    text = re.sub(r"[^a-z\s]", " ", text)
    return " ".join(t for t in text.split() if t not in _TITLES)


def normalize_mobile(value: str | None) -> str:
    """Keep digits only and compare on the last 10 (drops +91 / 0 prefixes)."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 7:
        return ""
    return digits[-10:]


def normalize_email(value: str | None) -> str:
    """Lower-case; drop '+tag'; ignore dots for Gmail addresses."""
    text = (value or "").strip().lower()
    if text.count("@") != 1:
        return ""
    local, domain = text.split("@")
    local = local.split("+")[0]
    if domain in _GMAIL_DOMAINS:
        local = local.replace(".", "")
        domain = "gmail.com"
    if not local or not domain:
        return ""
    return f"{local}@{domain}"


def normalize_ip(value: str | None) -> str:
    try:
        return str(ipaddress.ip_address((value or "").strip()))
    except ValueError:
        return ""


def normalize_atm(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())
