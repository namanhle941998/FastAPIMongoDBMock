from datetime import datetime, timedelta, timezone
from typing import Annotated
import json

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from middleware.models import User
from middleware.schemas import TokenData
from middleware import crud
from middleware import redis

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Utility functions for password hashing and token creation
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user_from_db(email: str):
    user = crud.user_col.find_one({"email": email})
    if not user:
        return None
    else:
        return User(**user)


def get_user_from_db_with_redis(email: str):
    cache_user = redis.get_cache(email)
    if cache_user:
        print("Cache hit")
        print(cache_user)
        return User(**json.loads(cache_user))
    print("Cache miss")
    user = crud.user_col.find_one({"email": email})
    if not user:
        return None
    else:
        redis.set_cache(email, json.dumps(User(**user).model_dump()))
        return User(**user)


def authenticate_user(email: str, password: str):
    user = get_user_from_db(email)
    print(user)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    crud.create_refresh_token(data["sub"], encoded_jwt, expire)
    return encoded_jwt


def get_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # this function will encrypt the signing input of the token
        # compare it to the signature in the token
        # and if they match, return the payload; if not, raise an error
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user_from_db(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


def get_current_user(current_user: Annotated[User, Depends(get_user)]):
    print(current_user)
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive User")
    return current_user


def get_current_admin(current_admin: Annotated[User, Depends(get_user)]):
    print(current_admin)
    if not current_admin.is_active:
        raise HTTPException(status_code=400, detail="Inactive User")
    if "Admin" not in current_admin.roles:
        raise HTTPException(status_code=400, detail="User is not an admin")
    return current_admin
