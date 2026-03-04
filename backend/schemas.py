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


# --- Tracking Schemas ---

class TrackingEventCreate(BaseModel):
    landing_id: int
    event_type: str  # 'pageview' or 'whatsapp_click'

class LandingStats(BaseModel):
    landing_id: int
    total_views: int = 0
    total_clicks: int = 0
    views_today: int = 0
    clicks_today: int = 0
    conversion_rate: float = 0.0  # clicks / views * 100

class OverviewStats(BaseModel):
    total_views: int = 0
    total_clicks: int = 0
    views_today: int = 0
    clicks_today: int = 0
    conversion_rate: float = 0.0

class LandingWithStats(LandingResponse):
    stats: Optional[LandingStats] = None

class DailyStats(BaseModel):
    date: str  # 'YYYY-MM-DD'
    views: int = 0
    clicks: int = 0


