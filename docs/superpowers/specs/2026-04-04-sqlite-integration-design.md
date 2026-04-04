# SQLite 集成设计文档

## 概述

本设计文档描述了如何在金融助理应用中引入 SQLite 数据库，以实现以下功能：

1. **Finnhub 数据缓存**：为 Finnhub API 响应提供类型化的小时级缓存，加速页面加载
2. **分析报告存储**：将分析报告和 Agent 输出存储到 SQLite 中，支持查阅历史记录
3. **灵活扩展**：架构设计支持未来添加新的 Agent 类型，无需修改数据库 schema

## 架构设计

### 1. 数据库架构

#### 表结构

**finnhub_cache** - Finnhub 数据缓存表
```sql
CREATE TABLE finnhub_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    data JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL
);

CREATE INDEX idx_finnhub_cache_key ON finnhub_cache(cache_key);
CREATE INDEX idx_finnhub_cache_type ON finnhub_cache(data_type);
CREATE INDEX idx_finnhub_cache_ticker ON finnhub_cache(ticker);
```

**analysis_reports** - 分析报告主表
```sql
CREATE TABLE analysis_reports (
    report_id VARCHAR(36) PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    current_price DECIMAL(15, 4) NOT NULL,
    change_percent DECIMAL(10, 4) NOT NULL,
    fusion_summary TEXT,
    FOREIGN KEY (ticker) REFERENCES tickers(ticker)
);

CREATE INDEX idx_analysis_reports_ticker ON analysis_reports(ticker);
```

**agent_reports** - Agent 报告明细表（支持无限扩展）
```sql
CREATE TABLE agent_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id VARCHAR(36) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    agent_content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES analysis_reports(report_id)
);

CREATE INDEX idx_agent_reports_report_id ON agent_reports(report_id);
CREATE INDEX idx_agent_reports_agent_name ON agent_reports(agent_name);
```

#### 缓存配置

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| quote | 5 分钟 | 实时报价，更新频繁 |
| profile | 24 小时 | 公司概况，基本不变化 |
| financials | 12 小时 | 财务数据，每日更新 |
| news | 1 小时 | 公司新闻，频繁更新 |
| technical | 4 小时 | 技术指标，每日几次更新 |

### 2. 架构组件

#### database.py - 数据库连接管理
- SQLAlchemy 连接和会话管理
- 数据库初始化和配置
- 依赖注入支持

#### models.py - 数据模型
- FinnhubCache：缓存数据模型
- AnalysisReport：分析报告主模型
- AgentReport：Agent 报告明细模型

#### services/finnhub_cache_service.py - Finnhub 缓存服务
- 缓存 CRUD 操作
- 类型化 TTL 管理
- 过期缓存清理

#### services/analysis_report_repository.py - 分析报告仓库
- 报告 CRUD 操作
- Agent 报告管理
- 查询接口

#### 集成到现有代码

**FinnhubService 更新**
- 添加缓存参数 `use_cache`（默认 True）
- 分析时传入 `use_cache=False` 避免使用缓存

**AnalysisStore 更新**
- 内部使用 AnalysisReportRepository
- 保持现有接口不变

**Dependencies 更新**
- 添加 SQLAlchemy Session 依赖注入
- 添加 AnalysisReportRepository 依赖注入

## 实现步骤

### 1. 安装依赖

```bash
pip install sqlalchemy
```

### 2. 创建核心文件

- `backend/database.py` - 数据库连接管理
- `backend/models.py` - SQLAlchemy 数据模型
- `backend/services/finnhub_cache_service.py` - 缓存服务
- `backend/services/analysis_report_repository.py` - 报告仓库

### 3. 更新现有文件

- `backend/config.py` - 添加 SQLite 配置
- `backend/dependencies.py` - 注入依赖
- `backend/services/finnhub_service.py` - 添加缓存逻辑
- `backend/storage/analysis.py` - 使用 SQLAlchemy 存储
- `backend/routers/analysis.py` - 注入新依赖

### 4. 初始化和测试

- 更新 `main.py` 启动时初始化数据库
- 运行现有测试确保功能正常
- 测试缓存功能
- 测试历史报告查询

## 测试策略

### 单元测试

```python
# 测试 Finnhub 缓存
def test_cache_service():
    db = get_test_db()
    cache_service = FinnhubCacheService(db)
    
    # 测试缓存保存
    test_data = {"test": "value"}
    cache_service.set_cache("quote", "AAPL", test_data)
    
    # 测试缓存查询
    cached_data = cache_service.get_cache("quote", "AAPL")
    assert cached_data == test_data
    
    # 测试缓存过期
    expired_data = {"expired": "data"}
    cache_service.set_cache("quote", "TSLA", expired_data)
    db.query(FinnhubCache).filter_by(ticker="TSLA").update({
        "expires_at": datetime.now() - timedelta(hours=1)
    })
    
    expired_cached = cache_service.get_cache("quote", "TSLA")
    assert expired_cached is None

# 测试分析报告存储
def test_analysis_repository():
    db = get_test_db()
    repo = AnalysisReportRepository(db)
    
    report_id = str(uuid.uuid4())
    
    # 测试报告创建
    report = repo.create_report(
        report_id=report_id,
        ticker="AAPL",
        company_name="Apple Inc.",
        current_price=150.0,
        change_percent=1.5,
        status="completed"
    )
    
    assert repo.get_report(report_id) is not None
    assert report.ticker == "AAPL"
    
    # 测试 Agent 报告存储
    repo.add_agent_report(report_id, "news_agent", "test content")
    agent_reports = repo.get_agent_reports(report_id)
    assert len(agent_reports) == 1
```

### 集成测试

```python
def test_finnhub_service_with_cache():
    db = get_test_db()
    service = FinnhubService("test_key", db=db)
    
    # 第一次调用不使用缓存
    result1 = service.get_quote("AAPL", use_cache=False)
    
    # 第二次调用使用缓存
    result2 = service.get_quote("AAPL", use_cache=True)
    
    # 检查是否是同一数据（测试缓存命中）
    assert result1 == result2
```

### E2E 测试

```python
# 测试历史报告查询
test("should display analysis reports history", async ({ page }) => {
    // 登录和导航
    await login(page)
    await page.click('[data-testid="history-link"]')
    
    // 验证报告列表显示
    const reports = await page.$$('[data-testid="analysis-report-item"]')
    expect(reports.length).toBeGreaterThan(0)
})

# 测试报告详情
test("should display analysis report details", async ({ page }) => {
    await login(page)
    await page.click('[data-testid="history-link"]')
    
    // 点击第一个报告
    await page.click('[data-testid="analysis-report-item"]:first-child')
    
    // 验证报告详情
    await expect(page.locator('[data-testid="report-summary"]')).toBeVisible()
    await expect(page.locator('[data-testid="agent-reports"]')).toBeVisible()
})
```

## 部署和监控

### 部署注意事项

- SQLite 数据库位于 `data/finance_assistant.db`（与其他数据一起）
- 确保部署过程中数据库文件权限正确
- 初始化时会自动创建表

### 性能优化

- 定期清理过期缓存（应用启动时自动清理）
- 优化查询索引
- 对于大量报告的场景，可以考虑分页查询

### 监控

- 添加数据库性能指标监控
- 监控缓存命中率
- 监控报告存储和查询延迟

## 未来扩展

### 支持更多 Agent 类型

```python
# 添加新 Agent 只需更新 AgentReport
agent_report = AgentReport(
    report_id=report_id,
    agent_name="new_agent_type",
    agent_content=content
)
db.add(agent_report)
```

### 缓存策略调整

```python
# 修改 CACHE_TTL_CONFIG
CACHE_TTL_CONFIG = {
    "quote": timedelta(minutes=5),
    "profile": timedelta(hours=24),
    "financials": timedelta(hours=12),
    "news": timedelta(minutes=30),  # 调整新闻缓存时间
    "technical": timedelta(hours=4)
}
```

### 数据库迁移

使用 Alembic 进行数据库 schema 管理。

## 总结

本设计实现了：

✅ **高性能缓存**：按数据类型设置合理的 TTL，提高页面加载速度
✅ **灵活存储**：Agent 报告独立存储，支持无限扩展
✅ **数据一致性**：分析时不使用缓存，确保分析准确性
✅ **历史记录**：完整的报告存储和查询系统
✅ **代码质量**：保持现有接口不变，使用 SQLAlchemy ORM 提高代码可维护性

使用 SQLAlchemy ORM 提供了以下优势：

✅ **类型安全**：编译时类型检查
✅ **可测试性**：易于 mock 和隔离测试
✅ **可扩展性**：ORM 抽象层便于未来数据库迁移
✅ **代码质量**：避免原始 SQL 查询带来的安全问题
