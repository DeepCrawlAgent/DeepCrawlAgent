"""
爬虫控制API
===========

提供爬虫的启动、停止、配置和监控功能。
支持单次爬取和批量爬取操作。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.models.crawler import (
    CrawlerRequest, CrawlerResponse, CrawlerConfig,
    CrawlerStatus, BatchCrawlerRequest
)
from app.services.crawler_service import CrawlerService
from app.core.exceptions import NotFoundException, ValidationException, CrawlerException
from app.utils.logger import setup_logger

# 创建路由器
router = APIRouter()

# 初始化日志
logger = setup_logger(__name__)

# 依赖注入
def get_crawler_service() -> CrawlerService:
    """获取爬虫服务实例"""
    return CrawlerService()


@router.post("/crawl", response_model=CrawlerResponse, summary="单个URL爬取")
async def crawl_single_url(
    crawler_request: CrawlerRequest,
    background_tasks: BackgroundTasks,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    爬取单个URL
    
    支持的配置选项：
    - 自定义User-Agent
    - 设置请求头
    - 配置代理
    - 设置超时时间
    """
    try:
        logger.info(f"开始爬取URL: {crawler_request.url}")
        
        # 验证URL格式
        if not crawler_request.url.startswith(('http://', 'https://')):
            raise ValidationException("无效的URL格式")
        
        # 创建爬虫任务
        task_id = await crawler_service.create_crawl_task(crawler_request)
        
        # 如果是异步执行，添加到后台任务
        if crawler_request.async_mode:
            background_tasks.add_task(
                crawler_service.execute_crawl_task, task_id
            )
            return CrawlerResponse(
                task_id=task_id,
                status=CrawlerStatus.PENDING,
                message="爬虫任务已创建，正在后台执行"
            )
        else:
            # 同步执行
            result = await crawler_service.execute_crawl_task(task_id)
            return result
            
    except ValidationException as e:
        logger.error(f"爬虫请求验证失败: {e.detail}")
        raise HTTPException(status_code=422, detail=e.detail)
    except CrawlerException as e:
        logger.error(f"爬虫执行失败: {e.detail}")
        raise HTTPException(status_code=500, detail=e.detail)
    except Exception as e:
        logger.error(f"爬虫服务异常: {str(e)}")
        raise HTTPException(status_code=500, detail="爬虫服务异常")


@router.post("/batch-crawl", summary="批量URL爬取")
async def crawl_batch_urls(
    batch_request: BatchCrawlerRequest,
    background_tasks: BackgroundTasks,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    批量爬取多个URL
    
    支持：
    - 并发控制
    - 失败重试
    - 进度跟踪
    """
    try:
        logger.info(f"开始批量爬取，URL数量: {len(batch_request.urls)}")
        
        # 验证URL数量
        if len(batch_request.urls) > 100:
            raise ValidationException("单次批量爬取URL数量不能超过100个")
        
        # 创建批量爬虫任务
        batch_task_id = await crawler_service.create_batch_crawl_task(batch_request)
        
        # 添加到后台任务
        background_tasks.add_task(
            crawler_service.execute_batch_crawl_task, batch_task_id
        )
        
        return {
            "batch_task_id": batch_task_id,
            "message": f"批量爬虫任务已创建，共{len(batch_request.urls)}个URL",
            "status": "pending"
        }
        
    except ValidationException as e:
        logger.error(f"批量爬虫请求验证失败: {e.detail}")
        raise HTTPException(status_code=422, detail=e.detail)
    except Exception as e:
        logger.error(f"批量爬虫服务异常: {str(e)}")
        raise HTTPException(status_code=500, detail="批量爬虫服务异常")


@router.get("/status/{task_id}", summary="获取爬虫任务状态")
async def get_crawl_status(
    task_id: str = Path(..., description="任务ID"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """获取指定爬虫任务的执行状态"""
    try:
        logger.info(f"查询爬虫任务状态: {task_id}")
        
        status = await crawler_service.get_crawl_status(task_id)
        if not status:
            raise NotFoundException(f"爬虫任务未找到: {task_id}")
        
        return status
        
    except NotFoundException as e:
        logger.warning(f"爬虫任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"获取爬虫任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取爬虫任务状态失败")


@router.get("/result/{task_id}", summary="获取爬虫任务结果")
async def get_crawl_result(
    task_id: str = Path(..., description="任务ID"),
    format: str = Query("json", description="返回格式: json, html, text"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """获取指定爬虫任务的执行结果"""
    try:
        logger.info(f"获取爬虫任务结果: {task_id}")
        
        result = await crawler_service.get_crawl_result(task_id, format)
        if not result:
            raise NotFoundException(f"爬虫任务结果未找到: {task_id}")
        
        return result
        
    except NotFoundException as e:
        logger.warning(f"爬虫任务结果未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"获取爬虫任务结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取爬虫任务结果失败")


@router.delete("/task/{task_id}", summary="取消爬虫任务")
async def cancel_crawl_task(
    task_id: str = Path(..., description="任务ID"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """取消指定的爬虫任务"""
    try:
        logger.info(f"取消爬虫任务: {task_id}")
        
        success = await crawler_service.cancel_crawl_task(task_id)
        if not success:
            raise NotFoundException(f"爬虫任务未找到或无法取消: {task_id}")
        
        return {"message": "爬虫任务已取消", "task_id": task_id}
        
    except NotFoundException as e:
        logger.warning(f"爬虫任务未找到: {task_id}")
        raise HTTPException(status_code=404, detail=e.detail)
    except Exception as e:
        logger.error(f"取消爬虫任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="取消爬虫任务失败")


@router.get("/config", response_model=CrawlerConfig, summary="获取爬虫配置")
async def get_crawler_config(
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """获取当前爬虫的配置信息"""
    try:
        config = await crawler_service.get_crawler_config()
        return config
        
    except Exception as e:
        logger.error(f"获取爬虫配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取爬虫配置失败")


@router.put("/config", response_model=CrawlerConfig, summary="更新爬虫配置")
async def update_crawler_config(
    config: CrawlerConfig,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """更新爬虫的配置信息"""
    try:
        logger.info("更新爬虫配置")
        
        updated_config = await crawler_service.update_crawler_config(config)
        return updated_config
        
    except ValidationException as e:
        logger.error(f"爬虫配置验证失败: {e.detail}")
        raise HTTPException(status_code=422, detail=e.detail)
    except Exception as e:
        logger.error(f"更新爬虫配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新爬虫配置失败")


@router.get("/statistics", summary="获取爬虫统计信息")
async def get_crawler_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """获取爬虫的统计信息"""
    try:
        logger.info("获取爬虫统计信息")
        
        stats = await crawler_service.get_statistics(start_date, end_date)
        return stats
        
    except Exception as e:
        logger.error(f"获取爬虫统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取爬虫统计信息失败") 