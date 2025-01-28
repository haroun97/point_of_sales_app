from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.OAuth2 import get_password_hash
from app import models, schemas, enums
from app.crud.auth import add_confirmation_code
from app.crud.error import add_error, get_error_message
from app.external_services import emailService
import uuid

# employee code
def get_employee(db: Session, id: int):
    return db.query(models.employee).filter(models.employee.id == id).first()

def edit_employee(db: Session, id: int, new_data: dict):
    db.query(models.employee).filter(models.employee.id == id).update(new_data, synchronize_session=False)
    
def get_employee_by_email(db: Session, email: str):
    return db.query(models.employee).filter(models.employee.email == email).first()

def get_employee(db: Session, skip:int = 0, limit: int = 100):
    return db.query(models.employee).offset(skip).limit(limit).all()

async def add_employee(db:Session, employee: schemas.employeeCreate):
    employee.password = get_password_hash(employee.password)
    employee_data = employee.model_dump()
    employee_data.pop('confirm_password')
    roles = employee_data.pop('roles')
    #add employee
    db_employee = models.employee(**employee_data)
    db.add(db_employee)
    db.flush() #update changes in database.
    #add employee roles
    db.add_all([models.employeeRole(role=role, employee_id=db_employee.id) for role in roles])
    #add confirmation code 
    activation_code = add_confirmation_code(db, db_employee)

    #send confirmation email
    await emailService.simple_send([db_employee.email], {
        "token": activation_code.token,
        "psw": employee.password,
        "name": db_employee.first_name
        }, enums.EmailTemplate.ConfirmAccount,
    )
    db.commit()
    return db_employee
