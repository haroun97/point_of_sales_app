from sqlalchemy import Column, Integer, String, Enum, Date, DateTime, CheckConstraint, func
from sqlalchemy.orm import relationship
from ..database import Base
from app.enums import gender, accountStatus, contractType


class employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    number = Column(Integer, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(Integer, nullable=True)
    address = Column(String, nullable=True)
    gender = Column(Enum(gender), nullable=False)
    phonee_number = Column(Integer, nullable=True)
    account_status = Column(Enum(accountStatus),nullable=False, default=accountStatus.INACTIVE)
    birth_date = Column(Date, nullable=True)
    contract_type = Column(Enum(contractType), nullable=False)
    cnss_number = Column(String, nullable=True)
    created_on = Column(DateTime, nullable=False, server_default=func.now())

    role = relationship("")
    __table_args__ = (  
        CheckConstraint("(contract_type IN ('CDI', 'CDD') AND cnss_number IS NOT NULL AND cnss_number ~ '^\\d{8}-\\d{2}$') "
            "OR (contract_type IN ('APPRENTI', 'SIVP') AND (cnss_number IS NULL OR cnss_number ~ '^\\d{8}-\\d{2}$'))",
            name='ck_employees_cnss_number'
        ),
    )

