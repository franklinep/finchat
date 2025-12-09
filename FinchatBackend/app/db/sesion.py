from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import Settings
# import logging :p Investigar sobre logging si es necesario

settings = Settings()

engine = create_engine(settings.database_url, future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
