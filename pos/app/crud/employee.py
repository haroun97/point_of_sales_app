from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.OAuth2 import get_password_hash
from app import models, schemas, enums
from app.crud.auth import add_confirmation_code
from app.dependencies import PaginationParams, paginationParams
from app.external_services import emailService

# employee code
def get_employee(db: Session, id: int):
    return db.query(models.employee).filter(models.employee.id == id).first()

def sudo_edit_employee(db: Session, id: int, new_data: dict):
    db.query(models.employee).filter(models.employee.id == id).update(new_data, synchronize_session=False)
    
def get_employee_by_email(db: Session, email: str):
    return db.query(models.employee).filter(models.employee.email == email).first()

def div_ceil(nominator, denominator):
    full_pages = nominator // denominator
    additional_page = 1 if nominator % denominator > 0 else 0
    return full_pages + additional_page


def get_employees(db: Session, pagination_param: PaginationParams, name_substr):
    query = db.query(models.employee)
    if name_substr:
        query = query.filter(func.lower(func.concat(models.employee.first_name,' ', models.last_name)).contains(func.lower(name_substr)))
    
    total_records = query.count()
    total_pages = div_ceil(total_records, pagination_param.page_size)
    employees = query.limit(pagination_param.page_size.offset((pagination_param.page_number-1)*pagination_param.page_size))    
    return (employees, total_records, total_pages)
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
    activation_code = add_confirmation_code(db, db_employee.id)

    #send confirmation email
    await emailService.simple_send([db_employee.email], {
        "token": activation_code.token,
        "psw": employee.password,
        "name": db_employee.first_name
        }, enums.EmailTemplate.ConfirmAccount,
    )
    db.commit()
    return db_employee

async def edit_empployee(db: Session, id: int, entry: schemas.EmployeeEdit):
    query = db.query(models.employee).filter(models.employee.id == id)
    employee_in_db = query.first()

    if not employee_in_db:
        raise HTTPException(status_code=400, detail="Employee not found")
    
    fields_to_update = entry.model_dump()
    for field in ["email", "password", "confirm_password", "roles", "actual_password"]:
        fields_to_update.pop(field)


    #manage role after reading relationships
   
    #if edit email orpsw
    if employee_in_db.email != entry.email:
        if not entry.actual_password or get_password_hash(entry.password) != employee_in_db.password:
            raise HTTPException(status_code=400, detail="Current password is missing or incorrect. It's mondatory to set new password")
        fields_to_update[models.employee.email] = entry.email
        fields_to_update[models.employee.account_status] = enums.accountStatus.INACTIVE
        

    #if edit psw
    if entry.password and get_password_hash(entry.password) != employee_in_db.password:
        if entry.password != entry.confirm_password:
            raise HTTPException(status_code=400, detail="Password must mutch")
        
        if not entry.actual_password or get_password_hash(entry.password) != employee_in_db.password:
            raise HTTPException(status_code=400, detail="Current password is missing or incorrect. It's mondatory to set new password")

        fields_to_update[models.employee.password] = get_password_hash(entry.password)

    query.update(fields_to_update, synchronize_session=False)
    
    if models.employee.email in fields_to_update:
        activation_code = add_confirmation_code(db, employee_in_db.id, fields_to_update[models.employee.email])

        #send confirmation email
        await emailService.simple_send([employee_in_db.email], {
            "token": activation_code.token,
            "name": employee_in_db.first_name,
            }, enums.EmailTemplate.ConfirmAccount,
        )
    db.commit()