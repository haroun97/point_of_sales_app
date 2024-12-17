from enum import Enum
class basicEnum(str, Enum):
    @classmethod
    def getPossibleValues(cls):
        return [val.value for val in cls]
    def is_valid_enum_value(cls, field):
        for val in cls: 
            if field.strip().upper() == val.value.upper():
                return 
        return None 
