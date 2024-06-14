import pymongo
from datetime import datetime, timezone
import re, os
import middleware.schemas as schemas
import middleware.models as models
import middleware.dependencies as dependencies
from middleware import pubsub

subscriber = pubsub.Subscriber("crud")
subscriber.subscribe("user_login")

mongo_uri = os.getenv("MONGO_URI") or "mongodb://localhost/27017"
print("Mongo URI: ", mongo_uri)
client = pymongo.MongoClient(mongo_uri)
db = client.get_database("fastapi")
user_col = db["users"]
item_col = db["items"]
invoice_col = db["invoices"]
refresh_token_col = db["refresh_tokens"]
audit_log_col = db["audit_logs"]


# Utility functions for authentication and authorization
def get_all_users():
    return list(user_col.find())


def get_users_by_name(substring: str):
    return list(user_col.find({"name": {"$regex": {re.escape(substring)}}}))


def get_user_by_email(email: str):
    return user_col.find_one({"email": email})


def get_user_refresh_token(email: str):
    return refresh_token_col.find_one({"user_email": email})


def set_user_active(email: str):
    user_col.update_one({"email": email}, {"$set": {"is_active": True}})


def create_refresh_token(user_email: str, token: str, expires_at: datetime):
    refresh_token = models.RefreshToken(
        user_email=user_email, token=token, expires_at=expires_at
    )
    refresh_token_col.insert_one(refresh_token.model_dump())
    return refresh_token


def revoke_refresh_token(user_email: str):
    refresh_token_col.update_one(
        {"user_email": user_email}, {"$set": {"is_revoked": True}}
    )


def write_log(user_email: str, action: str, detail: str, status: str):
    log = models.AuditLog(
        user_email=user_email,
        action=action,
        detail=detail,
        created_at=datetime.now(timezone.utc),
        status=status,
    )
    audit_log_col.insert_one(log.model_dump())
    return log


# Utility functions for product management
def get_all_items():
    return list(item_col.find())


def get_items_by_page(page: int, num_per_page: int, sort_by_column: str, is_ascend: bool):
    return list(item_col.find().sort(sort_by_column, 1 if is_ascend else -1).skip(page * num_per_page).limit(num_per_page))


def get_items_by_name(substring: str):
    return list(item_col.find_one({"name": {"$regex": re.escape(substring)}}))


def get_unique_item_by_name(name: str):
    return item_col.find_one({"name": name})


def get_items_by_price_range(lower_bound: int = 0, upper_bound: int = 100000000):
    return list(item_col.find({"price": {"$gt": lower_bound, "$lt": upper_bound}}))


def create_invoice(info: schemas.UserCreateInvoice):
    invoice = models.Invoice(**info.model_dump())
    print(invoice.model_dump())
    invoice_col.insert_one(invoice.model_dump())
    return schemas.InvoiceResponse(**invoice.model_dump())


def get_invoices_by_user_email(email: str):
    return list(invoice_col.find({"user_email": email}))


def create_user(info: schemas.UserCreate):
    info = info.model_dump()
    info["hashed_password"] = info["password"]
    del info["password"]
    info["hashed_password"] = dependencies.hash_password(info["hashed_password"])
    info["is_active"] = False
    info["is_disabled"] = False
    info["roles"] = sorted(info["roles"])
    print(info)
    user = models.User(**info)
    user.full_name
    user['full_name']
    user_col.insert_one(user.model_dump())
    return user

def update_user_roles(email: str, roles: list[str]):
    user_col.update_one({"email": email}, {"$set": {"roles": roles}})
    return {"message": "User roles updated successfully"}


def delete_user(email: str):
    user_col.delete_one({"email": email})
    return {"message": "User deleted successfully"}


def create_item(info: schemas.ItemCreate):
    item = models.Item(**info.model_dump())
    item_col.insert_one(item.model_dump())
    return item 

def set_item_quantity(name: str, quantity: int):
    item_col.update_one({"name": name}, {"$set": {"quantity": quantity}})
    return {"message": "Item quantity set successfully"}

def update_item_quantity(name: str, delta: int):
    item_col.update_one({"name": name}, {"$inc": {"quantity": delta}})
    return {"message": "Item quantity updated successfully"}

