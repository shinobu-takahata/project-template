import json
import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings


# JSON形式のカスタムフォーマッター
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 例外情報がある場合は追加
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


# ロギング設定
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler],
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# グローバル例外ハンドラー（すべての例外をログに記録）
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """すべての例外をキャッチしてJSON形式でログに記録"""
    logger = logging.getLogger(__name__)

    # 例外情報をログに記録（exc_infoを渡すことでスタックトレースも記録される）
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
        }
    )

    # クライアントには汎用的なエラーレスポンスを返す
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_type": exc.__class__.__name__,
        }
    )


# CORS設定（開発環境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(api_router, prefix=settings.API_V1_STR)
