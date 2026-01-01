from enum import Enum


class AnonymizationLevel(Enum):
    BASIC = "basic"
    STRICT = "strict"
    CLINICAL = "clinical"