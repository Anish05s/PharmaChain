"""Hybrid AI engine — Layer 1 (rule-based) + Layer 2 (Gemini LLM investigator)."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)

QUANTITY_DEVIATION_THRESHOLD = 0.15
TEMP_TOLERANCE_CELSIUS = 5.0
FLAG_RISK_THRESHOLD = 30


@dataclass
class PartyReport:
    party: str
    quantity: Optional[int] = None
    expiry: Optional[datetime] = None
    temp: Optional[float] = None
    batch_name: str = "Unknown"
    batch_number: str = "Unknown"


@dataclass
class VerificationResult:
    status: str
    risk_score: float
    triggered_rules: List[str] = field(default_factory=list)
    mismatches: List[dict] = field(default_factory=list)
    explanation: str = ""
    hospital_shipment_id: Optional[str] = None

    def triggered_rules_json(self) -> str:
        return json.dumps(self.triggered_rules)

    def mismatch_details_json(self) -> str:
        return json.dumps(self.mismatches)


def _pct_deviation(expected: int, reported: int) -> float:
    if expected == 0:
        return 0.0
    return abs(reported - expected) / expected


def _same_expiry(a: datetime, b: datetime) -> bool:
    return a.date() == b.date()


def run_verification(
    manufacturer: PartyReport,
    supplier: Optional[PartyReport],
    hospital: Optional[PartyReport],
    hospital_shipment_id: Optional[str],
    supplier_dispatched: Optional[int] = None,
) -> VerificationResult:
    if supplier is None or hospital is None:
        missing = []
        if supplier is None:
            missing.append("supplier")
        if hospital is None:
            missing.append("hospital")
        return VerificationResult(
            status="PENDING",
            risk_score=0,
            explanation=(
                f"Waiting for independent submissions from: {', '.join(missing)}. "
                "Verification requires all three parties."
            ),
            hospital_shipment_id=hospital_shipment_id,
        )

    rules: List[str] = []
    mismatches: List[dict] = []
    risk = 0.0

    # Manufacturer vs supplier quantity
    mfg_qty = manufacturer.quantity or 0
    sup_qty = supplier.quantity or 0
    sup_dev = _pct_deviation(mfg_qty, sup_qty)
    if sup_dev > QUANTITY_DEVIATION_THRESHOLD:
        rules.append("QUANTITY_DEVIATION_MFG_SUPPLIER")
        mismatches.append({
            "field": "quantity",
            "manufacturer": mfg_qty,
            "supplier": sup_qty,
            "deviation_pct": round(sup_dev * 100, 1),
        })
        risk += 30
    elif sup_dev > 0.0:
        rules.append("LOW_QUANTITY_DEVIATION_MFG_SUPPLIER")
        mismatches.append({
            "field": "quantity",
            "manufacturer": mfg_qty,
            "supplier": sup_qty,
            "deviation_pct": round(sup_dev * 100, 1),
        })
        risk += 10

    # Supplier vs hospital quantity
    hos_qty = hospital.quantity or 0
    sup_expected_for_hospital = supplier_dispatched if supplier_dispatched is not None else sup_qty
    hos_dev = _pct_deviation(sup_expected_for_hospital, hos_qty)
    if hos_dev > QUANTITY_DEVIATION_THRESHOLD:
        rules.append("QUANTITY_DEVIATION_SUPPLIER_HOSPITAL")
        mismatches.append({
            "field": "quantity",
            "supplier": sup_expected_for_hospital,
            "hospital": hos_qty,
            "deviation_pct": round(hos_dev * 100, 1),
        })
        risk += 30
    elif hos_dev > 0.0:
        rules.append("LOW_QUANTITY_DEVIATION_SUPPLIER_HOSPITAL")
        mismatches.append({
            "field": "quantity",
            "supplier": sup_expected_for_hospital,
            "hospital": hos_qty,
            "deviation_pct": round(hos_dev * 100, 1),
        })
        risk += 10

    # Expiry chain
    mfg_exp = manufacturer.expiry
    sup_exp = supplier.expiry
    hos_exp = hospital.expiry
    if mfg_exp and sup_exp and not _same_expiry(mfg_exp, sup_exp):
        rules.append("EXPIRY_MISMATCH_MFG_SUPPLIER")
        mismatches.append({
            "field": "expiry",
            "manufacturer": mfg_exp.isoformat(),
            "supplier": sup_exp.isoformat(),
        })
        risk += 40
    if sup_exp and hos_exp and not _same_expiry(sup_exp, hos_exp):
        rules.append("EXPIRY_MISMATCH_SUPPLIER_HOSPITAL")
        mismatches.append({
            "field": "expiry",
            "supplier": sup_exp.isoformat(),
            "hospital": hos_exp.isoformat(),
        })
        risk += 40

    # Temperature declarations
    mfg_temp = manufacturer.temp
    sup_temp = supplier.temp
    hos_temp = hospital.temp
    if mfg_temp is not None and sup_temp is not None:
        diff = abs(mfg_temp - sup_temp)
        if diff > TEMP_TOLERANCE_CELSIUS:
            rules.append("TEMP_DEVIATION_MFG_SUPPLIER")
            mismatches.append({
                "field": "temperature",
                "manufacturer": mfg_temp,
                "supplier": sup_temp,
                "difference_c": round(diff, 1),
            })
            risk += 15
    if sup_temp is not None and hos_temp is not None:
        diff = abs(sup_temp - hos_temp)
        if diff > TEMP_TOLERANCE_CELSIUS:
            rules.append("TEMP_DEVIATION_SUPPLIER_HOSPITAL")
            mismatches.append({
                "field": "temperature",
                "supplier": sup_temp,
                "hospital": hos_temp,
                "difference_c": round(diff, 1),
            })
            risk += 15

    risk = min(100.0, risk)
    status = "FLAGGED" if risk >= FLAG_RISK_THRESHOLD else "VERIFIED"

    if status == "FLAGGED":
        rule_explanation = _build_flagged_explanation(manufacturer, supplier, hospital, mismatches, risk)

        explanation = rule_explanation

    else:
        explanation = (
            f"All three parties aligned within thresholds. "
            f"Manufacturer {mfg_qty} units -> Supplier {sup_qty} -> Hospital {hos_qty}. "
            f"Risk score {risk:.0f}/100 (safe)."
        )

    return VerificationResult(
        status=status,
        risk_score=risk,
        triggered_rules=rules,
        mismatches=mismatches,
        explanation=explanation,
        hospital_shipment_id=hospital_shipment_id,
    )


def _build_flagged_explanation(
    manufacturer: PartyReport,
    supplier: PartyReport,
    hospital: PartyReport,
    mismatches: List[dict],
    risk: float,
) -> str:
    lines = [
        f"Cross-match flagged. Risk score {risk:.0f}/100.",
    ]
    
    # Customise the output if a quantity mismatch was the culprit
    qty_mismatch = next((m for m in mismatches if m.get("field") == "quantity"), None)
    if qty_mismatch:
        if "manufacturer" in qty_mismatch:
            lines.append(f"Manufacturer dispatched: {qty_mismatch['manufacturer']} units")
            lines.append(f"Supplier received: {qty_mismatch['supplier']} units")
        else:
            lines.append(f"Supplier dispatched: {qty_mismatch['supplier']} units")
            lines.append(f"Hospital received: {qty_mismatch['hospital']} units")
    else:
        lines.append(f"Manufacturer qty: {manufacturer.quantity} units")
        lines.append(f"Supplier qty:     {supplier.quantity} units")
        lines.append(f"Hospital qty:     {hospital.quantity} units")
    for m in mismatches:
        if m.get("field") == "quantity" and "deviation_pct" in m:
            lines.append(
                f"Quantity deviation {m['deviation_pct']}% exceeds "
                f"{QUANTITY_DEVIATION_THRESHOLD * 100:.0f}% threshold."
            )
        elif m.get("field") == "expiry":
            lines.append("Expiry date mismatch detected between parties.")
        elif m.get("field") == "temperature":
            lines.append(
                f"Storage temperature difference {m.get('difference_c')}°C "
                f"exceeds {TEMP_TOLERANCE_CELSIUS}°C tolerance."
            )
    lines.append("Possible diversion or tampering between handoff checkpoints.")
    return " ".join(lines)
