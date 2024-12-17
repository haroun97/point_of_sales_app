from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, func
from ..database import Base
from datetime import datetime
from app.enums.tokenStatus import tokenStatus

class resetPassword(Base):
    __tablename__ = "reset_password"

    id = Column(Integer, primary_key=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, nullable=False)
    status = Column(Enum(tokenStatus), nullable=False)
    created_on = Column(DateTime, nullable=False, server_default=func.now())