

# ══════════════════════════════════════════════════════════════════════════════
# ROLE-SPECIFIC VERIFICATION ENDPOINTS
# Each role sees only the legs relevant to them with plain English status.
# ══════════════════════════════════════════════════════════════════════════════

def _overall(legs: list) -> tuple:
    """Derive overall_status and risk_score from a list of LegReports."""
    has_flag = any(
        leg.qty_status == "DEVIATION" or leg.expiry_status == "MISMATCH"
        or leg.temp_status == "DEVIATION"
        for leg in legs
    )
    has_pending = any(
        leg.qty_status == "PENDING" or leg.expiry_status == "PENDING"
        for leg in legs
    )
    if has_flag:
        risk = sum(
            (30 if leg.qty_status == "DEVIATION" else 0) +
            (40 if leg.expiry_status == "MISMATCH" else 0) +
            (15 if leg.temp_status == "DEVIATION" else 0)
            for leg in legs
        )
        return "FLAGGED", min(100.0, float(risk))
    if has_pending:
        return "PENDING", 0.0
    return "VERIFIED", 0.0


# ── Manufacturer: full chain view (both legs) ─────────────────────────────────

@router.get(
    "/manufacturer/batch/{batch_id}",
    response_model=RoleVerificationResponse,
    summary="Manufacturer full-chain verification view",
)
def manufacturer_chain_view(
    batch_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Shows manufacturer:
    - Leg 1: What they dispatched to supplier vs what supplier received
    - Leg 2: What supplier forwarded to hospital vs what hospital received
    - Expiry / temp consistency across all parties
    """
    batch = db.query(MedicineBatch).filter(MedicineBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    legs = []

    mfr_shipments = (
        db.query(Shipment)
        .filter(Shipment.batch_id == batch_id, Shipment.from_entity_id == batch.entity_id)
        .order_by(Shipment.created_at)
        .all()
    )

    for mfr_ship in mfr_shipments:
        sup_handoff = (
            db.query(HandoffRecord)
            .filter(
                HandoffRecord.shipment_id == mfr_ship.id,
                HandoffRecord.stage == "supplier_receipt",
            )
            .first()
        )
        sup_entity = db.query(Supplier).filter(Supplier.id == mfr_ship.to_entity_id).first()
        sup_name = sup_entity.name if sup_entity else "Supplier"

        legs.append(build_leg("manufacturer_to_supplier", "Manufacturer", sup_name,
                               mfr_ship, batch, sup_handoff))

        if sup_entity:
            sup_shipments = (
                db.query(Shipment)
                .filter(Shipment.batch_id == batch_id,
                        Shipment.from_entity_id == sup_entity.id)
                .order_by(Shipment.created_at)
                .all()
            )
            for sup_ship in sup_shipments:
                hosp_handoff = (
                    db.query(HandoffRecord)
                    .filter(
                        HandoffRecord.shipment_id == sup_ship.id,
                        HandoffRecord.stage == "hospital_receipt",
                    )
                    .first()
                )
                hosp_entity = db.query(Consumer).filter(Consumer.id == sup_ship.to_entity_id).first()
                hosp_name = hosp_entity.name if hosp_entity else "Hospital/NGO"
                legs.append(build_leg("supplier_to_hospital", sup_name, hosp_name,
                                       sup_ship, batch, hosp_handoff))

    overall_status, risk = _overall(legs)
    if not legs:
        summary = f"Batch {batch.batch_number} — {batch.quantity:,} units produced. No outbound shipments yet."
    elif overall_status == "VERIFIED":
        summary = (f"✅ Full chain verified. Batch {batch.batch_number} — "
                   f"{batch.quantity:,} units produced. All {len(legs)} leg(s) cleared.")
    elif overall_status == "FLAGGED":
        summary = f"🚩 Chain flag detected. Risk {risk:.0f}/100. Review the legs below."
    else:
        summary = "⏳ Pending — waiting for handoff confirmations from downstream parties."

    return RoleVerificationResponse(
        role="manufacturer", batch_id=batch.id,
        batch_number=batch.batch_number, medicine_name=batch.name,
        batch_qty_total=batch.quantity or 0,
        batch_expiry=batch.expiry_date, declared_temp=batch.storage_temp_declared,
        legs=legs, overall_status=overall_status, risk_score=risk, summary=summary,
    )


# ── Supplier: incoming leg + outgoing leg(s) ──────────────────────────────────

@router.get(
    "/supplier/shipment/{incoming_shipment_id}",
    response_model=RoleVerificationResponse,
    summary="Supplier two-leg chain view",
)
def supplier_chain_view(
    incoming_shipment_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Shows supplier:
    - Leg 1: Manufacturer dispatched → supplier received (match/mismatch)
    - Leg 2: Supplier dispatched → hospital received (match/mismatch)
    - Batch number, expiry, temp across both legs
    """
    incoming = db.query(Shipment).filter(Shipment.id == incoming_shipment_id).first()
    if not incoming:
        raise HTTPException(status_code=404, detail="Incoming shipment not found")

    batch = db.query(MedicineBatch).filter(MedicineBatch.id == incoming.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    mfr_entity = db.query(Manufacturer).filter(Manufacturer.id == incoming.from_entity_id).first()
    mfr_name = mfr_entity.name if mfr_entity else "Manufacturer"
    sup_entity = db.query(Supplier).filter(Supplier.id == incoming.to_entity_id).first()
    sup_name = sup_entity.name if sup_entity else "Supplier"

    sup_handoff = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.shipment_id == incoming.id,
                HandoffRecord.stage == "supplier_receipt")
        .first()
    )

    legs = [build_leg("manufacturer_to_supplier", mfr_name, sup_name,
                       incoming, batch, sup_handoff)]

    if sup_entity:
        sup_shipments = (
            db.query(Shipment)
            .filter(Shipment.batch_id == batch.id,
                    Shipment.from_entity_id == sup_entity.id)
            .order_by(Shipment.created_at)
            .all()
        )
        for sup_ship in sup_shipments:
            hosp_handoff = (
                db.query(HandoffRecord)
                .filter(HandoffRecord.shipment_id == sup_ship.id,
                        HandoffRecord.stage == "hospital_receipt")
                .first()
            )
            hosp_entity = db.query(Consumer).filter(Consumer.id == sup_ship.to_entity_id).first()
            hosp_name = hosp_entity.name if hosp_entity else "Hospital/NGO"
            legs.append(build_leg("supplier_to_hospital", sup_name, hosp_name,
                                   sup_ship, batch, hosp_handoff))

    overall_status, risk = _overall(legs)
    if overall_status == "VERIFIED":
        summary = (f"✅ Both legs verified. Received from {mfr_name}: "
                   f"{incoming.quantity_dispatched:,} units. Downstream dispatch confirmed.")
    elif overall_status == "FLAGGED":
        summary = f"🚩 Discrepancy detected. Risk {risk:.0f}/100. Check leg details below."
    else:
        summary = "⏳ Awaiting downstream confirmation from hospital."

    return RoleVerificationResponse(
        role="supplier", batch_id=batch.id,
        batch_number=batch.batch_number, medicine_name=batch.name,
        batch_qty_total=batch.quantity or 0,
        batch_expiry=batch.expiry_date, declared_temp=batch.storage_temp_declared,
        legs=legs, overall_status=overall_status, risk_score=risk, summary=summary,
    )


# ── Hospital/Consumer: single leg + batch identity check ──────────────────────

@router.get(
    "/hospital/shipment/{incoming_shipment_id}",
    response_model=RoleVerificationResponse,
    summary="Hospital/consumer single-leg verification",
)
def hospital_chain_view(
    incoming_shipment_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Shows hospital:
    - Did they receive what the supplier dispatched?
    - Same batch number, expiry, temp as originally manufactured?
    - Product authenticity confirmation
    """
    incoming = db.query(Shipment).filter(Shipment.id == incoming_shipment_id).first()
    if not incoming:
        raise HTTPException(status_code=404, detail="Incoming shipment not found")

    batch = db.query(MedicineBatch).filter(MedicineBatch.id == incoming.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    sup_entity = db.query(Supplier).filter(Supplier.id == incoming.from_entity_id).first()
    sup_name = sup_entity.name if sup_entity else "Supplier"
    hosp_entity = db.query(Consumer).filter(Consumer.id == incoming.to_entity_id).first()
    hosp_name = hosp_entity.name if hosp_entity else "Hospital/NGO"

    hosp_handoff = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.shipment_id == incoming.id,
                HandoffRecord.stage == "hospital_receipt")
        .first()
    )

    leg = build_leg("supplier_to_hospital", sup_name, hosp_name,
                     incoming, batch, hosp_handoff)
    overall_status, risk = _overall([leg])

    if overall_status == "VERIFIED":
        qty = hosp_handoff.quantity_reported if hosp_handoff else "—"
        exp = batch.expiry_date.date() if batch.expiry_date else "—"
        summary = (f"✅ Shipment {incoming.shipment_code} verified. "
                   f"Received {qty:,} units of {batch.name} (Batch #{batch.batch_number}). "
                   f"Expiry {exp}. Product identity: authentic.")
    elif overall_status == "FLAGGED":
        summary = (f"🚩 Discrepancy in received shipment. Risk {risk:.0f}/100. "
                   f"Do not distribute until resolved.")
    else:
        summary = "⏳ Submit your receipt confirmation to run the verification check."

    return RoleVerificationResponse(
        role="consumer", batch_id=batch.id,
        batch_number=batch.batch_number, medicine_name=batch.name,
        batch_qty_total=batch.quantity or 0,
        batch_expiry=batch.expiry_date, declared_temp=batch.storage_temp_declared,
        legs=[leg], overall_status=overall_status, risk_score=risk, summary=summary,
    )
