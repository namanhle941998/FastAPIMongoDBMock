from middleware import crud, pubsub
from fastapi import HTTPException

subscriber = pubsub.Subscriber("authorization")
subscriber.subscribe("user_login")

def require_role(role: str, email: str):
    user = crud.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if role not in user["roles"]:
        raise HTTPException(status_code=403, detail="User does not have permission")
    return True

def require_one_of_roles(roles: list[str], email: str):
    user = crud.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for role in roles:
        if role.value in user["roles"]:
            return True
    raise HTTPException(status_code=403, detail="User does not have permission")

def add_role(email: str, role: str):
    user = crud.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if role not in user["roles"]:
        user["roles"].append(role)
    crud.update_user_roles(email, user["roles"])
    return user
