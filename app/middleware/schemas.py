from pydantic import BaseModel, EmailStr, validator
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    roles: list[str]

    @validator("password")
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v
    
    @validator("full_name")
    def full_name_not_match_password(cls, v, values, **kwargs):
        if "password" in values and v == values["password"]:
            raise ValueError("Full name and password must not match")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class ItemCreate(BaseModel):
    name: str
    price: int
    quantity: int
    review: str


class ItemGet(BaseModel):
    page: int 
    num_per_page: int
    sort_by_column: str
    is_ascend: bool


class ProductQuantityResponse(BaseModel):
    name: str
    quantity: int


class ProductInvoice(BaseModel):
    name: str
    price: int
    quantity: int
    total: int


class UserCreateInvoice(BaseModel):
    user_email: str
    items: list[ProductInvoice]
    total_amount: int


class InvoiceResponse(BaseModel):
    user_email: str
    items: list[ProductInvoice]
    total_amount: int
    status: str
    created_at: datetime
    updated_at: datetime
