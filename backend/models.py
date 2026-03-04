from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
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


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    landing_id = Column(Integer, ForeignKey("landings.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(20), nullable=False)  # 'pageview' or 'whatsapp_click'
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    referer = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_tracking_landing_type_date', 'landing_id', 'event_type', 'created_at'),
    )

