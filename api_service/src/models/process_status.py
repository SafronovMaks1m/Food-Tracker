from enum import Enum

class ProcessStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"