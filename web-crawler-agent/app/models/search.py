"""
搜索数据模型
============

定义搜索相关的数据结构，包括搜索请求、响应、结果等模型。
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class SearchType(str, Enum):
    """搜索类型枚举"""
    INTELLIGENT = "intelligent"    # 智能搜索
    SEMANTIC = "semantic"         # 语义搜索
    KEYWORD = "keyword"           # 关键词搜索
    FUZZY = "fuzzy"              # 模糊搜索


class SearchSort(str, Enum):
    """搜索排序枚举"""
    RELEVANCE = "relevance"      # 相关性
    DATE = "date"               # 日期
    POPULARITY = "popularity"    # 热门度
    QUALITY = "quality"         # 质量


class SearchFilter(BaseModel):
    """搜索过滤模型"""
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围过滤")
    domain: Optional[List[str]] = Field(None, description="域名过滤")
    language: Optional[str] = Field(None, description="语言过滤")
    content_type: Optional[List[str]] = Field(None, description="内容类型过滤")
    min_length: Optional[int] = Field(None, ge=0, description="最小内容长度")
    max_length: Optional[int] = Field(None, gt=0, description="最大内容长度")
    exclude_keywords: Optional[List[str]] = Field(None, description="排除关键词")
    
    @validator("date_range")
    def validate_date_range(cls, v):
        """验证日期范围"""
        if v:
            required_keys = ["start_date", "end_date"]
            for key in required_keys:
                if key not in v:
                    raise ValueError(f"日期范围缺少必需字段: {key}")
        return v


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    search_type: SearchType = Field(default=SearchType.INTELLIGENT, description="搜索类型")
    max_results: int = Field(default=10, ge=1, le=100, description="最大结果数")
    offset: int = Field(default=0, ge=0, description="结果偏移量")
    sort_by: SearchSort = Field(default=SearchSort.RELEVANCE, description="排序方式")
    filters: Optional[SearchFilter] = Field(None, description="搜索过滤条件")
    enable_summary: bool = Field(default=True, description="是否生成摘要")
    include_snippets: bool = Field(default=True, description="是否包含内容片段")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    
    @validator("query")
    def validate_query(cls, v):
        """验证搜索查询"""
        if not v.strip():
            raise ValueError("搜索查询不能为空")
        return v.strip()


class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str = Field(..., description="结果ID")
    title: str = Field(..., description="标题")
    url: str = Field(..., description="URL")
    snippet: Optional[str] = Field(None, description="内容片段")
    content: Optional[str] = Field(None, description="完整内容")
    summary: Optional[str] = Field(None, description="内容摘要")
    relevance_score: float = Field(..., ge=0, le=1, description="相关性评分")
    quality_score: float = Field(..., ge=0, le=1, description="质量评分")
    popularity_score: float = Field(..., ge=0, le=1, description="热门度评分")
    domain: str = Field(..., description="域名")
    language: Optional[str] = Field(None, description="语言")
    content_type: str = Field(..., description="内容类型")
    content_length: int = Field(..., ge=0, description="内容长度")
    published_date: Optional[datetime] = Field(None, description="发布日期")
    crawled_date: datetime = Field(..., description="爬取日期")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="实体识别结果")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    search_time: float = Field(..., description="搜索用时(秒)")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str = Field(..., description="搜索查询")
    search_type: SearchType = Field(..., description="搜索类型")
    results: List[SearchResult] = Field(..., description="搜索结果")
    total: int = Field(..., ge=0, description="总结果数")
    offset: int = Field(..., ge=0, description="结果偏移量")
    limit: int = Field(..., ge=1, description="结果限制数")
    search_time: float = Field(..., description="搜索总用时(秒)")
    suggestions: Optional[List[str]] = Field(None, description="搜索建议")
    related_queries: Optional[List[str]] = Field(None, description="相关查询")
    filters_applied: Optional[SearchFilter] = Field(None, description="应用的过滤条件")
    search_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="搜索ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="搜索时间戳")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchSuggestion(BaseModel):
    """搜索建议模型"""
    text: str = Field(..., description="建议文本")
    score: float = Field(..., ge=0, le=1, description="建议评分")
    type: str = Field(..., description="建议类型")
    source: str = Field(..., description="建议来源")


class SearchHistory(BaseModel):
    """搜索历史模型"""
    id: str = Field(..., description="历史记录ID")
    query: str = Field(..., description="搜索查询")
    search_type: SearchType = Field(..., description="搜索类型")
    results_count: int = Field(..., ge=0, description="结果数量")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    search_time: float = Field(..., description="搜索用时")
    timestamp: datetime = Field(..., description="搜索时间")
    clicked_results: List[str] = Field(default_factory=list, description="点击的结果ID")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchFeedback(BaseModel):
    """搜索反馈模型"""
    search_id: str = Field(..., description="搜索ID")
    result_id: str = Field(..., description="结果ID")
    feedback_type: str = Field(..., description="反馈类型")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    comment: Optional[str] = Field(None, max_length=500, description="评论")
    user_id: Optional[str] = Field(None, description="用户ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="反馈时间")
    
    @validator("feedback_type")
    def validate_feedback_type(cls, v):
        """验证反馈类型"""
        allowed_types = ["helpful", "not_helpful", "spam", "irrelevant", "outdated"]
        if v not in allowed_types:
            raise ValueError(f"无效的反馈类型: {v}")
        return v
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TrendingSearch(BaseModel):
    """热门搜索模型"""
    query: str = Field(..., description="搜索查询")
    search_count: int = Field(..., ge=0, description="搜索次数")
    trend_score: float = Field(..., ge=0, description="趋势评分")
    growth_rate: float = Field(..., description="增长率")
    category: Optional[str] = Field(None, description="分类")
    time_range: str = Field(..., description="时间范围")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True


class SearchAnalytics(BaseModel):
    """搜索分析模型"""
    total_searches: int = Field(default=0, description="总搜索数")
    unique_queries: int = Field(default=0, description="唯一查询数")
    average_results_per_query: float = Field(default=0.0, description="平均每查询结果数")
    average_search_time: float = Field(default=0.0, description="平均搜索时间")
    most_popular_queries: List[TrendingSearch] = Field(default_factory=list, description="最热门查询")
    search_patterns: Dict[str, Any] = Field(default_factory=dict, description="搜索模式")
    user_behavior: Dict[str, Any] = Field(default_factory=dict, description="用户行为")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="性能指标")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True 