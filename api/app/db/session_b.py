from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine_b = create_engine(
    settings.effective_database_b_url,
    connect_args={"client_encoding": "utf8"},
)
SessionLocalB = sessionmaker(autocommit=False, autoflush=False, bind=engine_b)


class BaseB(DeclarativeBase):
    pass


def get_db_b():
    db = SessionLocalB()
    try:
        yield db
    finally:
        db.close()
