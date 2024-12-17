from sqlalchemy import Column, Integer, ForeignKey, String, Enum
from ..database import Base
from app.enums import roleType

class employeeRole(Base):
    __tablename__ = "employee_roles"

    id = Column(Integer, primary_key=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    role = Column(Enum(roleType), nullable=False)