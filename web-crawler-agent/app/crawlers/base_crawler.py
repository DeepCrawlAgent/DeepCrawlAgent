"""
基础爬虫类
==========

定义爬虫的基础接口和通用功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseCrawler(ABC):
    """基础爬虫抽象类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.session = None
        self.default_headers = {
            "User-Agent": "Web-Crawler-Agent/1.0"
        }
    
    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        爬取URL
        
        Args:
            url: 目标URL
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 爬取结果
        """
        pass
    
    @abstractmethod
    async def setup(self):
        """设置爬虫"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass 