"""
Celery应用配置
==============

配置Celery应用实例，用于异步任务处理。
"""

from celery import Celery
from kombu import Queue

from app.core.config import settings

# 创建Celery应用实例
celery_app = Celery(
    "web-crawler-agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.crawler_tasks",
        "app.tasks.agent_tasks"
    ]
)

# Celery配置
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    
    # 任务路由配置
    task_routes={
        "app.tasks.crawler_tasks.*": {"queue": "crawler"},
        "app.tasks.agent_tasks.*": {"queue": "agent"}
    },
    
    # 队列配置
    task_default_queue="default",
    task_queues=(
        Queue("default"),
        Queue("crawler", routing_key="crawler"),
        Queue("agent", routing_key="agent"),
        Queue("high_priority", routing_key="high_priority"),
    ),
    
    # Worker配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # 结果过期时间
    result_expires=3600,  # 1小时
    
    # 任务软时间限制
    task_soft_time_limit=300,  # 5分钟
    task_time_limit=600,       # 10分钟
    
    # 重试配置
    task_default_retry_delay=60,
    task_max_retries=3,
)


# 自动发现任务
celery_app.autodiscover_tasks()


if __name__ == "__main__":
    celery_app.start() 