"""
系统配置管理
============

管理整个应用的配置信息，包括数据库连接、Redis配置、
API密钥等敏感信息。支持从环境变量和配置文件加载。
"""

from typing import List, Optional
from pydantic import BaseSettings, validator
import os


class Settings(BaseSettings):
    """
    应用配置类
    
    使用Pydantic进行配置验证和类型检查
    """
    
    # 应用基础配置
    APP_NAME: str = "Web Crawler Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./web_crawler.db"  # 默认使用SQLite
    DATABASE_ECHO: bool = False  # 是否输出SQL日志
    
    # Redis配置 (用于Celery和缓存)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_DB: int = 1  # 缓存使用的Redis数据库
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Shanghai"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/web_crawler.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # 爬虫配置
    CRAWLER_MAX_CONCURRENT: int = 10  # 最大并发爬虫数
    CRAWLER_DELAY: float = 1.0  # 爬虫延迟(秒)
    CRAWLER_TIMEOUT: int = 30  # 请求超时时间(秒)
    CRAWLER_RETRY_TIMES: int = 3  # 重试次数
    CRAWLER_USER_AGENT: str = "Web-Crawler-Agent/1.0"
    
    # 智能体配置
    AGENT_MODEL_NAME: str = "gpt-3.5-turbo"  # 默认使用的LLM模型
    AGENT_MAX_TOKENS: int = 4096
    AGENT_TEMPERATURE: float = 0.7
    OPENAI_API_KEY: Optional[str] = None
    
    # 存储配置
    STORAGE_TYPE: str = "local"  # local, s3, oss等
    STORAGE_PATH: str = "./storage"  # 本地存储路径
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # API限流配置
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS允许的主机"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """验证数据库URL格式"""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        return v
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取配置实例
    
    Returns:
        Settings: 配置实例
    """
    return settings


# 环境检查函数
def is_development() -> bool:
    """检查是否为开发环境"""
    return settings.DEBUG


def is_production() -> bool:
    """检查是否为生产环境"""
    return not settings.DEBUG


# 创建必要的目录
def create_required_directories():
    """创建应用运行所需的目录"""
    directories = [
        "logs",
        "storage",
        "storage/uploads",
        "storage/cache",
        "storage/temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# 初始化时创建目录
create_required_directories() 