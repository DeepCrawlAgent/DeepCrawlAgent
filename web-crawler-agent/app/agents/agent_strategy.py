"""
智能体策略
==========

定义智能体的执行策略和决策逻辑。
"""

from typing import Dict, Any, List
from enum import Enum

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AgentStrategy:
    """智能体策略类"""
    
    def __init__(self):
        """初始化策略"""
        self.strategies = {
            "conservative": {"risk_tolerance": 0.3, "exploration_rate": 0.2},
            "balanced": {"risk_tolerance": 0.5, "exploration_rate": 0.5},
            "aggressive": {"risk_tolerance": 0.8, "exploration_rate": 0.8}
        }
    
    def get_strategy(self, strategy_name: str = "balanced") -> Dict[str, Any]:
        """获取策略配置"""
        return self.strategies.get(strategy_name, self.strategies["balanced"]) 