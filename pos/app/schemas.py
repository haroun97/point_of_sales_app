from datetime import datetime, date
from pydantic import BaseModel
from app.enums import contractType, gender, accountStatus, roleType
from typing import List, Optional, Dict

from app.enums.matchyComparer import Comparer
from app.enums.matchyConditionProperty import ConditonProperty
from app.enums.matchyFieldType import FieldType

class ourBaseModel(BaseModel):
    class config:
        orm_mode = True

class employeeBase(ourBaseModel):
    
    first_name: str 
    last_name: str
    number: int
    email: str
    password: int | None = None
    address: int
    gender: gender
    roles: List[roleType]
    phonee_number: int | None = None
    birth_date: date | None = None
    contract_type: contractType
    cnss_number: str | None = None
    
class employeeCreate(employeeBase):
    password: str | None = None
    confirm_password: str | None = None

class employeeOut(employeeBase):
    id: int
    created_on: datetime

class confirmAccount(ourBaseModel):
    confirmation_code: str

class baseOut(ourBaseModel):
    detail: str
    status_code: int

class MatchyCondition(ourBaseModel):
    property: ConditonProperty
    comparer: Optional [Comparer]
    value: int| float | str | List[str]
    custom_fail_message: Optional[str] = None

class MatchyOption(ourBaseModel):
    display_value: str
    value: Optional[str] = None
    mondatory: Optional[bool] = False
    type: FieldType
    Condition: Optional[List[MatchyCondition]] = []

class ImportPossibleFields(ourBaseModel):
    possible_fields: List[MatchyOption] = []

class MatchyCell(ourBaseModel):
    value: str
    rowIndex: int
    colIndex: int

class MatchyUploadEntry(ourBaseModel):
    lines: List[Dict[str, MatchyCell]] # a list contains many dicts, e.g: [{CNSS Number: { 40, 1(Col), 1(row)}, {roles, vendor, 3, 5}}]
    
class MatchyWrongCell(ourBaseModel):
    message: str
    rowIndex: int
    colIndex: int   

class ImportResponse(ourBaseModel):
    errors: str
    Warnings: str
    wrongCells: list[MatchyWrongCell]
