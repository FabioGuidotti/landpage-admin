from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class LandingBase(BaseModel):
    subdomain: str
    html_content: str
    whatsapp_number: Optional[str] = None
    whatsapp_message: Optional[str] = None
    pixel_meta: Optional[str] = None
    pixel_google: Optional[str] = None
    active: bool = True

class LandingCreate(LandingBase):
    pass

class LandingUpdate(BaseModel):
    subdomain: Optional[str] = None
    html_content: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_message: Optional[str] = None
    pixel_meta: Optional[str] = None
    pixel_google: Optional[str] = None
    active: Optional[bool] = None

class LandingResponse(LandingBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
