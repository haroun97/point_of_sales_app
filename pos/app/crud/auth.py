from sqlalchemy.orm import Session
from app import models, enums
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

def add_confirmation_code(db: Session, id:int, email:str):
    activation_code = models.accountActivation(employee_id=id, email=email, status=enums.tokenStatus.PENDING, token=uuid.uuid1())
    db.add(activation_code)
    return activation_code

def edit_confirmation_code(db: Session, id: int, new_data: dict):
        db.query(models.accountActivation).filter(models.accountActivation.id == id).update(new_data, synchronize_session=False)

# reset password code
def get_reset_code(db: Session, code: str):
    return db.query(models.resetPassword).filter(models.resetPassword.token == code).first()

def add_reset_code(db: Session,db_employee: models.employee):
    reset_code = models.resetPassword(employee_id=db_employee.id, email=db_employee.email, status=enums.tokenStatus.PENDING, token=uuid.uuid1())
    db.add(reset_code)
    return reset_code

def edit_reset_code(db: Session, id: int, new_data: dict):
    db.query(models.resetPassword).filter(models.resetPassword.id == id).update(new_data, synchronize_session=False)
