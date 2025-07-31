"""
任务数据模型
============

定义任务相关的数据结构，包括任务创建、更新、响应等模型。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"        # 待执行
    RUNNING = "running"        # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消
    PAUSED = "paused"         # 已暂停


class TaskType(str, Enum):
    """任务类型枚举"""
    CRAWLER = "crawler"       # 爬虫任务
    AGENT = "agent"          # 智能体任务
    SEARCH = "search"        # 搜索任务
    BATCH = "batch"          # 批量任务


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"              # 低优先级
    NORMAL = "normal"        # 普通优先级
    HIGH = "high"           # 高优先级
    URGENT = "urgent"       # 紧急


class TaskConfig(BaseModel):
    """任务配置模型"""
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    timeout: int = Field(default=300, gt=0, description="超时时间(秒)")
    concurrent_limit: int = Field(default=1, ge=1, description="并发限制")
    enable_cache: bool = Field(default=True, description="是否启用缓存")
    custom_headers: Optional[Dict[str, str]] = Field(default=None, description="自定义请求头")
    proxy: Optional[str] = Field(default=None, description="代理设置")
    extra_params: Optional[Dict[str, Any]] = Field(default=None, description="额外参数")


class TaskCreate(BaseModel):
    """创建任务模型"""
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(default=None, max_length=1000, description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="任务优先级")
    config: TaskConfig = Field(default_factory=TaskConfig, description="任务配置")
    target_urls: Optional[List[str]] = Field(default=None, description="目标URL列表")
    scheduled_time: Optional[datetime] = Field(default=None, description="计划执行时间")
    auto_start: bool = Field(default=False, description="是否自动开始")
    tags: Optional[List[str]] = Field(default=None, description="任务标签")
    
    @validator("target_urls")
    def validate_urls(cls, v):
        """验证URL格式"""
        if v:
            for url in v:
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f"无效的URL格式: {url}")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        """验证标签"""
        if v and len(v) > 10:
            raise ValueError("标签数量不能超过10个")
        return v


class TaskUpdate(BaseModel):
    """更新任务模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级")
    config: Optional[TaskConfig] = Field(None, description="任务配置")
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间")
    tags: Optional[List[str]] = Field(None, description="任务标签")
    
    @validator("tags")
    def validate_tags(cls, v):
        """验证标签"""
        if v and len(v) > 10:
            raise ValueError("标签数量不能超过10个")
        return v


class TaskProgress(BaseModel):
    """任务进度模型"""
    current: int = Field(default=0, ge=0, description="当前进度")
    total: int = Field(default=0, ge=0, description="总数")
    percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="完成百分比")
    message: Optional[str] = Field(default=None, description="进度消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")


class TaskResult(BaseModel):
    """任务结果模型"""
    success_count: int = Field(default=0, ge=0, description="成功数量")
    failure_count: int = Field(default=0, ge=0, description="失败数量")
    total_count: int = Field(default=0, ge=0, description="总数量")
    data: Optional[List[Dict[str, Any]]] = Field(default=None, description="结果数据")
    error_messages: Optional[List[str]] = Field(default=None, description="错误消息")
    execution_time: Optional[float] = Field(default=None, description="执行时间(秒)")
    output_files: Optional[List[str]] = Field(default=None, description="输出文件路径")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: str = Field(..., description="任务ID")
    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    status: TaskStatus = Field(..., description="任务状态")
    priority: TaskPriority = Field(..., description="任务优先级")
    config: TaskConfig = Field(..., description="任务配置")
    progress: Optional[TaskProgress] = Field(None, description="任务进度")
    result: Optional[TaskResult] = Field(None, description="任务结果")
    target_urls: Optional[List[str]] = Field(None, description="目标URL列表")
    created_time: datetime = Field(..., description="创建时间")
    started_time: Optional[datetime] = Field(None, description="开始时间")
    completed_time: Optional[datetime] = Field(None, description="完成时间")
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间")
    tags: Optional[List[str]] = Field(None, description="任务标签")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: List[TaskResponse] = Field(..., description="任务列表")
    total: int = Field(..., ge=0, description="总数量")
    skip: int = Field(..., ge=0, description="跳过数量")
    limit: int = Field(..., ge=1, description="限制数量")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True


class TaskLog(BaseModel):
    """任务日志模型"""
    task_id: str = Field(..., description="任务ID")
    timestamp: datetime = Field(..., description="时间戳")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 