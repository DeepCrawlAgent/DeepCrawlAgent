"""
ORM模型
=======

定义数据库表结构的ORM模型。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.sql import func
from datetime import datetime

from .database import Base


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    priority = Column(String(20), default="normal")
    config = Column(JSON)
    target_urls = Column(JSON)
    created_time = Column(DateTime, default=func.now())
    started_time = Column(DateTime)
    completed_time = Column(DateTime)
    scheduled_time = Column(DateTime)
    tags = Column(JSON)
    result = Column(JSON)
    progress = Column(JSON)


class CrawlerResult(Base):
    """爬虫结果表"""
    __tablename__ = "crawler_results"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, index=True)
    url = Column(String(500), nullable=False)
    status_code = Column(Integer)
    content_type = Column(String(100))
    content_length = Column(Integer)
    title = Column(String(500))
    content = Column(Text)
    links = Column(JSON)
    images = Column(JSON)
    metadata = Column(JSON)
    extracted_data = Column(JSON)
    response_time = Column(Float)
    crawl_time = Column(DateTime, default=func.now())
    error_message = Column(Text)


class SearchHistory(Base):
    """搜索历史表"""
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True, index=True)
    query = Column(String(500), nullable=False)
    search_type = Column(String(50))
    results_count = Column(Integer)
    user_id = Column(String(100))
    session_id = Column(String(100))
    search_time = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    clicked_results = Column(JSON) 