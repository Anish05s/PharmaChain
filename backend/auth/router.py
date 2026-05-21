from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Manufacturer, Supplier, Consumer
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse, ROLE_SUB_ROLE
from auth.utils import hash_password, verify_password, create_access_token
from shared.entity_ids import next_entity_id

router = APIRouter(prefix="/auth", tags=["Authentication"])

VALID_ROLES = frozenset(ROLE_SUB_ROLE.keys())


def _resolve_sub_role(data: RegisterRequest) -> str:
    if data.sub_role:
        return data.sub_role
    sub = ROLE_SUB_ROLE.get(data.role)
    if not sub:
        raise HTTPException(status_code=400, detail="Invalid role")
    return sub

def _get_org_name(db: Session, role: str, entity_id: str) -> str | None:
    if not entity_id:
        return None
    if role == "manufacturer":
        ent = db.query(Manufacturer).filter(Manufacturer.id == entity_id).first()
    elif role == "supplier":
        ent = db.query(Supplier).filter(Supplier.id == entity_id).first()
    elif role == "consumer":
        ent = db.query(Consumer).filter(Consumer.id == entity_id).first()
    else:
        return None
    return ent.name if ent else None


def _create_entity(db: Session, data: RegisterRequest) -> str:
    entity_id = next_entity_id(db, data.role)
    if data.role == "manufacturer":
        entity = Manufacturer(
            id=entity_id,
            name=data.organization_name,
            license_number=data.license_number or f"LIC-{data.email.split('@')[0]}",
            country=data.country,
        )
    elif data.role == "supplier":
        entity = Supplier(
            id=entity_id,
            name=data.organization_name,
            warehouse_location=data.warehouse_location or data.location,
            country=data.country,
        )
    elif data.role == "consumer":
        entity = Consumer(
            id=entity_id,
            name=data.organization_name,
            type=data.consumer_type,
            location=data.location,
            country=data.country,
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid role")
    db.add(entity)
    db.flush()
    return entity.id


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Role must be manufacturer, supplier, or consumer")

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    sub_role = _resolve_sub_role(data)

    if data.entity_id:
        entity_id = data.entity_id
        if data.role == "manufacturer" and not db.query(Manufacturer).filter(Manufacturer.id == entity_id).first():
            raise HTTPException(status_code=400, detail="Manufacturer entity not found")
        if data.role == "supplier" and not db.query(Supplier).filter(Supplier.id == entity_id).first():
            raise HTTPException(status_code=400, detail="Supplier entity not found")
        if data.role == "consumer" and not db.query(Consumer).filter(Consumer.id == entity_id).first():
            raise HTTPException(status_code=400, detail="Consumer entity not found")
    else:
        entity_id = _create_entity(db, data)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        sub_role=sub_role,
        entity_id=entity_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": user.id,
        "role": user.role,
        "sub_role": user.sub_role
    })

    return TokenResponse(
        access_token=token,
        role=user.role,
        sub_role=user.sub_role,
        full_name=user.full_name,
        entity_id=user.entity_id,
        org_name=_get_org_name(db, user.role, user.entity_id)
    )

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.id,
        "role": user.role,
        "sub_role": user.sub_role
    })

    return TokenResponse(
        access_token=token,
        role=user.role,
        sub_role=user.sub_role,
        full_name=user.full_name,
        entity_id=user.entity_id,
        org_name=_get_org_name(db, user.role, user.entity_id)
    )