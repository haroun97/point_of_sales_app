
from fastapi import HTTPException
from app import models


def get_error_message(error_message, error_keys):
    for error_key in error_keys:
        if error_key in error_message:
            return error_keys[error_key]
    return "Something went wrong"

def add_error(text, db):
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