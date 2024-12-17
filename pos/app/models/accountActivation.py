from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Enum, func
from ..database import Base
from datetime import datetime
from app.enums import tokenStatus

class accountActivation(Base):
    __tablename__ = "account_activation"

    id = Column(Integer, primary_key=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, nullable=False)
    status = Column(Enum(tokenStatus), nullable=False)
    created_on = Column(DateTime, nullable=False, server_default=func.now())