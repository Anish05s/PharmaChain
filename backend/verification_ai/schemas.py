from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class PartySnapshot(BaseModel):
    party: str
    quantity: Optional[int] = None
    expiry: Optional[datetime] = None
    temp: Optional[float] = None


class VerificationResponse(BaseModel):
    batch_id: str
    batch_number: str
    medicine_name: str
    shipment_id: Optional[str] = None
    flag_id: Optional[str] = None
    status: str
    risk_score: float
    triggered_rules: List[str]
    mismatch_details: List[dict]
    explanation: str
    manufacturer: PartySnapshot
    supplier: Optional[PartySnapshot] = None
    hospital: Optional[PartySnapshot] = None


class FlagListItem(BaseModel):
    id: str
    shipment_id: str
    batch_id: str
    batch_number: str
    medicine_name: str
    risk_score: float
    status: str
    explanation: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Role-specific leg-level verification ─────────────────────────────────────

class LegReport(BaseModel):
    """A single shipment leg result (A → B)."""
    leg: str                          # e.g. "manufacturer_to_supplier"
    shipment_code: str
    from_party: str
    to_party: str
    medicine_name: str
    batch_number: str
    dispatched_qty: int
    received_qty: Optional[int] = None
    batch_expiry: Optional[datetime] = None
    received_expiry: Optional[datetime] = None
    declared_temp: Optional[float] = None
    received_temp: Optional[float] = None
    qty_status: str = "PENDING"       # MATCH | DEVIATION | PENDING
    expiry_status: str = "PENDING"    # MATCH | MISMATCH | PENDING
    temp_status: str = "PENDING"      # MATCH | DEVIATION | PENDING | N/A
    qty_deviation_pct: Optional[float] = None
    temp_deviation_c: Optional[float] = None
    notes: str = ""


class RoleVerificationResponse(BaseModel):
    """Full chain view tailored to a specific role."""
    role: str                         # manufacturer | supplier | consumer
    batch_id: str
    batch_number: str
    medicine_name: str
    batch_qty_total: int              # what manufacturer originally produced
    batch_expiry: Optional[datetime] = None
    declared_temp: Optional[float] = None
    legs: List[LegReport]
    overall_status: str               # VERIFIED | FLAGGED | PENDING
    risk_score: float
    summary: str
