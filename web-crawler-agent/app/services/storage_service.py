"""
存储服务
========

提供统一的存储接口，支持多种存储后端：
- 本地文件存储
- 云存储(S3, OSS等)
- 数据库存储
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import StorageException
from app.utils.logger import setup_logger

# 初始化日志
logger = setup_logger(__name__)


class StorageService:
    """存储服务类"""
    
    def __init__(self):
        """初始化存储服务"""
        self.storage_type = settings.STORAGE_TYPE
        self.storage_path = Path(settings.STORAGE_PATH)
        self.max_file_size = settings.MAX_FILE_SIZE
        
        # 确保存储目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.storage_path,
            self.storage_path / "uploads",
            self.storage_path / "cache",
            self.storage_path / "temp",
            self.storage_path / "results",
            self.storage_path / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def save_file(
        self, 
        file_content: bytes, 
        filename: str, 
        folder: str = "uploads",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        保存文件
        
        Args:
            file_content: 文件内容
            filename: 文件名
            folder: 文件夹
            metadata: 元数据
            
        Returns:
            Dict[str, Any]: 保存结果信息
        """
        try:
            logger.info(f"保存文件: {filename} 到 {folder}")
            
            # 检查文件大小
            if len(file_content) > self.max_file_size:
                raise StorageException(f"文件大小超过限制: {len(file_content)} > {self.max_file_size}")
            
            # 生成文件路径
            folder_path = self.storage_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            file_hash = hashlib.md5(file_content).hexdigest()
            file_ext = Path(filename).suffix
            unique_filename = f"{file_hash}_{int(datetime.now().timestamp())}{file_ext}"
            file_path = folder_path / unique_filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 保存元数据
            metadata_info = {
                "original_filename": filename,
                "saved_filename": unique_filename,
                "file_path": str(file_path),
                "file_size": len(file_content),
                "file_hash": file_hash,
                "content_type": self._detect_content_type(filename),
                "created_time": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # 保存元数据文件
            metadata_path = file_path.with_suffix('.meta.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"文件保存成功: {unique_filename}")
            return {
                "filename": unique_filename,
                "file_path": str(file_path),
                "file_size": len(file_content),
                "file_hash": file_hash,
                "url": f"/storage/{folder}/{unique_filename}"
            }
            
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            raise StorageException(f"保存文件失败: {str(e)}")
    
    async def get_file(self, filename: str, folder: str = "uploads") -> Optional[bytes]:
        """
        获取文件内容
        
        Args:
            filename: 文件名
            folder: 文件夹
            
        Returns:
            Optional[bytes]: 文件内容
        """
        try:
            logger.info(f"获取文件: {filename} 从 {folder}")
            
            file_path = self.storage_path / folder / filename
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"文件获取成功: {filename}")
            return content
            
        except Exception as e:
            logger.error(f"获取文件失败: {str(e)}")
            raise StorageException(f"获取文件失败: {str(e)}")
    
    async def get_file_info(self, filename: str, folder: str = "uploads") -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            filename: 文件名
            folder: 文件夹
            
        Returns:
            Optional[Dict[str, Any]]: 文件信息
        """
        try:
            file_path = self.storage_path / folder / filename
            metadata_path = file_path.with_suffix('.meta.json')
            
            if not metadata_path.exists():
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            raise StorageException(f"获取文件信息失败: {str(e)}")
    
    async def delete_file(self, filename: str, folder: str = "uploads") -> bool:
        """
        删除文件
        
        Args:
            filename: 文件名
            folder: 文件夹
            
        Returns:
            bool: 是否删除成功
        """
        try:
            logger.info(f"删除文件: {filename} 从 {folder}")
            
            file_path = self.storage_path / folder / filename
            metadata_path = file_path.with_suffix('.meta.json')
            
            # 删除文件
            if file_path.exists():
                file_path.unlink()
            
            # 删除元数据文件
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"文件删除成功: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            raise StorageException(f"删除文件失败: {str(e)}")
    
    async def list_files(self, folder: str = "uploads", limit: int = 100) -> List[Dict[str, Any]]:
        """
        列出文件
        
        Args:
            folder: 文件夹
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 文件列表
        """
        try:
            logger.info(f"列出文件: {folder}")
            
            folder_path = self.storage_path / folder
            if not folder_path.exists():
                return []
            
            files = []
            for file_path in folder_path.glob("*"):
                if file_path.is_file() and not file_path.name.endswith('.meta.json'):
                    metadata_path = file_path.with_suffix('.meta.json')
                    
                    if metadata_path.exists():
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        files.append(metadata)
                    else:
                        # 没有元数据，创建基本信息
                        stat = file_path.stat()
                        files.append({
                            "original_filename": file_path.name,
                            "saved_filename": file_path.name,
                            "file_path": str(file_path),
                            "file_size": stat.st_size,
                            "content_type": self._detect_content_type(file_path.name),
                            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat()
                        })
                    
                    if len(files) >= limit:
                        break
            
            # 按创建时间排序
            files.sort(key=lambda x: x.get("created_time", ""), reverse=True)
            
            logger.info(f"文件列表获取成功: {len(files)}个文件")
            return files
            
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            raise StorageException(f"列出文件失败: {str(e)}")
    
    async def save_crawl_result(
        self, 
        task_id: str, 
        result_data: Dict[str, Any], 
        format: str = "json"
    ) -> str:
        """
        保存爬虫结果
        
        Args:
            task_id: 任务ID
            result_data: 结果数据
            format: 保存格式
            
        Returns:
            str: 保存的文件路径
        """
        try:
            logger.info(f"保存爬虫结果: {task_id}")
            
            # 确定文件格式和内容
            if format == "json":
                content = json.dumps(result_data, ensure_ascii=False, indent=2).encode('utf-8')
                filename = f"crawl_result_{task_id}.json"
            elif format == "html":
                content = result_data.get("content", "").encode('utf-8')
                filename = f"crawl_result_{task_id}.html"
            elif format == "text":
                # 简单的HTML转文本处理
                import re
                text_content = re.sub(r'<[^>]+>', '', result_data.get("content", ""))
                content = text_content.encode('utf-8')
                filename = f"crawl_result_{task_id}.txt"
            else:
                content = str(result_data).encode('utf-8')
                filename = f"crawl_result_{task_id}.txt"
            
            # 保存文件
            save_result = await self.save_file(
                file_content=content,
                filename=filename,
                folder="results",
                metadata={
                    "task_id": task_id,
                    "format": format,
                    "url": result_data.get("url"),
                    "status_code": result_data.get("status_code"),
                    "content_type": result_data.get("content_type")
                }
            )
            
            logger.info(f"爬虫结果保存成功: {save_result['filename']}")
            return save_result["file_path"]
            
        except Exception as e:
            logger.error(f"保存爬虫结果失败: {str(e)}")
            raise StorageException(f"保存爬虫结果失败: {str(e)}")
    
    async def save_temp_file(self, content: bytes, filename: str) -> str:
        """
        保存临时文件
        
        Args:
            content: 文件内容
            filename: 文件名
            
        Returns:
            str: 临时文件路径
        """
        try:
            save_result = await self.save_file(
                file_content=content,
                filename=filename,
                folder="temp"
            )
            return save_result["file_path"]
            
        except Exception as e:
            logger.error(f"保存临时文件失败: {str(e)}")
            raise StorageException(f"保存临时文件失败: {str(e)}")
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        清理临时文件
        
        Args:
            max_age_hours: 最大保留时间(小时)
        """
        try:
            logger.info(f"清理临时文件: 超过{max_age_hours}小时的文件")
            
            temp_path = self.storage_path / "temp"
            if not temp_path.exists():
                return
            
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            deleted_count = 0
            for file_path in temp_path.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        # 同时删除元数据文件
                        metadata_path = file_path.with_suffix('.meta.json')
                        if metadata_path.exists():
                            metadata_path.unlink()
                        deleted_count += 1
            
            logger.info(f"临时文件清理完成: 删除了{deleted_count}个文件")
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict[str, Any]: 存储统计信息
        """
        try:
            stats = {}
            
            for folder in ["uploads", "cache", "temp", "results", "logs"]:
                folder_path = self.storage_path / folder
                if folder_path.exists():
                    total_size = 0
                    file_count = 0
                    
                    for file_path in folder_path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
                    
                    stats[folder] = {
                        "file_count": file_count,
                        "total_size": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                else:
                    stats[folder] = {
                        "file_count": 0,
                        "total_size": 0,
                        "total_size_mb": 0
                    }
            
            # 计算总计
            total_files = sum(folder["file_count"] for folder in stats.values())
            total_size = sum(folder["total_size"] for folder in stats.values())
            
            stats["total"] = {
                "file_count": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {str(e)}")
            raise StorageException(f"获取存储统计信息失败: {str(e)}")
    
    def _detect_content_type(self, filename: str) -> str:
        """
        检测文件内容类型
        
        Args:
            filename: 文件名
            
        Returns:
            str: 内容类型
        """
        ext = Path(filename).suffix.lower()
        
        content_types = {
            '.json': 'application/json',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.xml': 'application/xml',
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.zip': 'application/zip',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip'
        }
        
        return content_types.get(ext, 'application/octet-stream') 