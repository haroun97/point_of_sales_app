from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session  # This imports the type
from fastapi import Depends

from app.OAuth2 import get_curr_employee
from .database import get_db

dbDep = Annotated[Session, Depends(get_db)]

#Dependency
class PaginationParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

paginationDep = Annotated[PaginationParams, Depends()]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # create schema
tokenDep = Annotated[str, Depends(oauth2_scheme)]
formaDataDep = Annotated[OAuth2PasswordRequestForm, Depends()]
def get_current_employee(db: dbDep, token: tokenDep):
    return get_curr_employee(db, token)