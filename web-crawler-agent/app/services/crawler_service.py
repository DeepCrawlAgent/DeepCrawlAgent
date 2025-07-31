"""
爬虫调度服务
============

负责爬虫任务的调度、执行和结果管理。
集成webcrawl4ai，提供智能搜索功能。
"""

import uuid
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.crawler import (
    CrawlerRequest, CrawlerResponse, CrawlerConfig, CrawlerStatus,
    BatchCrawlerRequest, CrawlerResult, CrawlerStatistics
)
from app.models.search import (
    SearchRequest, SearchResponse, SearchResult, SearchHistory,
    TrendingSearch
)
from app.core.exceptions import CrawlerException, ValidationException
from app.utils.logger import setup_logger
from app.storage.redis_manager import RedisManager
from app.crawlers.web_crawler4ai import WebCrawler4AI

# 初始化日志
logger = setup_logger(__name__)


class CrawlerService:
    """爬虫调度服务类"""
    
    def __init__(self):
        """初始化爬虫服务"""
        self.redis_manager = RedisManager()
        self.web_crawler = WebCrawler4AI()
        self.task_prefix = "crawler_task:"
        self.result_prefix = "crawler_result:"
        self.search_prefix = "search:"
        
    async def create_crawl_task(self, request: CrawlerRequest) -> str:
        """
        创建爬虫任务
        
        Args:
            request: 爬虫请求
            
        Returns:
            str: 任务ID
        """
        try:
            logger.info(f"创建爬虫任务: {request.url}")
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务数据
            task_data = {
                "id": task_id,
                "url": str(request.url),
                "method": request.method,
                "headers": request.headers,
                "params": request.params,
                "data": request.data,
                "config": request.config.dict() if request.config else None,
                "extract_rules": request.extract_rules,
                "save_format": request.save_format,
                "callback_url": str(request.callback_url) if request.callback_url else None,
                "status": CrawlerStatus.PENDING,
                "created_time": datetime.now().isoformat(),
                "progress": {"current": 0, "total": 1}
            }
            
            # 保存任务数据
            await self.redis_manager.set(
                f"{self.task_prefix}{task_id}",
                task_data,
                expire=24 * 3600  # 24小时过期
            )
            
            logger.info(f"爬虫任务创建成功: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"创建爬虫任务失败: {str(e)}")
            raise CrawlerException(f"创建爬虫任务失败: {str(e)}")
    
    async def execute_crawl_task(self, task_id: str) -> CrawlerResponse:
        """
        执行爬虫任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            CrawlerResponse: 爬虫响应
        """
        try:
            logger.info(f"执行爬虫任务: {task_id}")
            
            # 获取任务数据
            task_data = await self.redis_manager.get(f"{self.task_prefix}{task_id}")
            if not task_data:
                raise CrawlerException(f"爬虫任务未找到: {task_id}")
            
            # 更新任务状态为运行中
            task_data["status"] = CrawlerStatus.RUNNING
            task_data["started_time"] = datetime.now().isoformat()
            await self.redis_manager.set(
                f"{self.task_prefix}{task_id}",
                task_data,
                expire=24 * 3600
            )
            
            # 执行爬虫
            start_time = datetime.now()
            result = await self.web_crawler.crawl(
                url=task_data["url"],
                method=task_data["method"],
                headers=task_data["headers"],
                config=task_data["config"],
                extract_rules=task_data["extract_rules"]
            )
            
            # 创建爬虫结果
            crawler_result = CrawlerResult(
                url=task_data["url"],
                status_code=result.get("status_code", 200),
                content_type=result.get("content_type", "text/html"),
                content_length=len(result.get("content", "")),
                title=result.get("title"),
                content=result.get("content"),
                links=result.get("links", []),
                images=result.get("images", []),
                metadata=result.get("metadata", {}),
                extracted_data=result.get("extracted_data", {}),
                response_time=(datetime.now() - start_time).total_seconds(),
                crawl_time=datetime.now(),
                error_message=result.get("error_message")
            )
            
            # 保存结果
            await self.redis_manager.set(
                f"{self.result_prefix}{task_id}",
                crawler_result.dict(),
                expire=7 * 24 * 3600  # 7天过期
            )
            
            # 更新任务状态
            task_data["status"] = CrawlerStatus.COMPLETED if not result.get("error_message") else CrawlerStatus.FAILED
            task_data["completed_time"] = datetime.now().isoformat()
            task_data["progress"] = {"current": 1, "total": 1}
            await self.redis_manager.set(
                f"{self.task_prefix}{task_id}",
                task_data,
                expire=24 * 3600
            )
            
            # 创建响应
            response = CrawlerResponse(
                task_id=task_id,
                status=task_data["status"],
                message="爬取完成" if not result.get("error_message") else f"爬取失败: {result.get('error_message')}",
                url=task_data["url"],
                result=crawler_result,
                created_time=datetime.fromisoformat(task_data["created_time"]),
                started_time=datetime.fromisoformat(task_data["started_time"]),
                completed_time=datetime.fromisoformat(task_data["completed_time"])
            )
            
            logger.info(f"爬虫任务执行完成: {task_id}")
            return response
            
        except Exception as e:
            logger.error(f"执行爬虫任务失败: {str(e)}")
            # 更新任务状态为失败
            if task_data:
                task_data["status"] = CrawlerStatus.FAILED
                task_data["error_message"] = str(e)
                await self.redis_manager.set(
                    f"{self.task_prefix}{task_id}",
                    task_data,
                    expire=24 * 3600
                )
            raise CrawlerException(f"执行爬虫任务失败: {str(e)}")
    
    async def create_batch_crawl_task(self, request: BatchCrawlerRequest) -> str:
        """
        创建批量爬虫任务
        
        Args:
            request: 批量爬虫请求
            
        Returns:
            str: 批量任务ID
        """
        try:
            logger.info(f"创建批量爬虫任务: {len(request.urls)}个URL")
            
            # 生成批量任务ID
            batch_task_id = str(uuid.uuid4())
            
            # 创建子任务
            sub_task_ids = []
            for url in request.urls:
                sub_request = CrawlerRequest(
                    url=url,
                    method=request.method,
                    config=request.config,
                    extract_rules=request.extract_rules,
                    save_format=request.save_format,
                    async_mode=True
                )
                sub_task_id = await self.create_crawl_task(sub_request)
                sub_task_ids.append(sub_task_id)
            
            # 创建批量任务数据
            batch_data = {
                "id": batch_task_id,
                "sub_task_ids": sub_task_ids,
                "total_urls": len(request.urls),
                "completed_urls": 0,
                "failed_urls": 0,
                "status": CrawlerStatus.PENDING,
                "created_time": datetime.now().isoformat(),
                "max_concurrent": request.max_concurrent
            }
            
            # 保存批量任务数据
            await self.redis_manager.set(
                f"batch_{self.task_prefix}{batch_task_id}",
                batch_data,
                expire=24 * 3600
            )
            
            logger.info(f"批量爬虫任务创建成功: {batch_task_id}")
            return batch_task_id
            
        except Exception as e:
            logger.error(f"创建批量爬虫任务失败: {str(e)}")
            raise CrawlerException(f"创建批量爬虫任务失败: {str(e)}")
    
    async def execute_batch_crawl_task(self, batch_task_id: str):
        """
        执行批量爬虫任务
        
        Args:
            batch_task_id: 批量任务ID
        """
        try:
            logger.info(f"执行批量爬虫任务: {batch_task_id}")
            
            # 获取批量任务数据
            batch_data = await self.redis_manager.get(f"batch_{self.task_prefix}{batch_task_id}")
            if not batch_data:
                raise CrawlerException(f"批量爬虫任务未找到: {batch_task_id}")
            
            # 更新状态为运行中
            batch_data["status"] = CrawlerStatus.RUNNING
            batch_data["started_time"] = datetime.now().isoformat()
            await self.redis_manager.set(
                f"batch_{self.task_prefix}{batch_task_id}",
                batch_data,
                expire=24 * 3600
            )
            
            # 并发执行子任务
            semaphore = asyncio.Semaphore(batch_data["max_concurrent"])
            tasks = []
            
            async def execute_sub_task(sub_task_id: str):
                async with semaphore:
                    try:
                        await self.execute_crawl_task(sub_task_id)
                        batch_data["completed_urls"] += 1
                    except Exception as e:
                        logger.error(f"子任务执行失败: {sub_task_id}, {str(e)}")
                        batch_data["failed_urls"] += 1
                    
                    # 更新进度
                    await self.redis_manager.set(
                        f"batch_{self.task_prefix}{batch_task_id}",
                        batch_data,
                        expire=24 * 3600
                    )
            
            # 创建所有子任务
            for sub_task_id in batch_data["sub_task_ids"]:
                task = asyncio.create_task(execute_sub_task(sub_task_id))
                tasks.append(task)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 更新最终状态
            batch_data["status"] = CrawlerStatus.COMPLETED
            batch_data["completed_time"] = datetime.now().isoformat()
            await self.redis_manager.set(
                f"batch_{self.task_prefix}{batch_task_id}",
                batch_data,
                expire=24 * 3600
            )
            
            logger.info(f"批量爬虫任务执行完成: {batch_task_id}")
            
        except Exception as e:
            logger.error(f"执行批量爬虫任务失败: {str(e)}")
            raise CrawlerException(f"执行批量爬虫任务失败: {str(e)}")
    
    async def get_crawl_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取爬虫任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务状态信息
        """
        try:
            task_data = await self.redis_manager.get(f"{self.task_prefix}{task_id}")
            return task_data
            
        except Exception as e:
            logger.error(f"获取爬虫任务状态失败: {str(e)}")
            raise CrawlerException(f"获取爬虫任务状态失败: {str(e)}")
    
    async def get_crawl_result(self, task_id: str, format: str = "json") -> Optional[Dict[str, Any]]:
        """
        获取爬虫任务结果
        
        Args:
            task_id: 任务ID
            format: 返回格式
            
        Returns:
            Optional[Dict[str, Any]]: 任务结果
        """
        try:
            result_data = await self.redis_manager.get(f"{self.result_prefix}{task_id}")
            if not result_data:
                return None
            
            # 根据格式转换结果
            if format == "json":
                return result_data
            elif format == "html":
                return {"content": result_data.get("content", "")}
            elif format == "text":
                # 简单的HTML转文本处理
                content = result_data.get("content", "")
                # 这里应该使用更完善的HTML转文本库
                import re
                text = re.sub(r'<[^>]+>', '', content)
                return {"text": text}
            else:
                return result_data
                
        except Exception as e:
            logger.error(f"获取爬虫任务结果失败: {str(e)}")
            raise CrawlerException(f"获取爬虫任务结果失败: {str(e)}")
    
    async def cancel_crawl_task(self, task_id: str) -> bool:
        """
        取消爬虫任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否取消成功
        """
        try:
            task_data = await self.redis_manager.get(f"{self.task_prefix}{task_id}")
            if not task_data:
                return False
            
            # 只能取消待执行或运行中的任务
            if task_data["status"] in [CrawlerStatus.PENDING, CrawlerStatus.RUNNING]:
                task_data["status"] = CrawlerStatus.CANCELLED
                task_data["completed_time"] = datetime.now().isoformat()
                await self.redis_manager.set(
                    f"{self.task_prefix}{task_id}",
                    task_data,
                    expire=24 * 3600
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"取消爬虫任务失败: {str(e)}")
            raise CrawlerException(f"取消爬虫任务失败: {str(e)}")
    
    async def get_crawler_config(self) -> CrawlerConfig:
        """
        获取爬虫配置
        
        Returns:
            CrawlerConfig: 爬虫配置
        """
        try:
            config_data = await self.redis_manager.get("crawler_config")
            if config_data:
                return CrawlerConfig(**config_data)
            else:
                return CrawlerConfig()  # 返回默认配置
                
        except Exception as e:
            logger.error(f"获取爬虫配置失败: {str(e)}")
            raise CrawlerException(f"获取爬虫配置失败: {str(e)}")
    
    async def update_crawler_config(self, config: CrawlerConfig) -> CrawlerConfig:
        """
        更新爬虫配置
        
        Args:
            config: 新的爬虫配置
            
        Returns:
            CrawlerConfig: 更新后的配置
        """
        try:
            await self.redis_manager.set(
                "crawler_config",
                config.dict(),
                expire=30 * 24 * 3600  # 30天过期
            )
            return config
            
        except Exception as e:
            logger.error(f"更新爬虫配置失败: {str(e)}")
            raise CrawlerException(f"更新爬虫配置失败: {str(e)}")
    
    async def get_statistics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> CrawlerStatistics:
        """
        获取爬虫统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            CrawlerStatistics: 统计信息
        """
        try:
            # 这里应该从数据库或缓存中获取统计数据
            # 暂时返回模拟数据
            stats = CrawlerStatistics(
                total_requests=1000,
                successful_requests=950,
                failed_requests=50,
                average_response_time=2.5,
                total_data_crawled=1024 * 1024 * 100,  # 100MB
                requests_per_hour=50.0,
                success_rate=95.0
            )
            return stats
            
        except Exception as e:
            logger.error(f"获取爬虫统计信息失败: {str(e)}")
            raise CrawlerException(f"获取爬虫统计信息失败: {str(e)}")
    
    # 智能搜索相关方法
    async def intelligent_search(self, request: SearchRequest) -> List[SearchResult]:
        """
        执行智能搜索
        
        Args:
            request: 搜索请求
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        try:
            logger.info(f"执行智能搜索: {request.query}")
            
            # 这里应该集成实际的搜索引擎和智能体
            # 暂时返回模拟结果
            results = []
            for i in range(min(request.max_results, 5)):
                result = SearchResult(
                    id=str(uuid.uuid4()),
                    title=f"搜索结果 {i+1}: {request.query}",
                    url=f"https://example.com/result-{i+1}",
                    snippet=f"这是关于 {request.query} 的搜索结果片段...",
                    relevance_score=0.9 - i * 0.1,
                    quality_score=0.8,
                    popularity_score=0.7,
                    domain="example.com",
                    content_type="text/html",
                    content_length=1000,
                    crawled_date=datetime.now(),
                    search_time=0.5
                )
                results.append(result)
            
            # 保存搜索历史
            await self._save_search_history(request, results)
            
            return results
            
        except Exception as e:
            logger.error(f"智能搜索失败: {str(e)}")
            raise CrawlerException(f"智能搜索失败: {str(e)}")
    
    async def semantic_search(self, request: SearchRequest) -> List[SearchResult]:
        """
        执行语义搜索
        
        Args:
            request: 搜索请求
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        try:
            logger.info(f"执行语义搜索: {request.query}")
            
            # 这里应该集成语义搜索引擎
            # 暂时返回模拟结果
            results = await self.intelligent_search(request)
            
            return results
            
        except Exception as e:
            logger.error(f"语义搜索失败: {str(e)}")
            raise CrawlerException(f"语义搜索失败: {str(e)}")
    
    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        获取搜索建议
        
        Args:
            query: 搜索查询
            limit: 建议数量
            
        Returns:
            List[str]: 搜索建议列表
        """
        try:
            # 这里应该基于历史搜索和智能分析生成建议
            # 暂时返回模拟建议
            suggestions = [
                f"{query} 教程",
                f"{query} 最佳实践",
                f"{query} 示例",
                f"如何使用 {query}",
                f"{query} 对比"
            ]
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"获取搜索建议失败: {str(e)}")
            return []
    
    async def get_search_history(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取搜索历史
        
        Args:
            user_id: 用户ID
            limit: 历史记录数量
            
        Returns:
            List[Dict[str, Any]]: 搜索历史列表
        """
        try:
            # 这里应该从数据库获取搜索历史
            # 暂时返回空列表
            return []
            
        except Exception as e:
            logger.error(f"获取搜索历史失败: {str(e)}")
            return []
    
    async def clear_search_history(self, user_id: Optional[str] = None) -> int:
        """
        清除搜索历史
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 清除的记录数
        """
        try:
            # 这里应该从数据库清除搜索历史
            # 暂时返回0
            return 0
            
        except Exception as e:
            logger.error(f"清除搜索历史失败: {str(e)}")
            return 0
    
    async def get_trending_searches(self, limit: int = 10, time_range: str = "24h") -> List[TrendingSearch]:
        """
        获取热门搜索
        
        Args:
            limit: 热门搜索数量
            time_range: 时间范围
            
        Returns:
            List[TrendingSearch]: 热门搜索列表
        """
        try:
            # 这里应该从数据库获取热门搜索统计
            # 暂时返回模拟数据
            trending = []
            for i in range(limit):
                trend = TrendingSearch(
                    query=f"热门搜索 {i+1}",
                    search_count=100 - i * 5,
                    trend_score=90 - i * 5,
                    growth_rate=10.0 + i,
                    time_range=time_range
                )
                trending.append(trend)
            
            return trending
            
        except Exception as e:
            logger.error(f"获取热门搜索失败: {str(e)}")
            return []
    
    async def submit_search_feedback(self, search_id: str, result_id: str, feedback_type: str) -> bool:
        """
        提交搜索反馈
        
        Args:
            search_id: 搜索ID
            result_id: 结果ID
            feedback_type: 反馈类型
            
        Returns:
            bool: 是否提交成功
        """
        try:
            # 这里应该保存反馈到数据库
            # 暂时返回True
            return True
            
        except Exception as e:
            logger.error(f"提交搜索反馈失败: {str(e)}")
            return False
    
    async def _save_search_history(self, request: SearchRequest, results: List[SearchResult]):
        """保存搜索历史"""
        try:
            search_history = {
                "query": request.query,
                "search_type": request.search_type,
                "results_count": len(results),
                "user_id": request.user_id,
                "session_id": request.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存到Redis（这里应该保存到数据库）
            await self.redis_manager.list_push(
                f"{self.search_prefix}history",
                search_history,
                max_length=1000
            )
            
        except Exception as e:
            logger.error(f"保存搜索历史失败: {str(e)}") 