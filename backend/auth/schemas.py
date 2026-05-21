from pydantic import BaseModel, Field
from typing import Optional

ROLE_SUB_ROLE = {
    "manufacturer": "manufacturer_admin",
    "supplier": "supplier_manager",
    "consumer": "hospital_officer",
}


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    full_name: str
    role: str  # manufacturer / supplier / consumer
    organization_name: str = Field(..., min_length=2)
    country: str = "India"
    # Optional org fields (used depending on role)
    license_number: Optional[str] = None
    warehouse_location: Optional[str] = None
    location: Optional[str] = None
    consumer_type: str = "hospital"
    # Legacy: link to an existing entity instead of creating one
    entity_id: Optional[str] = None
    sub_role: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    sub_role: str
    full_name: str
    entity_id: Optional[str] = None
    org_name: Optional[str] = None