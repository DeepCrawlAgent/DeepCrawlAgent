"""
辅助函数
========

提供通用的辅助函数。
"""

import uuid
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse


class HelperUtils:
    """辅助工具类"""
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def current_timestamp() -> datetime:
        """获取当前时间戳"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        格式化日期时间
        
        Args:
            dt: 日期时间对象
            format_str: 格式字符串
            
        Returns:
            str: 格式化后的字符串
        """
        return dt.strftime(format_str)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理字典中的None值
        
        Args:
            data: 原始字典
            
        Returns:
            Dict[str, Any]: 清理后的字典
        """
        return {k: v for k, v in data.items() if v is not None}
    
    @staticmethod
    def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        截断字符串
        
        Args:
            text: 原始字符串
            max_length: 最大长度
            suffix: 后缀
            
        Returns:
            str: 截断后的字符串
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def get_domain_from_url(url: str) -> Optional[str]:
        """
        从URL提取域名
        
        Args:
            url: URL
            
        Returns:
            Optional[str]: 域名
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None 