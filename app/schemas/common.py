from pydantic import BaseModel
from typing import Optional

class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
