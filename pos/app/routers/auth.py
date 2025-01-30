from app import enums, models
from app import schemas
from app.OAuth2 import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, authenticate_employee, get_password_hash
from app.crud.employee import add_reset_code, edit_reset_code, get_employee_by_email, get_confirmation_code, sudo_edit_employee, edit_confirmation_code, get_reset_code
from app.crud.error import add_error, get_error_message
from app.dependencies import dbDep, formaDataDep
from app.external_services import emailService
from app.schemas import Token
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta



app = APIRouter(
    tags=["Authentification"],
)

@app.post("/token",response_model=schemas.Token)
async def login_for_access_token(db: dbDep, form_data: formaDataDep):
    try:
        employee = authenticate_employee(db, form_data.username, form_data.password)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if employee.account_status == enums.accountStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email has not been verified yet",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"email": employee.email}, expires_delta=access_token_expires
        )
    except Exception as err:  #General error handling
        db.rollback()
        text = str(err)
        employee.add_error(text, db)
        raise HTTPException(status_code=500, detail=employee.get_error_message(text))
    
    return Token(access_token=access_token, token_type="bearer")

@app.patch("/confirmAccount", response_model=schemas.baseOut)
def confirm_account(confirAccountInput: schemas.confirmAccount, db:dbDep): #Depends means we have dependencies with database.
    try:    
        confirmation_code = get_confirmation_code(db, confirAccountInput.confirmation_code)
        if not confirmation_code:
            raise HTTPException(status_code=400, detail="Token Does not exist")
        if confirmation_code.status == enums.tokenStatus.USED:
            raise HTTPException(status_code=400, detail="Token is already used")
        diff = (datetime.now() - confirmation_code.created_on).seconds # time in seconds
        if diff > 3600:
            raise HTTPException(status_code=400, detail="token expired")
        
        sudo_edit_employee(confirmation_code.employee_id, {models.employee.account_status: enums.accountStatus.ACTIVE})
        edit_confirmation_code(confirmation_code.id, {models.accountActivation.status: enums.tokenStatus.USED})

        db.commit() #Save changes in the database
    except Exception as err:  #General error handling
        db.rollback()
        text = str(err)
        add_error(text, db)
        raise HTTPException(status_code=500, detail=get_error_message(text))
    
    return schemas.baseOut(
        detail="Account confirmed",
        status_code=status.HTTP_200_OK
    )

@app.patch("/forgotPassword", response_model=schemas.baseOut)
async def forgot_password(entry: schemas.ForgetPassword, db: dbDep):
    employee = get_employee_by_email(db, entry.email)
    if not employee:
        return schemas.BaseOut(
            message = 400,
            status = "Token Does not exist",
        )
    try: 
        reset_code = add_reset_code(db, employee)
        db.flush()
        await emailService.simple_send([employee.email], {
            "token": reset_code.token,
            "name": employee.first_name
            }, enums.EmailTemplate.ResetPassword,
        )
        db.commit()
    except Exception as err:  #General error handling
        db.rollback()
        text = str(err)
        add_error(text, db)
        raise HTTPException(status_code=500, detail=employee.get_error_message(text))
    
    return schemas.baseOut(
        message="Something went wrong",
        status=status.HTTP_200_OK
    )

@app.patch("/resetPassword", response_model=schemas.baseOut)
def confirm_account(entry: schemas.ResetPassword, db:dbDep): #Depends means we have dependencies with database.
    try:    
        reset_code = get_reset_code(db, entry.reset_code)
        if not reset_code:
            raise HTTPException(status_code=400, detail="Token Does not exist")
        
        if reset_code.status == enums.tokenStatus.USED:
            raise HTTPException(status_code=400, detail="Token is already used")
        diff = (datetime.now() - reset_code.created_on).seconds # time in seconds
        
        if diff > 3600:
            raise HTTPException(status_code=400, detail="token expired")
        
        if entry.psw != entry.confirm_psw:
            raise HTTPException(status_code=400, detail="password do not match")
        
        
        sudo_edit_employee(reset_code.employee_id, {models.employee.password: get_password_hash(entry.psw)})
        edit_reset_code(reset_code.id, {models.resetPassword.status: enums.tokenStatus.USED})

        db.commit() #Save changes in the database
    except Exception as err:  #General error handling
        db.rollback()
        text = str(err)
        add_error(text, db)
        raise HTTPException(status_code=500, detail=get_error_message(text))
    
    return schemas.baseOut(
        detail="Password changed",
        status_code=status.HTTP_200_OK
    )