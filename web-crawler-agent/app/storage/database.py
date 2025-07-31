"""
数据库连接管理
==============

提供数据库连接和会话管理。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 创建基础模型类
Base = declarative_base()

# 数据库引擎
engine = None
async_engine = None

# 会话工厂
SessionLocal = None
AsyncSessionLocal = None


def init_database():
    """初始化数据库连接"""
    global engine, async_engine, SessionLocal, AsyncSessionLocal
    
    try:
        # 同步数据库引擎
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True
        )
        
        # 异步数据库引擎（如果使用异步驱动）
        if "postgresql" in settings.DATABASE_URL:
            async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            async_engine = create_async_engine(
                async_url,
                echo=settings.DATABASE_ECHO,
                pool_pre_ping=True
            )
            AsyncSessionLocal = async_sessionmaker(
                async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        
        # 会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        logger.info("数据库连接初始化成功")
        
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {str(e)}")
        raise


def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {str(e)}")
        raise


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncSession:
    """获取异步数据库会话"""
    if AsyncSessionLocal is None:
        raise RuntimeError("异步数据库会话未初始化")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库管理器"""
        if engine is None:
            init_database()
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()
    
    async def get_async_session(self) -> AsyncSession:
        """获取异步数据库会话"""
        if AsyncSessionLocal is None:
            raise RuntimeError("异步数据库会话未初始化")
        return AsyncSessionLocal()
    
    def close_connections(self):
        """关闭数据库连接"""
        try:
            if engine:
                engine.dispose()
            if async_engine:
                async_engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}")


# 初始化数据库
init_database() 