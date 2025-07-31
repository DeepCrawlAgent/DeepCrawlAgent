"""
爬虫数据模型
============

定义爬虫相关的数据结构，包括请求、响应、配置等模型。
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl
import uuid


class CrawlerStatus(str, Enum):
    """爬虫状态枚举"""
    PENDING = "pending"       # 待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"      # 超时


class CrawlerMethod(str, Enum):
    """爬虫方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class ContentType(str, Enum):
    """内容类型枚举"""
    HTML = "html"
    JSON = "json"
    TEXT = "text"
    XML = "xml"
    PDF = "pdf"
    IMAGE = "image"


class CrawlerConfig(BaseModel):
    """爬虫配置模型"""
    user_agent: str = Field(
        default="Web-Crawler-Agent/1.0",
        description="用户代理"
    )
    timeout: int = Field(default=30, gt=0, le=300, description="超时时间(秒)")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    retry_delay: float = Field(default=1.0, ge=0, description="重试延迟(秒)")
    delay_between_requests: float = Field(default=1.0, ge=0, description="请求间延迟(秒)")
    max_redirects: int = Field(default=5, ge=0, le=20, description="最大重定向次数")
    verify_ssl: bool = Field(default=True, description="是否验证SSL证书")
    follow_robots: bool = Field(default=True, description="是否遵循robots.txt")
    max_page_size: int = Field(default=10*1024*1024, gt=0, description="最大页面大小(字节)")
    enable_javascript: bool = Field(default=False, description="是否启用JavaScript")
    proxy: Optional[str] = Field(default=None, description="代理设置")
    custom_headers: Optional[Dict[str, str]] = Field(default=None, description="自定义请求头")
    cookies: Optional[Dict[str, str]] = Field(default=None, description="Cookies")
    
    @validator("proxy")
    def validate_proxy(cls, v):
        """验证代理格式"""
        if v and not v.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            raise ValueError("代理格式无效")
        return v


class CrawlerRequest(BaseModel):
    """爬虫请求模型"""
    url: HttpUrl = Field(..., description="目标URL")
    method: CrawlerMethod = Field(default=CrawlerMethod.GET, description="请求方法")
    headers: Optional[Dict[str, str]] = Field(default=None, description="请求头")
    params: Optional[Dict[str, Any]] = Field(default=None, description="URL参数")
    data: Optional[Dict[str, Any]] = Field(default=None, description="POST数据")
    config: Optional[CrawlerConfig] = Field(default=None, description="爬虫配置")
    extract_rules: Optional[Dict[str, str]] = Field(default=None, description="内容提取规则")
    save_format: str = Field(default="json", description="保存格式")
    async_mode: bool = Field(default=True, description="是否异步执行")
    callback_url: Optional[HttpUrl] = Field(default=None, description="回调URL")
    
    @validator("extract_rules")
    def validate_extract_rules(cls, v):
        """验证提取规则"""
        if v:
            allowed_keys = ["title", "content", "links", "images", "custom"]
            for key in v.keys():
                if key not in allowed_keys:
                    raise ValueError(f"不支持的提取规则: {key}")
        return v


class BatchCrawlerRequest(BaseModel):
    """批量爬虫请求模型"""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=100, description="URL列表")
    method: CrawlerMethod = Field(default=CrawlerMethod.GET, description="请求方法")
    config: Optional[CrawlerConfig] = Field(default=None, description="爬虫配置")
    extract_rules: Optional[Dict[str, str]] = Field(default=None, description="内容提取规则")
    save_format: str = Field(default="json", description="保存格式")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="最大并发数")
    callback_url: Optional[HttpUrl] = Field(default=None, description="回调URL")
    
    @validator("urls")
    def validate_urls(cls, v):
        """验证URL列表"""
        if len(set(v)) != len(v):
            raise ValueError("URL列表中存在重复项")
        return v


class CrawlerResult(BaseModel):
    """爬虫结果模型"""
    url: str = Field(..., description="爬取的URL")
    status_code: int = Field(..., description="HTTP状态码")
    content_type: str = Field(..., description="内容类型")
    content_length: int = Field(..., description="内容长度")
    title: Optional[str] = Field(None, description="页面标题")
    content: Optional[str] = Field(None, description="页面内容")
    links: Optional[List[str]] = Field(None, description="页面链接")
    images: Optional[List[str]] = Field(None, description="页面图片")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="提取的数据")
    response_time: float = Field(..., description="响应时间(秒)")
    crawl_time: datetime = Field(..., description="爬取时间")
    error_message: Optional[str] = Field(None, description="错误消息")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CrawlerResponse(BaseModel):
    """爬虫响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: CrawlerStatus = Field(..., description="爬虫状态")
    message: str = Field(..., description="响应消息")
    url: Optional[str] = Field(None, description="爬取的URL")
    result: Optional[CrawlerResult] = Field(None, description="爬虫结果")
    progress: Optional[Dict[str, Any]] = Field(None, description="进度信息")
    created_time: datetime = Field(..., description="创建时间")
    started_time: Optional[datetime] = Field(None, description="开始时间")
    completed_time: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchCrawlerResponse(BaseModel):
    """批量爬虫响应模型"""
    batch_task_id: str = Field(..., description="批量任务ID")
    status: CrawlerStatus = Field(..., description="批量任务状态")
    total_urls: int = Field(..., description="总URL数量")
    completed_urls: int = Field(default=0, description="已完成URL数量")
    failed_urls: int = Field(default=0, description="失败URL数量")
    results: List[CrawlerResult] = Field(default_factory=list, description="爬虫结果列表")
    progress_percentage: float = Field(default=0.0, description="完成百分比")
    estimated_time_remaining: Optional[float] = Field(None, description="预计剩余时间(秒)")
    created_time: datetime = Field(..., description="创建时间")
    started_time: Optional[datetime] = Field(None, description="开始时间")
    completed_time: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CrawlerStatistics(BaseModel):
    """爬虫统计模型"""
    total_requests: int = Field(default=0, description="总请求数")
    successful_requests: int = Field(default=0, description="成功请求数")
    failed_requests: int = Field(default=0, description="失败请求数")
    average_response_time: float = Field(default=0.0, description="平均响应时间")
    total_data_crawled: int = Field(default=0, description="爬取数据总量(字节)")
    requests_per_hour: float = Field(default=0.0, description="每小时请求数")
    success_rate: float = Field(default=0.0, description="成功率")
    most_crawled_domains: List[Dict[str, Any]] = Field(default_factory=list, description="最多爬取的域名")
    error_breakdown: Dict[str, int] = Field(default_factory=dict, description="错误分类统计")
    daily_stats: List[Dict[str, Any]] = Field(default_factory=list, description="每日统计")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True 