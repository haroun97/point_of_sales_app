from fastapi import HTTPException,  status
from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from app import models
from app.schemas import TokenData
from datetime import datetime, timedelta, timezone
import jwt
from .config import settings


# to get a string like this run:
# Move them to .env later
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_min

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_employee(db, email):
    return db.query(models.employee).filter(models.employee.email==email).first()

def get_curr_employee(db, token):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    employee = get_employee(db, token_data.email)
    if employee is None:
        raise credentials_exception
    return employee

def authenticate_employee(db, email, password):
    employee = get_employee(db, email)
    if not employee:
        return False
    if not verify_password(password, employee.hashed_password):
        return False
    return employee
