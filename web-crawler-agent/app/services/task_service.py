"""
任务管理服务
============

负责任务的创建、更新、删除、查询和执行管理。
提供任务生命周期的完整管理功能。
"""

import uuid
import asyncio
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from app.models.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskStatus, 
    TaskType, TaskProgress, TaskResult, TaskLog
)
from app.core.exceptions import NotFoundException, ValidationException, TaskException
from app.utils.logger import setup_logger
from app.storage.redis_manager import RedisManager
from app.tasks.crawler_tasks import CrawlerTask
from app.tasks.agent_tasks import AgentTask

# 初始化日志
logger = setup_logger(__name__)


class TaskService:
    """任务管理服务类"""
    
    def __init__(self):
        """初始化任务服务"""
        self.redis_manager = RedisManager()
        self.task_prefix = "task:"
        self.task_log_prefix = "task_log:"
        
    async def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """
        创建新任务
        
        Args:
            task_data: 任务创建数据
            
        Returns:
            TaskResponse: 创建的任务信息
        """
        try:
            logger.info(f"创建任务: {task_data.title}")
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务响应对象
            task = TaskResponse(
                id=task_id,
                title=task_data.title,
                description=task_data.description,
                task_type=task_data.task_type,
                status=TaskStatus.PENDING,
                priority=task_data.priority,
                config=task_data.config,
                target_urls=task_data.target_urls,
                created_time=datetime.now(),
                scheduled_time=task_data.scheduled_time,
                tags=task_data.tags
            )
            
            # 保存到Redis
            await self.redis_manager.set(
                f"{self.task_prefix}{task_id}",
                task.dict(),
                expire=7 * 24 * 3600  # 7天过期
            )
            
            # 记录日志
            await self._log_task_event(task_id, "INFO", "任务已创建")
            
            logger.info(f"任务创建成功: {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            raise TaskException(f"创建任务失败: {str(e)}")
    
    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskResponse]: 任务信息
        """
        try:
            logger.info(f"获取任务详情: {task_id}")
            
            task_data = await self.redis_manager.get(f"{self.task_prefix}{task_id}")
            if not task_data:
                return None
            
            return TaskResponse(**task_data)
            
        except Exception as e:
            logger.error(f"获取任务详情失败: {str(e)}")
            raise TaskException(f"获取任务详情失败: {str(e)}")
    
    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Optional[TaskResponse]:
        """
        更新任务信息
        
        Args:
            task_id: 任务ID
            task_data: 更新数据
            
        Returns:
            Optional[TaskResponse]: 更新后的任务信息
        """
        try:
            logger.info(f"更新任务: {task_id}")
            
            # 获取现有任务
            task = await self.get_task(task_id)
            if not task:
                return None
            
            # 更新字段
            update_data = task_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(task, key, value)
            
            # 保存更新
            await self.redis_manager.set(
                f"{self.task_prefix}{task_id}",
                task.dict(),
                expire=7 * 24 * 3600
            )
            
            # 记录日志
            await self._log_task_event(task_id, "INFO", "任务已更新")
            
            logger.info(f"任务更新成功: {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"更新任务失败: {str(e)}")
            raise TaskException(f"更新任务失败: {str(e)}")
    
    async def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            logger.info(f"删除任务: {task_id}")
            
            # 检查任务是否存在
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # 如果任务正在执行，先停止
            if task.status == TaskStatus.RUNNING:
                await self.stop_task(task_id)
            
            # 删除任务数据
            await self.redis_manager.delete(f"{self.task_prefix}{task_id}")
            
            # 删除任务日志
            await self.redis_manager.delete(f"{self.task_log_prefix}{task_id}")
            
            logger.info(f"任务删除成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除任务失败: {str(e)}")
            raise TaskException(f"删除任务失败: {str(e)}")
    
    async def list_tasks(
        self, 
        skip: int = 0, 
        limit: int = 10,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        search: Optional[str] = None
    ) -> Tuple[List[TaskResponse], int]:
        """
        获取任务列表
        
        Args:
            skip: 跳过数量
            limit: 限制数量
            status: 状态过滤
            task_type: 类型过滤
            search: 搜索关键词
            
        Returns:
            Tuple[List[TaskResponse], int]: 任务列表和总数
        """
        try:
            logger.info(f"获取任务列表: skip={skip}, limit={limit}")
            
            # 获取所有任务键
            task_keys = await self.redis_manager.scan_keys(f"{self.task_prefix}*")
            
            tasks = []
            for key in task_keys:
                task_data = await self.redis_manager.get(key)
                if task_data:
                    task = TaskResponse(**task_data)
                    
                    # 应用过滤条件
                    if status and task.status != status:
                        continue
                    if task_type and task.task_type != task_type:
                        continue
                    if search and search.lower() not in task.title.lower():
                        continue
                    
                    tasks.append(task)
            
            # 按创建时间降序排序
            tasks.sort(key=lambda x: x.created_time, reverse=True)
            
            # 应用分页
            total = len(tasks)
            tasks = tasks[skip:skip + limit]
            
            logger.info(f"获取任务列表成功: 总数={total}, 返回={len(tasks)}")
            return tasks, total
            
        except Exception as e:
            logger.error(f"获取任务列表失败: {str(e)}")
            raise TaskException(f"获取任务列表失败: {str(e)}")
    
    async def start_task(self, task_id: str) -> bool:
        """
        启动任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否启动成功
        """
        try:
            logger.info(f"启动任务: {task_id}")
            
            # 获取任务
            task = await self.get_task(task_id)
            if not task:
                raise NotFoundException(f"任务未找到: {task_id}")
            
            # 检查任务状态
            if task.status != TaskStatus.PENDING:
                raise ValidationException(f"任务状态不允许启动: {task.status}")
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_time = datetime.now()
            
            # 保存状态更新
            await self.redis_manager.set(
                f"{self.task_prefix}{task_id}",
                task.dict(),
                expire=7 * 24 * 3600
            )
            
            # 根据任务类型执行
            if task.task_type == TaskType.CRAWLER:
                await self._execute_crawler_task(task)
            elif task.task_type == TaskType.AGENT:
                await self._execute_agent_task(task)
            else:
                raise ValidationException(f"不支持的任务类型: {task.task_type}")
            
            # 记录日志
            await self._log_task_event(task_id, "INFO", "任务已启动")
            
            logger.info(f"任务启动成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"启动任务失败: {str(e)}")
            # 更新任务状态为失败
            await self._update_task_status(task_id, TaskStatus.FAILED, str(e))
            raise TaskException(f"启动任务失败: {str(e)}")
    
    async def stop_task(self, task_id: str) -> bool:
        """
        停止任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否停止成功
        """
        try:
            logger.info(f"停止任务: {task_id}")
            
            # 获取任务
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # 检查任务状态
            if task.status != TaskStatus.RUNNING:
                return True
            
            # 更新任务状态
            await self._update_task_status(task_id, TaskStatus.CANCELLED)
            
            # 记录日志
            await self._log_task_event(task_id, "INFO", "任务已停止")
            
            logger.info(f"任务停止成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"停止任务失败: {str(e)}")
            raise TaskException(f"停止任务失败: {str(e)}")
    
    async def get_task_logs(self, task_id: str, lines: int = 100) -> List[str]:
        """
        获取任务日志
        
        Args:
            task_id: 任务ID
            lines: 日志行数
            
        Returns:
            List[str]: 日志列表
        """
        try:
            logger.info(f"获取任务日志: {task_id}")
            
            logs = await self.redis_manager.get_list(
                f"{self.task_log_prefix}{task_id}",
                start=-lines
            )
            
            return logs or []
            
        except Exception as e:
            logger.error(f"获取任务日志失败: {str(e)}")
            raise TaskException(f"获取任务日志失败: {str(e)}")
    
    async def _execute_crawler_task(self, task: TaskResponse):
        """执行爬虫任务"""
        try:
            crawler_task = CrawlerTask()
            await crawler_task.execute(task)
        except Exception as e:
            logger.error(f"执行爬虫任务失败: {str(e)}")
            raise
    
    async def _execute_agent_task(self, task: TaskResponse):
        """执行智能体任务"""
        try:
            agent_task = AgentTask()
            await agent_task.execute(task)
        except Exception as e:
            logger.error(f"执行智能体任务失败: {str(e)}")
            raise
    
    async def _update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus, 
        error_message: Optional[str] = None
    ):
        """更新任务状态"""
        try:
            task = await self.get_task(task_id)
            if task:
                task.status = status
                if status == TaskStatus.COMPLETED:
                    task.completed_time = datetime.now()
                elif status == TaskStatus.FAILED and error_message:
                    if not task.result:
                        task.result = TaskResult()
                    if not task.result.error_messages:
                        task.result.error_messages = []
                    task.result.error_messages.append(error_message)
                
                await self.redis_manager.set(
                    f"{self.task_prefix}{task_id}",
                    task.dict(),
                    expire=7 * 24 * 3600
                )
        except Exception as e:
            logger.error(f"更新任务状态失败: {str(e)}")
    
    async def _log_task_event(self, task_id: str, level: str, message: str):
        """记录任务事件日志"""
        try:
            log_entry = f"[{datetime.now().isoformat()}] {level}: {message}"
            await self.redis_manager.list_push(
                f"{self.task_log_prefix}{task_id}",
                log_entry,
                max_length=1000  # 最多保留1000条日志
            )
        except Exception as e:
            logger.error(f"记录任务日志失败: {str(e)}") 