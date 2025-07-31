"""
搜索服务API
===========

提供基于智能体的搜索功能，包括：
- 智能搜索
- 语义搜索
- 结果排序和过滤
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from app.models.search import (
    SearchRequest, SearchResponse, SearchResult,
    SearchFilter, SearchSort
)
from app.services.crawler_service import CrawlerService
from app.core.exceptions import ValidationException
from app.utils.logger import setup_logger

# 创建路由器
router = APIRouter()

# 初始化日志
logger = setup_logger(__name__)

# 依赖注入
def get_crawler_service() -> CrawlerService:
    """获取爬虫服务实例"""
    return CrawlerService()


@router.post("/", response_model=SearchResponse, summary="智能搜索")
async def intelligent_search(
    search_request: SearchRequest,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    执行智能搜索
    
    功能特性：
    - 基于智能体的查询理解
    - 实时网页搜索
    - 结果智能排序
    - 内容摘要生成
    """
    try:
        logger.info(f"执行智能搜索: {search_request.query}")
        
        # 验证搜索查询
        if not search_request.query.strip():
            raise ValidationException("搜索查询不能为空")
        
        if len(search_request.query) > 500:
            raise ValidationException("搜索查询长度不能超过500字符")
        
        # 执行搜索
        search_results = await crawler_service.intelligent_search(search_request)
        
        return SearchResponse(
            query=search_request.query,
            results=search_results,
            total=len(search_results),
            search_time=search_results[0].search_time if search_results else 0,
            suggestions=await crawler_service.get_search_suggestions(search_request.query)
        )
        
    except ValidationException as e:
        logger.error(f"搜索请求验证失败: {e.detail}")
        raise HTTPException(status_code=422, detail=e.detail)
    except Exception as e:
        logger.error(f"智能搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail="智能搜索服务异常")


@router.get("/suggestions", summary="获取搜索建议")
async def get_search_suggestions(
    query: str = Query(..., description="搜索查询", min_length=1),
    limit: int = Query(10, ge=1, le=20, description="建议数量"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    获取搜索建议
    
    基于历史搜索和智能分析提供搜索建议
    """
    try:
        logger.info(f"获取搜索建议: {query}")
        
        suggestions = await crawler_service.get_search_suggestions(query, limit)
        
        return {
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取搜索建议失败")


@router.post("/semantic", response_model=SearchResponse, summary="语义搜索")
async def semantic_search(
    search_request: SearchRequest,
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    执行语义搜索
    
    使用向量相似度进行语义匹配搜索
    """
    try:
        logger.info(f"执行语义搜索: {search_request.query}")
        
        # 验证搜索请求
        if not search_request.query.strip():
            raise ValidationException("搜索查询不能为空")
        
        # 执行语义搜索
        search_results = await crawler_service.semantic_search(search_request)
        
        return SearchResponse(
            query=search_request.query,
            results=search_results,
            total=len(search_results),
            search_time=search_results[0].search_time if search_results else 0,
            search_type="semantic"
        )
        
    except ValidationException as e:
        logger.error(f"语义搜索请求验证失败: {e.detail}")
        raise HTTPException(status_code=422, detail=e.detail)
    except Exception as e:
        logger.error(f"语义搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail="语义搜索服务异常")


@router.get("/history", summary="获取搜索历史")
async def get_search_history(
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(20, ge=1, le=100, description="历史记录数量"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    获取搜索历史记录
    
    支持按用户ID过滤历史记录
    """
    try:
        logger.info(f"获取搜索历史: user_id={user_id}")
        
        history = await crawler_service.get_search_history(user_id, limit)
        
        return {
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"获取搜索历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取搜索历史失败")


@router.delete("/history", summary="清除搜索历史")
async def clear_search_history(
    user_id: Optional[str] = Query(None, description="用户ID，为空则清除所有"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """清除搜索历史记录"""
    try:
        logger.info(f"清除搜索历史: user_id={user_id}")
        
        count = await crawler_service.clear_search_history(user_id)
        
        return {
            "message": "搜索历史已清除",
            "cleared_count": count
        }
        
    except Exception as e:
        logger.error(f"清除搜索历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="清除搜索历史失败")


@router.get("/trending", summary="获取热门搜索")
async def get_trending_searches(
    limit: int = Query(10, ge=1, le=50, description="热门搜索数量"),
    time_range: str = Query("24h", description="时间范围: 1h, 24h, 7d, 30d"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    获取热门搜索词
    
    基于搜索频率和时间衰减计算热门度
    """
    try:
        logger.info(f"获取热门搜索: limit={limit}, time_range={time_range}")
        
        trending = await crawler_service.get_trending_searches(limit, time_range)
        
        return {
            "trending": trending,
            "time_range": time_range,
            "total": len(trending)
        }
        
    except Exception as e:
        logger.error(f"获取热门搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取热门搜索失败")


@router.post("/feedback", summary="搜索结果反馈")
async def submit_search_feedback(
    search_id: str,
    result_id: str,
    feedback_type: str = Query(..., description="反馈类型: helpful, not_helpful, spam"),
    crawler_service: CrawlerService = Depends(get_crawler_service)
):
    """
    提交搜索结果反馈
    
    用于改进搜索算法和结果质量
    """
    try:
        logger.info(f"提交搜索反馈: search_id={search_id}, result_id={result_id}")
        
        success = await crawler_service.submit_search_feedback(
            search_id, result_id, feedback_type
        )
        
        if success:
            return {"message": "反馈已提交，感谢您的反馈"}
        else:
            raise HTTPException(status_code=400, detail="反馈提交失败")
        
    except Exception as e:
        logger.error(f"提交搜索反馈失败: {str(e)}")
        raise HTTPException(status_code=500, detail="提交搜索反馈失败") 