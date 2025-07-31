#!/usr/bin/env python3
"""
数据库初始化脚本
================

初始化数据库表结构和基础数据。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage.database import init_database, create_tables
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")
        
        # 初始化数据库连接
        init_database()
        
        # 创建数据库表
        create_tables()
        
        logger.info("数据库初始化完成!")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 