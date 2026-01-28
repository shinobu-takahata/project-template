import os
from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.database import Base
from app.infrastructure.database.models import *  # noqa: F401, F403

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

# 環境変数からデータベースURLを構築（ECS環境用）
def get_database_url():
    """環境変数からデータベースURLを構築"""
    db_user = os.getenv("DATABASE_USER")
    db_password = os.getenv("DATABASE_PASSWORD")
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_name = os.getenv("DATABASE_NAME", "postgres")

    if db_user and db_password and db_host:
        # パスワードに特殊文字が含まれる場合にURLエンコード
        encoded_password = quote_plus(db_password)
        return f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"

    # 環境変数がない場合はalembic.iniの設定を使用（ローカル開発用）
    return config.get_main_option("sqlalchemy.url")

# 環境変数が設定されている場合、alembic.iniの設定を上書き
database_url = get_database_url()
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
