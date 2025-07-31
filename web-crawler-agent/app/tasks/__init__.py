"""
Celery任务模块
==============

定义系统中的所有异步任务，包括：
- 爬虫相关任务
- 智能体相关任务
"""

from .crawler_tasks import CrawlerTask
from .agent_tasks import AgentTask 