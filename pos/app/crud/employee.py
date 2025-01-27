from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.OAuth2 import get_password_hash
from app import models, schemas, enums
from app.crud.error import add_error, get_error_message
from app.external_services import emailService
import uuid

error_keys = {
    "employee_roles_employee_id_fkey":"No employee with this id",
    "employee_roles_pkey":"No employee role with this id",
    "ck_employees_cnss_number":"It should be {8 digitds}.{2 digits} and it's mondatory for cdi and cdd",
    "employees_email_key":"Email already used",
    "employees_pkey":" No employee with id",
}
# confirm account code
def get_confirmation_code(db: Session, code: str):
    return db.query(models.accountActivation).filter(models.accountActivation.token == code).first()

def add_confirmation_code(db: Session,db_employee: models.employee):
    activation_code = models.accountActivation(employee_id=db_employee.id, email=db_employee.email, status=enums.tokenStatus.PENDING, token=uuid.uuid1())
    db.add(activation_code)
    return activation_code

def edit_confirmation_code(db: Session, id: int, new_data: dict):
        db.query(models.accountActivation).filter(id).update(new_data, synchronize_session=False)

# reset password code
def get_reset_code(db: Session, code: str):
    return db.query(models.resetPassword).filter(models.resetPassword.token == code).first()

def add_reset_code(db: Session,db_employee: models.employee):
    reset_code = models.resetPassword(employee_id=db_employee.id, email=db_employee.email, status=enums.tokenStatus.PENDING, token=uuid.uuid1())
    db.add(reset_code)
    return reset_code

def edit_reset_code(db: Session, id: int, new_data: dict):
    db.query(models.resetPassword).filter(id).update(new_data, synchronize_session=False)

# employee code
def get_employee(db: Session, id: int):
    return db.query(models.employee).filter(models.employee.id == id).first()

def edit_employee(db: Session, id: int, new_data: dict):
    db.query(models.employee).filter(models.employee.id == id).update(new_data, synchronize_session=False)
    
def get_employee_by_email(db: Session, email: str):
    return db.query(models.employee).filter(models.employee.email == email).first()

def get_employee(db: Session, skip:int = 0, limit: int = 100):
    return db.query(models.employee).offset(skip).limit(limit).all()

async def add(db:Session, employee: schemas.employeeCreate):
    try:
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
    except Exception as err:  #General error handling
        db.rollback()
        text = str(err)
        add_error(text, db)
        #Attempt to extract a status code dynamically
        status_code = getattr(err, "status_code", 400)  #Default to 400 if not found
        raise HTTPException(
            status_code=status_code,
            detail=get_error_message(text),
        )

    return schemas.employeeOut(**db_employee.__dict__)