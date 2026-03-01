from sqlalchemy.orm import Session
import models, schemas

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
