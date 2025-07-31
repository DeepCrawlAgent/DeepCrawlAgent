"""
FastAPI 应用主入口
================

这是整个Web Crawler Agent系统的FastAPI应用入口点。
配置了所有的路由、中间件和应用设置。
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn

from app.core.config import settings
from app.core.exceptions import CustomException
from app.api.v1 import tasks, crawler, search
from app.utils.logger import setup_logger

# 初始化日志
logger = setup_logger(__name__)

def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        FastAPI: 配置好的FastAPI应用
    """
    app = FastAPI(
        title="Web Crawler Agent API",
        description="基于智能体的网络爬虫系统API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 添加中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """添加请求处理时间头"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # 添加异常处理
    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        """自定义异常处理器"""
        logger.error(f"Custom exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )
    
    # 注册路由
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任务管理"])
    app.include_router(crawler.router, prefix="/api/v1/crawler", tags=["爬虫控制"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["搜索服务"])
    
    @app.get("/", tags=["根路径"])
    async def root():
        """根路径健康检查"""
        return {"message": "Web Crawler Agent API is running!", "version": "1.0.0"}
    
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        """系统健康检查"""
        return {"status": "healthy", "timestamp": time.time()}
    
    return app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    ) 