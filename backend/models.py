from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class Landing(Base):
    __tablename__ = "landings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True) # Optional for now
    subdomain = Column(String, unique=True, index=True, nullable=False)
    html_content = Column(Text, nullable=False)
    whatsapp_number = Column(String, nullable=True)
    whatsapp_message = Column(Text, nullable=True)
    pixel_meta = Column(Text, nullable=True)
    pixel_google = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
