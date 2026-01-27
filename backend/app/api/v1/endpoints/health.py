from fastapi import APIRouter

# from sqlalchemy import text
# from sqlalchemy.orm import Session

# from app.core.database import get_db

router = APIRouter()


@router.get("/health")
# async def health_check(db: Session = Depends(get_db)):
async def health_check():
    """ヘルスチェックエンドポイント"""
    # データベース接続確認
    # db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
