#!/usr/bin/env python3
"""
サンプルバッチスクリプト

データベースにアクセスし、サンプルデータの集計・保存を行います。
Step Functionsから定期的に実行されることを想定しています。

Usage:
    python batch/sample_batch.py
"""
import sys
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# 既存のアプリケーションコードを再利用
from app.core.database import SessionLocal
from app.core.config import settings

# ログ設定（標準出力に出力 → CloudWatch Logsに転送）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def get_db_session():
    """データベースセッションを取得"""
    if SessionLocal is None:
        raise RuntimeError("Database is not configured. Check DATABASE_URL.")
    return SessionLocal()


def sample_select_query(db) -> int:
    """
    サンプル: データ参照（SELECT）

    実際のユースケースに合わせて実装してください。
    例: 特定条件のレコード数をカウント
    """
    logger.info("Executing SELECT query...")

    # サンプル: テーブル一覧を取得（PostgreSQL）
    result = db.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
    )
    tables = result.fetchall()
    table_count = len(tables)

    logger.info(f"Found {table_count} tables in public schema")
    for table in tables:
        logger.info(f"  - {table[0]}")

    return table_count


def sample_insert_query(db, data: dict) -> None:
    """
    サンプル: データ登録（INSERT/UPDATE）

    実際のユースケースに合わせて実装してください。
    例: 集計結果をログテーブルに保存

    注意: このサンプルでは実際のINSERTは行いません。
    実装時は適切なテーブルとモデルを使用してください。
    """
    logger.info("Executing INSERT/UPDATE query...")
    logger.info(f"Data to insert: {data}")

    # 実際の実装例（コメントアウト）:
    # from app.domain.models import BatchLog
    # batch_log = BatchLog(
    #     execution_time=data["execution_time"],
    #     table_count=data["table_count"],
    #     status="completed",
    #     created_at=datetime.now(timezone.utc)
    # )
    # db.add(batch_log)
    # db.commit()
    # logger.info(f"Inserted batch log with id: {batch_log.id}")

    logger.info("INSERT/UPDATE completed (sample - no actual data written)")


def main() -> int:
    """
    メイン処理

    Returns:
        int: 終了コード (0: 成功, 1: 失敗)
    """
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 50)
    logger.info("Batch execution started")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Start time: {start_time.isoformat()}")
    logger.info("=" * 50)

    db = None
    try:
        # データベースセッション取得
        logger.info("Connecting to database...")
        db = get_db_session()
        logger.info("Database connection established")

        # サンプル処理1: データ参照
        table_count = sample_select_query(db)

        # サンプル処理2: データ登録
        sample_insert_query(
            db,
            {
                "execution_time": start_time.isoformat(),
                "table_count": table_count,
            },
        )

        # 処理完了
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 50)
        logger.info("Batch execution completed successfully")
        logger.info(f"End time: {end_time.isoformat()}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("=" * 50)

        return 0

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"Batch execution failed: {str(e)}", exc_info=True)
        return 1
    finally:
        if db:
            db.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
