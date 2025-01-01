from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from . import models, schemas, enums
from . import emailUtil
import uuid

def get_confirmation_code(db: Session, code: str):
    return db.query(models.accountActivation).filter(models.accountActivation.token == code).first()

def get(db: Session, id: int):
    return db.query(models.employee).filter(models.employee.id == id).first()

def get_by_email(db: Session, email: str):
    return db.query(models.employee).filter(models.employee.email == email).first()

def get_all(db: Session, skip:int = 0, limit: int = 100):
    return db.query(models.employee).offset(skip).limit(limit).all()

error_keys = {
    "employee_roles_employee_id_fkey":"No employee with this id",
    "employee_roles_pkey":"No employee role with this id",
    "ck_employees_cnss_number":"It should be {8 digitds}.{2 digits} and it's mondatory for cdi and cdd",
    "employees_email_key":"Email already used",
    "employees_pkey":" No employee with id",
}


def get_error_message(error_message):
    for error_key in error_keys:
        if error_key in error_message:
            return error_keys[error_key]
    return "Something went wrong"

def add_error(text, db:Session):
    try:
        db.add(models.error(
            text = text,
        ))
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Something went wrong",
        )

async def add(db:Session, employee: schemas.employeeCreate):
    try:
        #fix me later when reading about the security 
        not_hashed_password = employee.password
        employee.password = employee.password
        employee_data = employee.model_dump()
        employee_data.pop('confirm_password')
        roles = employee_data.pop('roles')
        #at this moment in the database the id = null.
        #add employee
        db_employee = models.employee(**employee_data)
        db.add(db_employee)
        db.flush() #update changes in database.
        db.refresh(db_employee)#After refreshing the data base we can get the id.

        #add employee roles
        #for role in roles:
        #    db_role = models.employeeRole(role=role, employee_id=db_employee.id)
        #    db.add(db_role)
        #    db.flush() #update changes in database.
        #    db.refresh(db_role)
        db.add_all([models.employeeRole(role=role, employee_id=db_employee.id) for role in roles])
        #add confirmation code fix me later, duplicated code
        activation_code = models.accountActivation(employee_id=db_employee.id, email=db_employee.email, status=enums.tokenStatus.PENDING, token=uuid.uuid1())
        db.add(activation_code)
        #send confirmation email
        await emailUtil.simple_send([db_employee.email], {
            "token": activation_code.token,
            "psw": not_hashed_password,
            "name": db_employee.first_name
            }
        )
        db.commit()
    except Exception as err:  #General error handling
        db.rollback()
        text = str(err)
        print(get_error_message(text))
        add_error(text, db)
        #Attempt to extract a status code dynamically
        status_code = getattr(err, "status_code", 400)  #Default to 400 if not found
        raise HTTPException(
            status_code=status_code,
            detail=get_error_message(text),
        )
    '''
    except IntegrityError as db_err:  #Handle database integrity errors
        db.rollback() #Undo changes made for the database when an error accurs.
        print(get_error_message(db_err))
        print("Database Error:", db_err)
        raise HTTPException(
            status_code=409,  #Conflict: likely a unique constraint violation
            detail="A record with the same email or data already exists.",
        )
    except SQLAlchemyError as sql_err:  #Detects errors related to sqlalchemy integrity constraint, such as: Unique constraint violations (e.g., duplicate primary keys). Foreign key violations. NOT NULL constraint violations.
        db.rollback()
        print(get_error_message(str(sql_err)))
        #print("SQLAlchemy Error:", sql_err)
        raise HTTPException(
            status_code=500,  #Internal Server Error for generic DB issues
            detail="A database error occurred. Please try again later.",
        )
    '''

    return schemas.employeeOut(**db_employee.__dict__)
