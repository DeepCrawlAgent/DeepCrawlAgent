"""
自定义异常处理
==============

定义系统中使用的各种自定义异常类，
提供统一的错误处理机制。
"""

from typing import Any, Dict, Optional


class CustomException(Exception):
    """
    自定义基础异常类
    
    所有业务异常都应该继承这个类
    """
    
    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        extra_data: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.extra_data = extra_data or {}
        super().__init__(self.detail)


class ValidationException(CustomException):
    """数据验证异常"""
    
    def __init__(self, detail: str, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=422,
            error_code="VALIDATION_ERROR",
            extra_data=extra_data
        )


class NotFoundException(CustomException):
    """资源未找到异常"""
    
    def __init__(self, detail: str = "资源未找到", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=404,
            error_code="NOT_FOUND",
            extra_data=extra_data
        )


class UnauthorizedException(CustomException):
    """未授权异常"""
    
    def __init__(self, detail: str = "未授权访问", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=401,
            error_code="UNAUTHORIZED",
            extra_data=extra_data
        )


class ForbiddenException(CustomException):
    """禁止访问异常"""
    
    def __init__(self, detail: str = "禁止访问", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=403,
            error_code="FORBIDDEN",
            extra_data=extra_data
        )


class RateLimitException(CustomException):
    """限流异常"""
    
    def __init__(self, detail: str = "请求过于频繁", extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            extra_data=extra_data
        )


class CrawlerException(CustomException):
    """爬虫相关异常"""
    
    def __init__(self, detail: str, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="CRAWLER_ERROR",
            extra_data=extra_data
        )


class AgentException(CustomException):
    """智能体相关异常"""
    
    def __init__(self, detail: str, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="AGENT_ERROR",
            extra_data=extra_data
        )


class StorageException(CustomException):
    """存储相关异常"""
    
    def __init__(self, detail: str, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="STORAGE_ERROR",
            extra_data=extra_data
        )


class TaskException(CustomException):
    """任务相关异常"""
    
    def __init__(self, detail: str, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="TASK_ERROR",
            extra_data=extra_data
        )


class DatabaseException(CustomException):
    """数据库相关异常"""
    
    def __init__(self, detail: str, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=500,
            error_code="DATABASE_ERROR",
            extra_data=extra_data
        ) 