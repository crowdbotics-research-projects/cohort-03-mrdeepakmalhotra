from sqlalchemy import create_engine, MetaData
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# from databases import Database

import models

DATABASE_URL = "postgresql+psycopg2://app_user:app_password@db/app"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async support
# database = Database(DATABASE_URL)

# MetaData and Base for model creation
metadata = MetaData()
Base = declarative_base(metadata=metadata)


# Dependency for getting the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_database():
    print("Creating tables")
    models.Base.metadata.create_all(bind=engine)