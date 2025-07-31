"""
任务管理API
===========

提供任务的创建、查询、更新、删除等操作。
包括爬虫任务和智能体任务的管理。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, BackgroundTasks, Body
from fastapi.responses import JSONResponse

from app.models.task import (
    TaskCreate, TaskUpdate, TaskResponse, 
    TaskListResponse, TaskStatus, TaskType
)
from app.services.task_service import TaskService
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.logger import setup_logger

# 创建路由器
router = APIRouter()

# 初始化日志
logger = setup_logger(__name__)

# 依赖注入
def get_task_service() -> TaskService:
    """获取任务服务实例"""
    return TaskService()


@router.post("/", response_model=TaskResponse, summary="创建新任务")
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    task_service: TaskService = Depends(get_task_service)
):
    """
    创建新的任务
    
    支持的任务类型：
    - CRAWLER: 爬虫任务
    - AGENT: 智能体任务
    - SEARCH: 搜索任务
    """
    try:
        logger.info(f"创建新任务: {task_data.title}")
        
        # 创建任务
        task = await task_service.create_task(task_data)
        
        # 如果需要立即执行，添加到后台任务
        if task_data.auto_start:
            background_tasks.add_task(task_service.start_task, task.id)
        
        return task
        
    except ValidationException as e:
        logger.error(f"任务创建失败，验证错误: {e.detail}")
        raise HTTPException(status_code=422, detail=e.detail)
    except Exception as e:
        logger.error(f"任务创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail="任务创建失败")


@router.get("/", response_model=TaskListResponse, summary="获取任务列表")
async def list_tasks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    status: Optional[TaskStatus] = Query(None, description="任务状态过滤"),
    task_type: Optional[TaskType] = Query(None, description="任务类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取任务列表
    
    支持分页、过滤和搜索功能
    """
    try:
        logger.info(f"获取任务列表: skip={skip}, limit={limit}")
        
        tasks, total = await task_service.list_tasks(
            skip=skip,
            limit=limit,
            status=status,
            task_type=task_type,
            search=search
        )
        
        return TaskListResponse(
            tasks=tasks,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务列表失败")


@router.get("/{task_id}", response_model=TaskResponse, summary="获取任务详情")
async def get_task(
    task_id: str = Path(..., description="任务ID"),
    task_service: TaskService = Depends(get_task_service)
):
    """获取指定任务的详细信息"""
    try:
        logger.info(f"获取任务详情: {task_id}")
        
        task = await task_service.get_task(task_id)
        if not task:
            raise NotFoundException(f"任务未找到: {task_id}")
        
        return task
        
    except NotFoundException as e:
        logger.warning(f"任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务详情失败")


@router.put("/{task_id}", response_model=TaskResponse, summary="更新任务")
async def update_task(
    task_id: str = Path(..., description="任务ID"),
    task_data: TaskUpdate = Body(...),
    task_service: TaskService = Depends(get_task_service)
):
    """更新指定任务的信息"""
    try:
        logger.info(f"更新任务: {task_id}")
        
        task = await task_service.update_task(task_id, task_data)
        if not task:
            raise NotFoundException(f"任务未找到: {task_id}")
        
        return task
        
    except NotFoundException as e:
        logger.warning(f"任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except ValidationException as e:
        logger.error(f"任务更新失败，验证错误: {e.detail}")
        raise HTTPException(status_code=422, detail=e.detail)
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新任务失败")


@router.delete("/{task_id}", summary="删除任务")
async def delete_task(
    task_id: str = Path(..., description="任务ID"),
    task_service: TaskService = Depends(get_task_service)
):
    """删除指定任务"""
    try:
        logger.info(f"删除任务: {task_id}")
        
        success = await task_service.delete_task(task_id)
        if not success:
            raise NotFoundException(f"任务未找到: {task_id}")
        
        return {"message": "任务删除成功", "task_id": task_id}
        
    except NotFoundException as e:
        logger.warning(f"任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除任务失败")


@router.post("/{task_id}/start", summary="启动任务")
async def start_task(
    task_id: str = Path(..., description="任务ID"),
    background_tasks: BackgroundTasks,
    task_service: TaskService = Depends(get_task_service)
):
    """启动指定任务的执行"""
    try:
        logger.info(f"启动任务: {task_id}")
        
        # 添加到后台任务队列
        background_tasks.add_task(task_service.start_task, task_id)
        
        return {"message": "任务启动成功", "task_id": task_id}
        
    except NotFoundException as e:
        logger.warning(f"任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"启动任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="启动任务失败")


@router.post("/{task_id}/stop", summary="停止任务")
async def stop_task(
    task_id: str = Path(..., description="任务ID"),
    task_service: TaskService = Depends(get_task_service)
):
    """停止指定任务的执行"""
    try:
        logger.info(f"停止任务: {task_id}")
        
        success = await task_service.stop_task(task_id)
        if not success:
            raise NotFoundException(f"任务未找到或无法停止: {task_id}")
        
        return {"message": "任务停止成功", "task_id": task_id}
        
    except NotFoundException as e:
        logger.warning(f"任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"停止任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="停止任务失败")


@router.get("/{task_id}/logs", summary="获取任务日志")
async def get_task_logs(
    task_id: str = Path(..., description="任务ID"),
    lines: int = Query(100, ge=1, le=1000, description="返回的日志行数"),
    task_service: TaskService = Depends(get_task_service)
):
    """获取指定任务的执行日志"""
    try:
        logger.info(f"获取任务日志: {task_id}")
        
        logs = await task_service.get_task_logs(task_id, lines)
        
        return {"task_id": task_id, "logs": logs}
        
    except NotFoundException as e:
        logger.warning(f"任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"获取任务日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务日志失败") 