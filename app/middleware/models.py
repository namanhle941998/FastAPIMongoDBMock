from pydantic import BaseModel
from datetime import datetime, timezone


class User(BaseModel):
    full_name: str
    email: str
    hashed_password: str
    roles: list[str] = ["Guest"]
    is_active: bool | None = None
    is_disabled: bool | None = None


class RefreshToken(BaseModel):
    user_email: str
    token: str
    expires_at: datetime
    is_revoked: bool = False


class Item(BaseModel):
    name: str
    price: int
    quantity: int
    review: str


class ProductInvoice(BaseModel):
    name: str
    price: int
    quantity: int
    total: int


class Invoice(BaseModel):
    user_email: str
    items: list[ProductInvoice]
    total_amount: int
    status: str = "Pending"
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class AuditLog(BaseModel):
    user_email: str
    action: str
    detail: str
    created_at: datetime = datetime.now(timezone.utc)
    status: str
