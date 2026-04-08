# 数据库初始化说明

本项目使用 SQLite 作为数据库，提供了以下初始化工具：

## 文件说明

### 1. `init_db.py` - 数据库初始化脚本
- 自动创建数据库表结构
- 导入示例数据
- 提供命令行接口
- 支持重置数据库功能

### 2. `example_data.sql` - 示例数据 SQL 文件
- 包含示例持仓数据
- 包含示例分析报告数据
- 包含示例分析任务数据
- 包含示例 Finnhub 缓存数据

## 使用方法

### 方法一：自动初始化（推荐）

项目启动时会自动执行数据库初始化。在 `main.py` 的 `startup_event` 中：
```python
# 初始化数据库
from database import Base, engine
Base.metadata.create_all(bind=engine)
```

### 方法二：手动执行脚本

#### 1. 初始化数据库
```bash
cd backend
python init_db.py
```

#### 2. 重置数据库（删除所有数据并重新初始化）
```bash
cd backend
python init_db.py reset
```

#### 3. 仅创建示例持仓数据
```bash
cd backend
python init_db.py sample
```

### 方法三：直接使用 SQL 文件

如果需要直接执行 SQL 文件：
```bash
sqlite3 data/finance_assistant.db < example_data.sql
```

## 数据库表结构

### 核心表

1. **portfolio_holdings** - 用户持仓数据
   - 存储用户的股票持仓信息
   - 字段：id, ticker, quantity, cost_price, note, created_at, updated_at

2. **analysis_reports** - 分析报告主表
   - 存储完整分析报告的元数据和汇总信息
   - 字段：report_id, ticker, company_name, status, current_price, change_percent, fusion_summary, created_at

3. **agent_reports** - Agent 报告子表
   - 存储各个分析 Agent 生成的详细报告
   - 字段：id, report_id, agent_name, agent_content, created_at

4. **analysis_tasks** - 分析任务表
   - 存储分析任务的状态和元数据
   - 字段：task_id, ticker, company_name, status, progress, progress_message, progress_stage, report_id, error_message, created_at, updated_at

5. **finnhub_cache** - Finnhub 数据缓存表
   - 存储 Finnhub API 响应的缓存数据
   - 字段：id, cache_key, data_type, ticker, data, created_at, expires_at

## 示例数据说明

### 示例持仓数据
包含以下股票：
- AAPL - 苹果公司
- NVDA - 英伟达公司
- TSLA - 特斯拉公司
- INTC - 英特尔公司
- MSFT - 微软公司
- AMZN - 亚马逊公司

### 示例分析报告
包含 3 个已完成的分析报告：
- AAPL - 苹果公司分析报告（1天前）
- NVDA - 英伟达公司分析报告（2天前）
- TSLA - 特斯拉公司分析报告（3天前）

### 示例分析任务
包含 1 个待处理的分析任务：
- MSFT - 微软公司分析任务

## 开发和测试

### 重置测试数据
```bash
# 重置数据库到初始状态
python init_db.py reset
```

### 验证数据
```bash
# 查看所有持仓数据
sqlite3 data/finance_assistant.db "SELECT * FROM portfolio_holdings;"

# 查看分析报告数量
sqlite3 data/finance_assistant.db "SELECT COUNT(*) FROM analysis_reports;"

# 查看 Agent 报告数量
sqlite3 data/finance_assistant.db "SELECT COUNT(*) FROM agent_reports;"
```

## 注意事项

1. 数据库文件位置：`backend/data/finance_assistant.db`
2. 首次启动时会自动创建数据库文件
3. 示例数据文件位置：`backend/example_data.sql`
4. 如果 `example_data.sql` 文件不存在，会自动创建默认的持仓数据
5. 数据库初始化脚本支持多次执行，会自动处理重复数据

## 故障排除

### 常见问题

1. **数据库文件权限问题**
   ```bash
   # 确保 data 目录有写入权限
   chmod 755 data
   ```

2. **SQLite 数据库损坏**
   ```bash
   # 删除损坏的数据库文件，系统会自动重新创建
   rm data/finance_assistant.db
   python init_db.py
   ```

3. **示例数据导入失败**
   ```bash
   # 检查 SQL 文件是否存在
   ls -la example_data.sql

   # 检查 SQL 文件内容
   cat example_data.sql
   ```

# 数据库操作指南

## 基本查询操作

### 查询所有持仓数据
```sql
SELECT * FROM portfolio_holdings;
```

### 查询指定股票的持仓
```sql
SELECT * FROM portfolio_holdings WHERE ticker = 'AAPL';
```

### 查询分析报告
```sql
SELECT * FROM analysis_reports ORDER BY created_at DESC;
```

### 查询 Agent 报告
```sql
SELECT * FROM agent_reports WHERE report_id = '7f9c5b2a-1234-4567-890a-bcdef123456';
```

## 高级查询操作

### 查询最近 7 天的分析报告
```sql
SELECT * FROM analysis_reports 
WHERE created_at > datetime('now', '-7 days')
ORDER BY created_at DESC;
```

### 查询待处理的分析任务
```sql
SELECT * FROM analysis_tasks WHERE status = 'pending';
```

### 查询 Finnhub 缓存数据
```sql
SELECT * FROM finnhub_cache WHERE data_type = 'quote';
```

## 数据备份和恢复

### 备份数据库
```bash
cp data/finance_assistant.db data/finance_assistant.db.backup
```

### 恢复数据库
```bash
cp data/finance_assistant.db.backup data/finance_assistant.db
```

### 定期备份建议
```bash
# 每日备份
0 2 * * * cp /path/to/backend/data/finance_assistant.db /path/to/backup/finance_assistant_$(date +\%Y\%m\%d).db
```
