from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from middleware.models import User
from middleware.schemas import UserCreate, Token
from middleware import dependencies, crud, authorization, pubsub
from utilites import constants

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

producer = pubsub.Producer("auth")

# Endpoints for users
@router.post("/register", response_model=User)
def register(user: UserCreate):
    if dependencies.get_user_from_db(user.email):
        crud.write_log(user.email, "register", "Email already exists", "failed")
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = UserCreate(
        email=user.email,
        password=user.password,
        full_name=user.full_name,
        roles=user.roles,
    )
    return_user = crud.create_user(new_user)
    crud.write_log(user.email, "register", "User registered successfully", "success")
    return return_user


@router.post("/login")
def login(formData: OAuth2PasswordRequestForm = Depends()):
    user = dependencies.authenticate_user(formData.username, formData.password)
    if not user:
        crud.write_log(
            formData.username, "login", "Incorrect username or password", "failed"
        )
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = dependencies.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = dependencies.create_refresh_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    crud.set_user_active(user.email)
    crud.write_log(user.email, "login", "User logged in successfully", "success")
    producer.publish("user_login", {"email": user.email, "message": "User logged in successfully", "status": "success"})
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/logout")
def logout(current_user: User = Depends(dependencies.get_current_user)):
    dependencies.user_col.update_one(
        {"email": current_user.email}, {"$set": {"is_active": False}}
    )
    crud.revoke_refresh_token(current_user.email)
    crud.write_log(
        current_user.email, "logout", "User logged out successfully", "success"
    )
    return {"message": "User logged out successfully"}


@router.post("/refresh_token")
def refresh_token(current_user: User = Depends(dependencies.get_current_user)):
    refresh_token = crud.get_user_refresh_token(current_user.email)
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token not found")
    access_token = dependencies.create_access_token(
        data={"sub": current_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token["token"],
        token_type="bearer",
    )


@router.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(dependencies.get_current_user)):
    return current_user


# Redis testing
@router.get("/users/{email}", response_model=User)
def read_user(email: str):
    user = dependencies.get_user_from_db_with_redis(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Endpoints for admin
@router.post("/create_user", response_model=User)
def create_user(user: UserCreate, current_user=Depends(dependencies.get_current_user)):
    authorization.require_one_of_roles(
        [constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email
    )
    if dependencies.get_user_from_db(user.email):
        crud.write_log(user.email, "create_user", "Email already exists", "failed")
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = UserCreate(
        email=user.email,
        password=user.password,
        full_name=user.full_name,
        roles=user.roles,
    )
    return_user = crud.create_user(new_user)
    crud.write_log(user.email, "create_user", "User created successfully", "success")
    return return_user


@router.post("/delete_user")
def delete_user(email: str, current_user=Depends(dependencies.get_current_user)):
    authorization.require_one_of_roles(
        [constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email
    )
    dependencies.user_col.delete_one({"email": email})
    crud.write_log(email, "delete_user", "User deleted successfully", "success")
    return {"message": "User deleted successfully"}


# Endpoints for moderator
@router.post("/update_user_roles")
def update_user_roles(
    email: str, roles: list[str], current_user=Depends(dependencies.get_current_user)
):
    authorization.require_one_of_roles([constants.Role.MODERATOR], current_user.email)
    crud.update_user_roles(email, roles)
    crud.write_log(
        email, "update_user_roles", "User roles updated successfully", "success"
    )
    return {"message": "User roles updated successfully"}

# /v1/admin/** endpoints => ADMIN role ADMIN => /v1/admin/** endpoints
# /v1/admin/cart
# /v1/admin/invoice

# 
@router.post("/add_user_role")
def add_user_role(
    email: str, role: str, current_user=Depends(dependencies.get_current_user)
):
    authorization.require_one_of_roles([constants.Role.MODERATOR], current_user.email)
    user = crud.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if role not in user["roles"]:
        user["roles"].append(role)
    crud.update_user_roles(email, user["roles"])
    crud.write_log(email, "add_user_role", "User role added successfully", "success")
    return user
