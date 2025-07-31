"""
安全工具
========

提供安全相关的工具函数。
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.core.config import settings


class SecurityUtils:
    """安全工具类"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        生成随机令牌
        
        Args:
            length: 令牌长度
            
        Returns:
            str: 随机令牌
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed: 哈希密码
            
        Returns:
            bool: 是否匹配
        """
        try:
            salt, password_hash = hashed.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except Exception:
            return False
    
    @staticmethod
    def create_jwt_token(payload: Dict[str, Any], expires_hours: int = 24) -> str:
        """
        创建JWT令牌
        
        Args:
            payload: 载荷数据
            expires_hours: 过期时间(小时)
            
        Returns:
            str: JWT令牌
        """
        payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
        payload["iat"] = datetime.utcnow()
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 载荷数据
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None 