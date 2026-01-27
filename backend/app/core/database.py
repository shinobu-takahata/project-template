from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# データベースが設定されている場合のみengineを作成
if settings.DATABASE_URL and settings.DATABASE_URL != "test":
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # データベースが未設定の場合はNoneを設定
    engine = None  # type: ignore
    SessionLocal = None  # type: ignore


class Base(DeclarativeBase):
    pass


def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database is not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
