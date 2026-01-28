import logging

from fastapi import APIRouter

# from sqlalchemy import text
# from sqlalchemy.orm import Session

# from app.core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
# async def health_check(db: Session = Depends(get_db)):
async def health_check():
    """ヘルスチェックエンドポイント"""
    # データベース接続確認
    # db.execute(text("SELECT 1"))
    logger.debug("Performing health check database query")
    logger.info("Health check endpoint called")
    logger.error("This is a test error log for health check")
    return {"status": "healthy-2", "database": "connected"}
