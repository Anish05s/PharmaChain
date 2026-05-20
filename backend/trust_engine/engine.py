"""
Trust Engine — MVP weighted formula.
Communicates with other modules ONLY via the database (per master prompt rule).

Trust score formula (per shipment verification):
  VERIFIED  → each involved entity +1 point  (capped at 100)
  FLAGGED   → each involved entity -5 points (floored at 0)
  PENDING   → no change

Called from verification_ai/router.py after an AIFlag is written.
"""
import logging
from sqlalchemy.orm import Session
from models import Manufacturer, Supplier, Consumer, Shipment

logger = logging.getLogger(__name__)

# ── Tuneable weights ─────────────────────────────────────────────────────────
VERIFIED_REWARD   = 1.0    # points added for a clean verification
FLAGGED_PENALTY   = 5.0    # points deducted for a flagged verification
SCORE_MIN         = 0.0
SCORE_MAX         = 100.0


def _clamp(value: float) -> float:
    return max(SCORE_MIN, min(SCORE_MAX, value))


def _adjust(current: float, delta: float) -> float:
    return _clamp(current + delta)


def update_trust_after_verification(
    db: Session,
    shipment_id: str,
    ai_status: str,
    risk_score: float = 0.0,
) -> None:
    """
    Update trust scores for all entities involved in a shipment
    based on the AI verification result.

    Args:
        db:          SQLAlchemy session (caller owns commit/rollback)
        shipment_id: UUID of the shipment that was just verified
        ai_status:   "VERIFIED" | "FLAGGED" | "PENDING"
        risk_score:  AI risk score 0-100 (used for granular penalty in future)
    """
    if ai_status == "PENDING":
        return  # no score change until all three parties have submitted

    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        logger.warning("TrustEngine: shipment %s not found", shipment_id)
        return

    delta = VERIFIED_REWARD if ai_status == "VERIFIED" else -FLAGGED_PENALTY

    # ── Manufacturer ─────────────────────────────────────────────────────────
    mfg = db.query(Manufacturer).filter(
        Manufacturer.id == shipment.from_entity_id
    ).first()
    if mfg:
        old = mfg.trust_score or 100.0
        mfg.trust_score = _adjust(old, delta)
        logger.info(
            "TrustEngine: Manufacturer %s  %s → %.1f  (Δ%+.1f)",
            mfg.name, old, mfg.trust_score, delta
        )

    # ── Supplier ─────────────────────────────────────────────────────────────
    # The shipment's to_entity_id is the supplier for manufacturer→supplier legs
    sup = db.query(Supplier).filter(
        Supplier.id == shipment.to_entity_id
    ).first()
    if sup:
        old = sup.trust_score or 100.0
        sup.trust_score = _adjust(old, delta)
        logger.info(
            "TrustEngine: Supplier %s  %.1f → %.1f  (Δ%+.1f)",
            sup.name, old, sup.trust_score, delta
        )

    # ── Consumer / Hospital ───────────────────────────────────────────────────
    # Consumer shipments go from supplier (from_entity) to consumer (to_entity)
    con = db.query(Consumer).filter(
        Consumer.id == shipment.to_entity_id
    ).first()
    if con:
        old = con.trust_score or 100.0
        con.trust_score = _adjust(old, delta)
        logger.info(
            "TrustEngine: Consumer %s  %.1f → %.1f  (Δ%+.1f)",
            con.name, old, con.trust_score, delta
        )

    try:
        db.commit()
    except Exception as exc:
        logger.error("TrustEngine commit failed: %s", exc)
        db.rollback()
