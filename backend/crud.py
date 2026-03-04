from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import datetime, date, timezone
import models, schemas


# --- Landing CRUD ---

def get_landing(db: Session, landing_id: int):
    return db.query(models.Landing).filter(models.Landing.id == landing_id).first()

def get_landing_by_subdomain(db: Session, subdomain: str):
    return db.query(models.Landing).filter(models.Landing.subdomain == subdomain).first()

def get_landings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Landing).offset(skip).limit(limit).all()

def create_landing(db: Session, landing: schemas.LandingCreate):
    db_landing = models.Landing(**landing.model_dump())
    db.add(db_landing)
    db.commit()
    db.refresh(db_landing)
    return db_landing

def update_landing(db: Session, landing_id: int, landing: schemas.LandingUpdate):
    db_landing = db.query(models.Landing).filter(models.Landing.id == landing_id).first()
    if db_landing:
        update_data = landing.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_landing, key, value)
        db.commit()
        db.refresh(db_landing)
    return db_landing

def delete_landing(db: Session, landing_id: int):
    db_landing = db.query(models.Landing).filter(models.Landing.id == landing_id).first()
    if db_landing:
        db.delete(db_landing)
        db.commit()
    return db_landing


# --- Tracking CRUD ---

def create_tracking_event(db: Session, landing_id: int, event_type: str, ip_address: str = None, user_agent: str = None, referer: str = None):
    event = models.TrackingEvent(
        landing_id=landing_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent[:512] if user_agent else None,
        referer=referer[:1024] if referer else None,
    )
    db.add(event)
    db.commit()
    return event


def get_landing_stats(db: Session, landing_id: int) -> schemas.LandingStats:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Total counts
    total_views = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.landing_id == landing_id,
        models.TrackingEvent.event_type == "pageview"
    ).scalar() or 0

    total_clicks = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.landing_id == landing_id,
        models.TrackingEvent.event_type == "whatsapp_click"
    ).scalar() or 0

    # Today counts
    views_today = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.landing_id == landing_id,
        models.TrackingEvent.event_type == "pageview",
        models.TrackingEvent.created_at >= today_start
    ).scalar() or 0

    clicks_today = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.landing_id == landing_id,
        models.TrackingEvent.event_type == "whatsapp_click",
        models.TrackingEvent.created_at >= today_start
    ).scalar() or 0

    conversion_rate = (total_clicks / total_views * 100) if total_views > 0 else 0.0

    return schemas.LandingStats(
        landing_id=landing_id,
        total_views=total_views,
        total_clicks=total_clicks,
        views_today=views_today,
        clicks_today=clicks_today,
        conversion_rate=round(conversion_rate, 1)
    )


def get_all_stats(db: Session) -> dict:
    """Get stats for all landings in a single batch."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Get all counts grouped by landing_id and event_type
    total_counts = db.query(
        models.TrackingEvent.landing_id,
        models.TrackingEvent.event_type,
        sql_func.count(models.TrackingEvent.id)
    ).group_by(
        models.TrackingEvent.landing_id,
        models.TrackingEvent.event_type
    ).all()

    today_counts = db.query(
        models.TrackingEvent.landing_id,
        models.TrackingEvent.event_type,
        sql_func.count(models.TrackingEvent.id)
    ).filter(
        models.TrackingEvent.created_at >= today_start
    ).group_by(
        models.TrackingEvent.landing_id,
        models.TrackingEvent.event_type
    ).all()

    # Build stats dict keyed by landing_id
    stats = {}
    for landing_id, event_type, count in total_counts:
        if landing_id not in stats:
            stats[landing_id] = {"total_views": 0, "total_clicks": 0, "views_today": 0, "clicks_today": 0}
        if event_type == "pageview":
            stats[landing_id]["total_views"] = count
        elif event_type == "whatsapp_click":
            stats[landing_id]["total_clicks"] = count

    for landing_id, event_type, count in today_counts:
        if landing_id not in stats:
            stats[landing_id] = {"total_views": 0, "total_clicks": 0, "views_today": 0, "clicks_today": 0}
        if event_type == "pageview":
            stats[landing_id]["views_today"] = count
        elif event_type == "whatsapp_click":
            stats[landing_id]["clicks_today"] = count

    # Calculate conversion rates
    result = {}
    for lid, s in stats.items():
        conv = (s["total_clicks"] / s["total_views"] * 100) if s["total_views"] > 0 else 0.0
        result[lid] = schemas.LandingStats(
            landing_id=lid,
            total_views=s["total_views"],
            total_clicks=s["total_clicks"],
            views_today=s["views_today"],
            clicks_today=s["clicks_today"],
            conversion_rate=round(conv, 1)
        )
    return result


def get_overview_stats(db: Session) -> schemas.OverviewStats:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_views = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.event_type == "pageview"
    ).scalar() or 0

    total_clicks = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.event_type == "whatsapp_click"
    ).scalar() or 0

    views_today = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.event_type == "pageview",
        models.TrackingEvent.created_at >= today_start
    ).scalar() or 0

    clicks_today = db.query(sql_func.count(models.TrackingEvent.id)).filter(
        models.TrackingEvent.event_type == "whatsapp_click",
        models.TrackingEvent.created_at >= today_start
    ).scalar() or 0

    conversion_rate = (total_clicks / total_views * 100) if total_views > 0 else 0.0

    return schemas.OverviewStats(
        total_views=total_views,
        total_clicks=total_clicks,
        views_today=views_today,
        clicks_today=clicks_today,
        conversion_rate=round(conversion_rate, 1)
    )


def get_daily_stats(db: Session, days: int = 7, landing_id: int = None) -> list:
    """Get daily stats for the last N days, optionally filtered by landing_id."""
    from datetime import timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    query = db.query(
        sql_func.date(models.TrackingEvent.created_at).label("day"),
        models.TrackingEvent.event_type,
        sql_func.count(models.TrackingEvent.id)
    ).filter(
        sql_func.date(models.TrackingEvent.created_at) >= start_date
    )

    if landing_id:
        query = query.filter(models.TrackingEvent.landing_id == landing_id)

    rows = query.group_by("day", models.TrackingEvent.event_type).all()

    # Build lookup
    data = {}
    for day, event_type, count in rows:
        day_str = str(day)
        if day_str not in data:
            data[day_str] = {"views": 0, "clicks": 0}
        if event_type == "pageview":
            data[day_str]["views"] = count
        elif event_type == "whatsapp_click":
            data[day_str]["clicks"] = count

    # Fill all days in range (no gaps)
    result = []
    current = start_date
    while current <= end_date:
        day_str = current.isoformat()
        d = data.get(day_str, {"views": 0, "clicks": 0})
        result.append(schemas.DailyStats(date=day_str, views=d["views"], clicks=d["clicks"]))
        current += timedelta(days=1)

    return result

