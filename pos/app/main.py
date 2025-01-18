from typing import Annotated
import uuid
from fastapi import FastAPI, Depends, HTTPException, Header, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app import crud, schemas, emailUtil, enums, models
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session  # This imports the type
from .database import sessionLocal
from datetime import datetime
import re
app = FastAPI()

# Fix me: use specific origins later
""" origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
] """

app.add_middleware(
    CORSMiddleware,
    #allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Dependency
class PaginationParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
        
async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

paginationDep = Annotated[PaginationParams, Depends()]
dbDep = Annotated[Session, Depends(get_db)]

@app.get("/employee/")
def get_all(db: dbDep , pagination_params: paginationDep ):   
    return db.query(models.employee).all()
     
def get_all_products(db: dbDep, pagination_params: paginationDep, key: Annotated[str, Depends(verify_key)]):   
    # The key is need to fill something
    return db.query(models.Product).all()

@app.get("/")
async def root():
    return await emailUtil.simple_send(["hldeco2023@gmail.com"], {
        "first_name" : "fred",
        "last-name" : "fredson"
        }
    )

@app.post("/employee/", response_model=schemas.employeeOut)
async def create_user(employee: schemas.employeeCreate, db: Session = Depends(get_db)):
    try:
        if employee.password != employee.confirm_password:
            raise HTTPException(status_code=400, detail="Password must match!")
        '''db_employee = crud.get_by_email(db, email = employee.email)
        if db_employee:
            raise HTTPException(status_code=400, detail="Email already exist")
            '''
    except IntegrityError as ie:
        db.rollback()
        print("Integrity Error:", ie)
        raise HTTPException( # This error is raied when "ennazeha" the integrity of the data is affected
            status_code=409,
            detail="Database integrity error: Possible duplicate or invalid data."
        )
    except SQLAlchemyError as se:
        db.rollback()
        print("SQLAlchemy Error:", se)
        raise HTTPException(
            status_code=500,
            detail="A database error occurred. Please try again later."
        )
    except Exception as err:
        db.rollback()
        print("Unexpected Error:", err)
        raise HTTPException(
            status_code=400,
            detail=str(err)
        )
    return await crud.add(db=db, employee=employee)

@app.patch("/employee", response_model=schemas.baseOut)
def confirm_account(confirAccountInput: schemas.confirmAccount, db:Session = Depends(get_db)): #Depends means we have dependencies with database.
    try:    
        confirmation_code = crud.get_confirmation_code(db, confirAccountInput.confirmation_code)
        if not confirmation_code:
            raise HTTPException(status_code=400, detail="Token Does not exist")
        if confirmation_code.status == enums.tokenStatus.USED:
            raise HTTPException(status_code=400, detail="Token is already used")
        diff = (datetime.now() - confirmation_code.created_on).seconds # time in seconds
        if diff > 3600:
            raise HTTPException(status_code=400, detail="token expired")
        
        #Employee activated
        db.query(models.employee).filter(models.employee.id == confirmation_code.employee_id).\
        update({models.employee.account_status: enums.accountStatus.ACTIVE}, synchronize_session=False)

        db.commit() #Save changes in the database

        #Token used ==> we cannot use this token again
        db.query(models.accountActivation).filter(models.accountActivation.id == confirmation_code.id).\
        update({models.accountActivation.status: enums.tokenStatus.USED}, synchronize_session=False)

        db.commit() #Save changes in the database
    except SQLAlchemyError as se:
        db.rollback()
        print("SQLAlchemy Error:", se)
        raise HTTPException(
            status_code=500,
            detail="A database error occurred. Please try again later."
        )
    except Exception as err:
        db.rollback()
        print("Unexpected Error:", err)
        raise HTTPException(
            status_code=400,
            detail=str(err)
        )
    
    return schemas.baseOut(
        detail="Account confirmed",
        status_code=status.HTTP_200_OK
    )

email_regex = r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$' # r is raw string is used to make backslashes part of the string not a part of the code.
cnss_number_regex = r'^\d{8}-\d{2}$'
phone_number_regex = r'^(\+49|0049|0)?[1-9]\d{1,4}[-\s]?(\(?\d+\)?[-\s]?)*\d$'



mondatory_fields = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "Email",
    "password": "Password",
    "number": "Number",
    "contract_type": "Contract Type",
    "gender": "Gender",
    "employee_roles": "Roles",  
}

mondatory_with_condition = {
    "cnss_number": ("CNSS Number", lambda employee: is_cdi_or_cdd(employee)) # tuple inside a dict tuple. Note: We cannot change the values of a tuple.
}

optional_fields = {
    "birth_date": "Birth Date",
    "address": "Address",
    "phone_number": "Phone Number"
}

possible_fields = {
    **mondatory_fields, # ** lists all the options of mondary_fields dictionary
    **mondatory_with_condition,
    **optional_fields,
}

unique_fields = {
    "email": models.employee.email,
    "number": models.employee.number,
}


options = [
    schemas.MatchyOption(display_value=mondatory_fields["first_name"], value="first_name", mondatory=True, type=enums.FieldType.string),
    schemas.MatchyOption(display_value=mondatory_fields["last_name"], value="last_name", mondatory=True, type=enums.FieldType.string),

    schemas.MatchyOption(display_value=mondatory_fields["email"], value="email", mondatory=True, type=enums.FieldType.string, Condition=[
        schemas.MatchyCondition(property=enums.ConditonProperty.regex, comparer=enums.Comparer.e, value=email_regex)]),

    schemas.MatchyOption(display_value=mondatory_fields["password"], value="password", mondatory=True, type=enums.FieldType.string),
    schemas.MatchyOption(display_value=mondatory_fields["number"], value="number", mondatory=True, type=enums.FieldType.string),
    schemas.MatchyOption(display_value=optional_fields["address"], value="address", mondatory=False, type=enums.FieldType.string),
    schemas.MatchyOption(display_value=optional_fields["birth_date"], value="birth_date", mondatory=False, type=enums.FieldType.string),

    schemas.MatchyOption(display_value=mondatory_with_condition["cnss_number"][0], value="cnss_number", mondatory=True, type=enums.FieldType.string, Condition=[
        schemas.MatchyCondition(property=enums.ConditonProperty.regex, comparer=enums.Comparer.e, value=cnss_number_regex)]),

    schemas.MatchyOption(display_value=mondatory_fields["contract_type"], value="contract_type", mondatory=True, type=enums.FieldType.string, Condition=[
        schemas.MatchyCondition(property=enums.ConditonProperty.value, comparer=enums.Comparer._in, value=enums.contractType.getPossibleValues())]),

    schemas.MatchyOption(display_value=mondatory_fields["gender"], value="gender", mondatory=True, type=enums.FieldType.string, Condition=[
        schemas.MatchyCondition(property=enums.ConditonProperty.value, comparer=enums.Comparer._in, value=enums.gender.getPossibleValues())]),

    schemas.MatchyOption(display_value="Account Status", value="account_status", mondatory=True, type=enums.FieldType.string, Condition=[
        schemas.MatchyCondition(property=enums.ConditonProperty.value, comparer=enums.Comparer._in, value=enums.accountStatus.getPossibleValues())]),

    schemas.MatchyOption(display_value=mondatory_fields["employee_roles"], value="employee_roles", mondatory=True, type=enums.FieldType.string, Condition=[
        schemas.MatchyCondition(property=enums.ConditonProperty.value, comparer=enums.Comparer._in, value=enums.gender.getPossibleValues())]),

    schemas.MatchyOption(display_value=optional_fields["phone_number"], value="phone_number", mondatory=False, type=enums.FieldType.string, Condition=[
        schemas.MatchyCondition(property=enums.ConditonProperty.regex, comparer=enums.Comparer.e, value=phone_number_regex)]),
]
#move me later to util folder
def is_regex_matched(pattern, field):
    return field if re.match(pattern, field) else None 

def is_valid_email(field: str):
    return field if is_regex_matched(email_regex, field) else None

def is_positive_int(field: str):
    try: 
        res = int(field) # try to cast to int
    except:
        return None # not parsable to int
    return res if res >= 0 else None

def is_valid_date(field: str):
    try:
        obj = datetime.strptime(field, '%d/%m/%y') # convert string to date format
        return obj.isoformat() # not parsable to int
    except:
        return None


def is_cdi_or_cdd(employee):
    return employee["contract_type"].value in [enums.contractType.CDI, enums.contractType.CDD]


def is_valid_cnss_number(field):
    return field if is_regex_matched(cnss_number_regex, field) else None

def is_valid_phone_number(field):
    return field if is_regex_matched(phone_number_regex, field) else None

def are_valid_roles(field):
    res = []
    for role_name in field.split(','):
        val = enums.roleType.is_valid_enum_value(role_name)
        if not val:
            return None
        res = res.append(val)
    return res # res contains a list of roles

fields_check = {
    #field to validate: (function to validate, return error message in case of wrong input value)
    "email": (lambda field: is_valid_email(field), "Wrong Email format"),
    "gender": (lambda field: enums.gender.is_valid_enum_value(field), f"Possible values are: { enums.gender.getPossibleValues()}"),
    "contract_type": (lambda field: enums.contractType.is_valid_enum_value(field), f"Possible values are: { enums.contractType.getPossibleValues()}"),
    "number": (lambda field: is_positive_int(field), f"It should be integer >= 0:"),
    "birthdate": (lambda field: is_valid_date(field), f"Dates format should be dd/mm/yyyy"),
    "cnss_number": (lambda field: is_valid_cnss_number(field), f"It should be (8_digit)-(2 digits) and it's valid only for CDI and CDD"),
    "phone_number": (lambda field: is_valid_phone_number(field), f"this number is not valid for germany, it should start with +49 or 0049 and contain 10 digits"),
    "employee_roles": (lambda field: are_valid_roles(field), f"Possible values are: { enums.roleType.getPossibleValues()}"),

}

def is_field_mondatory(employee, field):
    return field in mondatory_fields or (field in mondatory_with_condition and mondatory_with_condition[field][1](employee))

def validate_employee_data(employee):
    errors = [] # stores the errors in a list
    warnings = [] # stores the warnings in a list
    wrong_cells = [] # To store wrongs cells in order to color wrong cells with red in matchy interface.
    employee_to_add = { field: cell.value for field, cell in employee.items()}
    for field in possible_fields:
        if field not in employee:
            if is_field_mondatory(employee, field):
                errors.append(f"{possible_fields[field]} is mondatory but missing")
            continue
    cell = employee[field]
    employee_to_add[field]= employee_to_add[field].strip() # strip() removes the space at beginning and at the end of the string

    if employee_to_add[field] == '':
        if is_field_mondatory(employee, field):
            msg = f"{possible_fields[field]} is mondatory but missing"
            errors.append(msg)
            wrong_cells.append(schemas.MatchyWrongCell(message=msg, rowIndex=cell.rowIndex, colIndex=cell.colIndex))
        else:
            employee_to_add[field] = None # In db will be stored as Null
    elif field in fields_check:
        converted_val = fields_check[field][0](employee_to_add[field])
        if converted_val is None: 
            msg = fields_check[field][1]
            (errors if is_field_mondatory(employee, field) else warnings).append(msg)
            wrong_cells.append(schemas.MatchyWrongCell(message=msg, rowIndex=cell.rowIndex, colIndex=cell.colIndex))
        else:
            employee_to_add[field] = converted_val
 
    return (errors, warnings, wrong_cells, employee_to_add)



def valid_employees_data_and_upload(employees:list, force_upload: bool, backgroundTask: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        errors = [] # stores the errors in a list
        warnings = [] # stores the warnings in a list
        wrong_cells = [] # To store wrongs cells in order to color wrong cells with red in matchy interface.
        employees_to_add = [] # To store all employee data together and store them in the db at once.
        roles_per_email = {}
        roles =[]
        for line, employee in enumerate(employees): # for i in range(len(employees)) line = i, employee = employees[i]
            emp_errors, emp_warnings, emp_wrong_cells, emp = validate_employee_data(employee)
            if emp_errors:
                msg = {'\n'}.join(emp_errors)
                errors.append(f"Line {line + 1}:\n{msg}")
            if emp_warnings:
                msg = {'\n'}.join(emp_warnings)
                errors.append(f"Line {line + 1}:\n{msg}")
            if emp_wrong_cells:
                wrong_cells.extend(emp_wrong_cells)
                errors.append(f"Line {line + 1}:\n{msg}")
        
            roles_per_email[emp.get("email")] = emp.pop('employee_roles') # Email unique
            emp['password'] = uuid.uuid1() # It allows us to generate password to employee
            employees_to_add.append(models.employee(**emp))

        
        for field in unique_fields:
            values = {}
            for line, employee in enumerate(employees):
                cell = employee.get(field)
                val = cell.value.strip()
                if val == '': # If it's mondatory, email and number were already checked in fields check
                    continue
                if val in values:
                    msg = f"{possible_fields[field]} should be unique. but this value exists more that one time in the file"
                    (errors if is_field_mondatory(employee, field) else warnings).append(msg)
                    wrong_cells.append(schemas.MatchyWrongCell(message=msg, rowIndex=cell.rowIndex, colIndex=cell.colIndex))
                else: 
                    values.add(val)

                duplicated_vals = set(db.query(unique_fields[field]).filter(unique_fields[field].in_(values)).all())
                duplicated_vals = {str([val[0] for val in duplicated_vals])}
                if duplicated_vals:
                    msg = f"{possible_fields[field]} should be unique. {(', ').join(duplicated_vals)} already exist in databse"
                    (errors if is_field_mondatory(employee, field) else warnings).append(msg)
                    for employee in employees:
                        cell = employee.get(field)
                        val = cell.value.strip()
                        if val in duplicated_vals:
                            wrong_cells.append(schemas.MatchyWrongCell(message=msg, rowIndex=cell.rowIndex, colIndex=cell.colIndex))



        if errors or (warnings and not force_upload):
            return schemas.ImportResponse(
                errors=('\n').join(errors),
                warnings=('\n').join(warnings),
                wrongCells=wrong_cells,
                detail="Something went wrong",
                status_code="400",
            )

        db.add_all(employees_to_add)
        db.flush() # Field id contains value (email)

        #case 1: imagine employees lost their order
        employee_roles = []
        for emp in employees_to_add:
            for role in roles_per_email[emp.email]:
                employee_roles.append(models.employeeRole(employee_id=em.id, role=role))
                
        db.add_all([[models.employeeRole(employee_id=emp.id, role=roles) for emp in roles_per_email[emp.email]] for emp in employees_to_add])
        db.flush()

        activation_code_to_add = []
        email_data = []
        for emp in employees_to_add:
            token = uuid.uuid1()
            activation_code = models.accountActivation(employee_id=emp.id, email=emp.email, status=enums.tokenStatus.PENDING, token=uuid.uuid1())
            activation_code_to_add.append(activation_code)
            email_data.append(([emp.email],{
            "name": emp.first_name,
            "code": token,
            "psw": emp.password
            }))

        db.add_all(activation_code_to_add)

        for email_datum in email_data:
            #send confirmation email
            backgroundTask.add_task(emailUtil.simple_send,email_datum[0], email_datum[1])
            

        db.commit()

    except Exception as err:  #General error handling
        db.rollback()
        text = str(err)
        crud.add_error(text, db)
        raise HTTPException(status_code=500, detail=crud.get_error_message(text))
    return schemas.ImportResponse(
        detail="file uploaded successfully",
        status_code=201
    )
@app.post("/employees/import")
def importEmployees():
    pass

@app.get("/employee/possibleImportFields")
def getPossibleFields (db: Session = Depends(get_db)):
    return schemas.ImportPossibleFields(
        possible_fields=options,
    )
    
@app.post("/employees/test") # it was "/employees/csv"
async def upload(entry: schemas.MatchyUploadEntry, backgroundTask: BackgroundTasks, db: Session = Depends(get_db)):
    employees = entry.lines
    if not employees:
        raise HTTPException(status_code=400, detail='Nothing to do, empty file' )

    missing_mondatory_fields = set(mondatory_fields.keys()) - employees[0].keys() # Keys convert dict to python dict (a list)
    if missing_mondatory_fields:
        field_names = [display for field, display in missing_mondatory_fields.items()]        
        raise HTTPException(
            status_code=400, 
            detail= f"missing mondatory fields: {(', ').join(missing_mondatory_fields)}" # it was join (field_names)
        )
    return valid_employees_data_and_upload(employees, entry.forcedUpload, backgroundTask, db)

