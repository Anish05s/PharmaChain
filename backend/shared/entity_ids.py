import re
from typing import Type

from sqlalchemy.orm import Session

from models import Consumer, Manufacturer, Supplier

PREFIX_BY_ROLE = {
    "manufacturer": "mfg",
    "supplier": "sup",
    "consumer": "con",
}

MODEL_BY_ROLE: dict[str, Type] = {
    "manufacturer": Manufacturer,
    "supplier": Supplier,
    "consumer": Consumer,
}

_ID_RE = re.compile(r"^(mfg|sup|con)-(\d+)$", re.IGNORECASE)


def format_entity_serial(n: int) -> str:
    """001–999 zero-padded; 1000+ grows naturally (e.g. 100000)."""
    return str(n).zfill(3)


def _max_serial_for_prefix(db: Session, model: Type, prefix: str) -> int:
    prefix_lower = prefix.lower()
    max_n = 0
    rows = db.query(model.id).filter(model.id.like(f"{prefix_lower}-%")).all()
    for (entity_id,) in rows:
        match = _ID_RE.match(entity_id or "")
        if match and match.group(1).lower() == prefix_lower:
            max_n = max(max_n, int(match.group(2)))
    return max_n


def next_entity_id(db: Session, role: str) -> str:
    prefix = PREFIX_BY_ROLE[role]
    model = MODEL_BY_ROLE[role]
    serial = _max_serial_for_prefix(db, model, prefix) + 1
    return f"{prefix}-{format_entity_serial(serial)}"
