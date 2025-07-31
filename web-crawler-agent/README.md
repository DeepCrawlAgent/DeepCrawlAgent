# Web Crawler Agent

基于smolagents和webcrawl4ai的智能网络爬虫系统，可为领域大模型采集训练数据，也可充当搜索引擎为用户提供服务。

## 🚀 功能特性

- **智能爬虫**: 基于webcrawl4ai的AI增强网页爬取
- **智能体集成**: 基于smolagents的智能决策和内容分析
- **分布式任务**: 使用Celery进行异步任务处理
- **RESTful API**: 完整的FastAPI接口
- **实时搜索**: 智能搜索和语义搜索功能
- **数据存储**: 支持多种存储后端
- **监控日志**: 完善的日志和监控系统

## 🏗️ 系统架构

```
web-crawler-agent/
├── app/                    # 主应用
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   ├── tasks/             # Celery任务
│   ├── agents/            # 智能体模块
│   ├── crawlers/          # 爬虫模块
│   ├── storage/           # 存储模块
│   └── utils/             # 工具函数
├── workers/               # Celery Worker
├── tests/                 # 测试代码
└── scripts/              # 部署脚本
```

## 🛠️ 安装部署

### 环境要求

- Python 3.8+
- Redis 6.0+
- PostgreSQL 12+ (可选)

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd web-crawler-agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和Redis连接
```

4. **初始化数据库**
```bash
python scripts/setup_db.py
```

5. **启动服务**

启动API服务:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动Celery Worker:
```bash
celery -A workers.celery_app worker --loglevel=info
```

启动Celery监控:
```bash
celery -A workers.celery_app flower
```

### Docker部署

```bash
docker-compose up -d
```

## 📚 API文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要接口

#### 任务管理
- `POST /api/v1/tasks/` - 创建任务
- `GET /api/v1/tasks/` - 获取任务列表
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `POST /api/v1/tasks/{task_id}/start` - 启动任务

#### 爬虫控制
- `POST /api/v1/crawler/crawl` - 单URL爬取
- `POST /api/v1/crawler/batch-crawl` - 批量爬取
- `GET /api/v1/crawler/status/{task_id}` - 获取爬取状态

#### 智能搜索
- `POST /api/v1/search/` - 智能搜索
- `POST /api/v1/search/semantic` - 语义搜索
- `GET /api/v1/search/suggestions` - 搜索建议

## 🔧 开发指南

### 为后端工程师

1. **爬虫模块开发**
   - 实现 `app/crawlers/web_crawler4ai.py` 中的实际webcrawl4ai集成
   - 安装和配置webcrawl4ai库
   - 自定义爬虫策略和规则

2. **存储模块扩展**
   - 实现 `app/storage/` 中的实际数据库操作
   - 添加新的存储后端支持
   - 优化数据库模型和索引

### 为算法工程师

1. **智能体模块开发**
   - 实现 `app/agents/smol_agent.py` 中的实际smolagents集成
   - 开发智能体策略和决策逻辑
   - 集成大语言模型

2. **搜索算法优化**
   - 实现语义搜索算法
   - 优化搜索结果排序
   - 添加内容分析功能

## 🧪 测试

运行测试:
```bash
pytest tests/
```

运行覆盖率测试:
```bash
pytest --cov=app tests/
```

## 📊 监控

- **健康检查**: `GET /health`
- **指标监控**: Celery Flower (http://localhost:5555)
- **日志查看**: `logs/` 目录

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如有问题，请：
1. 查看文档和FAQ
2. 搜索已知问题
3. 创建新的Issue

## 🗺️ 路线图

- [ ] 支持更多爬虫引擎
- [ ] 增强智能体功能
- [ ] 添加Web UI界面
- [ ] 支持插件系统
- [ ] 云原生部署支持 