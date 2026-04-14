import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from models import Base

# 确保 SQLite 数据库目录存在（Docker 挂载卷场景）
db_url = config.DATABASE_URL
if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "")
    os.makedirs(Path(db_path).parent, exist_ok=True)

engine = create_engine(db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """创建所有表。"""
    Base.metadata.create_all(engine)


def get_db():
    """FastAPI 依赖注入用的数据库会话生成器。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
