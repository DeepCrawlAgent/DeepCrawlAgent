"""
爬虫工具函数
============

提供爬虫相关的通用工具函数。
"""

import re
import urllib.parse
from typing import List, Optional, Dict, Any
from urllib.robotparser import RobotFileParser

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CrawlerUtils:
    """爬虫工具类"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        验证URL是否有效
        
        Args:
            url: 待验证的URL
            
        Returns:
            bool: 是否有效
        """
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        规范化URL
        
        Args:
            url: 原始URL
            
        Returns:
            str: 规范化后的URL
        """
        try:
            # 移除尾部斜杠，统一格式
            url = url.rstrip('/')
            
            # 解析URL组件
            parsed = urllib.parse.urlparse(url)
            
            # 重新构建规范化的URL
            normalized = urllib.parse.urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            return normalized
            
        except Exception as e:
            logger.warning(f"URL规范化失败: {url}, {str(e)}")
            return url
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """
        提取URL的域名
        
        Args:
            url: URL
            
        Returns:
            Optional[str]: 域名
        """
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None
    
    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """
        检查两个URL是否属于同一域名
        
        Args:
            url1: 第一个URL
            url2: 第二个URL
            
        Returns:
            bool: 是否同域名
        """
        domain1 = CrawlerUtils.extract_domain(url1)
        domain2 = CrawlerUtils.extract_domain(url2)
        return domain1 == domain2 and domain1 is not None
    
    @staticmethod
    def can_fetch(url: str, user_agent: str = "*") -> bool:
        """
        检查robots.txt是否允许爬取
        
        Args:
            url: 目标URL
            user_agent: 用户代理
            
        Returns:
            bool: 是否允许爬取
        """
        try:
            domain = CrawlerUtils.extract_domain(url)
            if not domain:
                return False
            
            robots_url = f"https://{domain}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.warning(f"检查robots.txt失败: {url}, {str(e)}")
            # 如果无法检查，默认允许
            return True
    
    @staticmethod
    def extract_links(html_content: str, base_url: str = "") -> List[str]:
        """
        从HTML内容中提取链接
        
        Args:
            html_content: HTML内容
            base_url: 基础URL
            
        Returns:
            List[str]: 链接列表
        """
        try:
            # 使用正则表达式提取href属性
            link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
            matches = re.findall(link_pattern, html_content, re.IGNORECASE)
            
            links = []
            for match in matches:
                # 处理相对链接
                if base_url and not match.startswith(('http://', 'https://')):
                    link = urllib.parse.urljoin(base_url, match)
                else:
                    link = match
                
                if CrawlerUtils.is_valid_url(link):
                    links.append(CrawlerUtils.normalize_url(link))
            
            # 去重
            return list(set(links))
            
        except Exception as e:
            logger.warning(f"提取链接失败: {str(e)}")
            return []
    
    @staticmethod
    def extract_images(html_content: str, base_url: str = "") -> List[str]:
        """
        从HTML内容中提取图片链接
        
        Args:
            html_content: HTML内容
            base_url: 基础URL
            
        Returns:
            List[str]: 图片链接列表
        """
        try:
            # 提取img标签的src属性
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            images = []
            for match in matches:
                # 处理相对链接
                if base_url and not match.startswith(('http://', 'https://')):
                    img_url = urllib.parse.urljoin(base_url, match)
                else:
                    img_url = match
                
                if CrawlerUtils.is_valid_url(img_url):
                    images.append(CrawlerUtils.normalize_url(img_url))
            
            # 去重
            return list(set(images))
            
        except Exception as e:
            logger.warning(f"提取图片失败: {str(e)}")
            return []
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        try:
            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            
            # 移除多余的空白字符
            text = re.sub(r'\s+', ' ', text)
            
            # 移除首尾空白
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"文本清理失败: {str(e)}")
            return text
    
    @staticmethod
    def get_file_extension(url: str) -> Optional[str]:
        """
        获取URL对应文件的扩展名
        
        Args:
            url: URL
            
        Returns:
            Optional[str]: 文件扩展名
        """
        try:
            parsed = urllib.parse.urlparse(url)
            path = parsed.path
            
            if '.' in path:
                return path.split('.')[-1].lower()
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def is_static_resource(url: str) -> bool:
        """
        检查URL是否为静态资源
        
        Args:
            url: URL
            
        Returns:
            bool: 是否为静态资源
        """
        static_extensions = {
            'css', 'js', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'ico',
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar',
            'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv'
        }
        
        ext = CrawlerUtils.get_file_extension(url)
        return ext in static_extensions if ext else False 