from pathlib import Path
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

from app.enums.emailTemplate import EmailTemplate
from ..config import settings

conf = ConnectionConfig(
    MAIL_USERNAME = settings.mail_username,
    MAIL_PASSWORD = settings.mail_password,
    MAIL_FROM = settings.mail_from,
    MAIL_PORT = 465,
    MAIL_SERVER = settings.mail_server,
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER= Path(__file__).parent / 'templates'
)

template_name_per_template = {
    EmailTemplate.ConfirmAccount: "account_activation.html",
    EmailTemplate.ResetPassword: "reset_password.html"
}
async def simple_send(emails: list[EmailStr], body: dict, template:EmailTemplate):
    try:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            recipients=emails,
            template_body=body,
            subtype=MessageType.html)

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name_per_template[template])
    except FileNotFoundError as file_err:
        # Handle missing template file errors
        print("Template File Error:", file_err)
        raise HTTPException(
            status_code=500,
            detail="Email template not found. Please contact support."
        )
    except ValueError as value_err:
        # Handle issues with email recipients or invalid data
        print("Value Error:", value_err)
        raise HTTPException(
            status_code=400,
            detail="Invalid input provided for email or template. Check the email addresses and content."
        )
    except Exception as general_err:
        # Handle all other unexpected exceptions
        print("Unexpected Error:", general_err)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while sending the email."
        )
    return JSONResponse(status_code=200, content={"message": "email has been sent"})
