from __future__ import annotations

from dataclasses import dataclass

CSV_FIELDS = (
    "id",
    "bank",
    "name",
    "atm_used",
    "mobile",
    "email",
    "ip_address",
    "channel",
)


@dataclass(frozen=True)
class Record:
    """One card/customer record as submitted by a member bank."""

    id: str  # 16-digit identifier issued by the bank
    name: str
    atm_used: str
    mobile: str
    email: str
    ip_address: str  # IP of the mobile app or web session
    bank: str = ""
    channel: str = ""  # MOBILE_APP or WEB

    def to_row(self) -> dict[str, str]:
        return {f: getattr(self, f) for f in CSV_FIELDS}
