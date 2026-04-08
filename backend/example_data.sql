-- 金融分析助手应用示例数据
-- 该文件包含应用所需的示例数据，用于开发和测试

-- ===========================================================
-- 示例持仓数据 (portfolio_holdings)
-- ===========================================================

INSERT OR IGNORE INTO portfolio_holdings (ticker, quantity, cost_price, note, created_at, updated_at)
VALUES
    ('AAPL', 500, 150.00, '苹果公司股票', datetime('now'), datetime('now')),
    ('NVDA', 5, 800.00, '英伟达 - AI 赛道', datetime('now'), datetime('now')),
    ('TSLA', 3, 200.00, '特斯拉 - 电动车', datetime('now'), datetime('now')),
    ('INTC', 1111, 111.00, '英特尔 - 芯片制造', datetime('now'), datetime('now')),
    ('MSFT', 200, 350.00, '微软 - 云计算', datetime('now'), datetime('now')),
    ('AMZN', 100, 150.00, '亚马逊 - 电商', datetime('now'), datetime('now'));


-- ===========================================================
-- 示例分析报告数据 (analysis_reports)
-- ===========================================================

-- 已完成的分析报告
INSERT OR IGNORE INTO analysis_reports (
    report_id, ticker, company_name, status, current_price, change_percent, fusion_summary, created_at
)
VALUES
    (
        '7f9c5b2a-1234-4567-890a-bcdef123456',
        'AAPL',
        '苹果公司',
        'completed',
        175.50,
        2.35,
        '苹果公司在最近一个季度的财务表现强劲，营收和利润均超出预期。iPhone 16系列的销售表现出色，尤其是高端机型的需求旺盛。公司的服务业务继续保持稳定增长，包括Apple Music、iCloud和App Store。整体来看，苹果公司的基本面健康，值得长期持有。',
        datetime('now', '-1 day')
    ),
    (
        '8d3e7f1b-2345-6789-0abc-def12345678',
        'NVDA',
        '英伟达公司',
        'completed',
        850.20,
        5.12,
        '英伟达在AI芯片市场的主导地位进一步巩固，H100和H200芯片的需求持续强劲。数据中心业务增长显著，游戏业务也有所恢复。公司的软件生态系统不断完善，CUDA平台的优势明显。长期来看，AI芯片市场的增长潜力巨大。',
        datetime('now', '-2 days')
    ),
    (
        '9e5f8g3c-3456-7890-1bcd-ef123456789',
        'TSLA',
        '特斯拉公司',
        'completed',
        225.80,
        -1.25,
        '特斯拉在电动车市场的份额略有下降，但Cybertruck的交付开始加速。公司的利润率有所改善，成本控制措施效果显著。超级充电桩网络的扩张继续进行，储能业务增长强劲。整体来看，特斯拉的长期前景仍然看好。',
        datetime('now', '-3 days')
    );


-- ===========================================================
-- 示例 Agent 报告数据 (agent_reports)
-- ===========================================================

-- Apple 分析报告的 Agent 报告
INSERT OR IGNORE INTO agent_reports (report_id, agent_name, agent_content, created_at)
VALUES
    (
        '7f9c5b2a-1234-4567-890a-bcdef123456',
        'news_agent',
        '【公司新闻】苹果公司宣布将在9月10日举办秋季发布会，预计将发布iPhone 16系列和新款Apple Watch。分析师普遍预期iPhone 16的销量将同比增长15-20%。

【行业动态】全球智能手机市场在第二季度出现复苏迹象，苹果公司的市场份额提升至18.5%，位居第二。中国市场的需求正在逐步恢复。

【风险提示】苹果公司可能面临中美贸易摩擦的影响，以及高通公司的专利诉讼风险。',
        datetime('now', '-1 day')
    ),
    (
        '7f9c5b2a-1234-4567-890a-bcdef123456',
        'financial_agent',
        '【财务数据】苹果公司Q2营收为908亿美元，同比增长5%；净利润为230亿美元，同比增长11%。每股收益为1.53美元，超出预期的1.43美元。

【关键指标】毛利率为45.3%，同比上升0.8个百分点；运营现金流为286亿美元，同比增长8%。

【财务分析】苹果公司的财务表现稳健，各业务板块均有增长。iPhone业务增长7%，Mac业务增长12%，服务业务增长6%。',
        datetime('now', '-1 day')
    ),
    (
        '7f9c5b2a-1234-4567-890a-bcdef123456',
        'technical_agent',
        '【技术分析】苹果公司股票在过去30天上涨了8.5%，短期趋势向上。目前价格位于50日均线和200日均线上方，技术面看好。

【关键指标】相对强弱指数(RSI)为68，接近超买区域；MACD指标显示正动能增强。成交量较平均水平增加25%。

【支撑阻力】短期支撑位在170美元，阻力位在180美元。',
        datetime('now', '-1 day')
    );


-- NVDA 分析报告的 Agent 报告
INSERT OR IGNORE INTO agent_reports (report_id, agent_name, agent_content, created_at)
VALUES
    (
        '8d3e7f1b-2345-6789-0abc-def12345678',
        'news_agent',
        '【公司新闻】英伟达宣布推出新款H200 GPU，专为AI大语言模型设计。该芯片的内存带宽提升了50%，预计将在2026年第一季度开始出货。',
        datetime('now', '-2 days')
    ),
    (
        '8d3e7f1b-2345-6789-0abc-def12345678',
        'financial_agent',
        '【财务数据】英伟达Q1营收为248亿美元，同比增长26%；净利润为120亿美元，同比增长33%。每股收益为4.98美元，超出预期的4.50美元。',
        datetime('now', '-2 days')
    ),
    (
        '8d3e7f1b-2345-6789-0abc-def12345678',
        'technical_agent',
        '【技术分析】英伟达股票在过去30天上涨了15.2%，强劲的上升趋势。价格突破了历史高点，技术面非常强劲。',
        datetime('now', '-2 days')
    );


-- TSLA 分析报告的 Agent 报告
INSERT OR IGNORE INTO agent_reports (report_id, agent_name, agent_content, created_at)
VALUES
    (
        '9e5f8g3c-3456-7890-1bcd-ef123456789',
        'news_agent',
        '【公司新闻】特斯拉宣布Cybertruck的周产量已突破1000辆，预计将在今年底实现全面量产。同时，公司正在开发下一代电动车平台。',
        datetime('now', '-3 days')
    ),
    (
        '9e5f8g3c-3456-7890-1bcd-ef123456789',
        'financial_agent',
        '【财务数据】特斯拉Q1营收为251亿美元，同比下降9%；净利润为11亿美元，同比下降55%。每股收益为0.22美元，低于预期的0.45美元。',
        datetime('now', '-3 days')
    ),
    (
        '9e5f8g3c-3456-7890-1bcd-ef123456789',
        'technical_agent',
        '【技术分析】特斯拉股票在过去30天下跌了3.2%，短期趋势向下。价格位于50日均线上方但接近200日均线。',
        datetime('now', '-3 days')
    );


-- ===========================================================
-- 示例分析任务数据 (analysis_tasks)
-- ===========================================================

INSERT OR IGNORE INTO analysis_tasks (
    task_id, ticker, company_name, status, progress, progress_message, progress_stage, report_id, created_at, updated_at
)
VALUES
    (
        'task_7f9c5b2a-1234-4567-890a',
        'MSFT',
        '微软公司',
        'pending',
        0,
        '等待分析任务开始',
        'pending',
        NULL,
        datetime('now'),
        datetime('now')
    );


-- ===========================================================
-- 示例 Finnhub 缓存数据 (finnhub_cache)
-- ===========================================================

-- 注意：Finnhub 缓存数据通常由系统自动生成，
-- 这里只提供一个示例以演示数据结构

INSERT OR IGNORE INTO finnhub_cache (
    cache_key, data_type, ticker, data, created_at, expires_at
)
VALUES
    (
        'quote:AAPL',
        'quote',
        'AAPL',
        '{
            "c": 175.50,
            "h": 176.20,
            "l": 174.80,
            "o": 175.00,
            "pc": 172.20
        }',
        datetime('now'),
        datetime('now', '+5 minutes')
    );


-- ===========================================================
-- 初始化完成
-- ===========================================================

-- 查询验证数据是否已正确导入
-- SELECT COUNT(*) FROM portfolio_holdings;
-- SELECT COUNT(*) FROM analysis_reports;
-- SELECT COUNT(*) FROM agent_reports;
-- SELECT COUNT(*) FROM analysis_tasks;

-- 打印导入成功的消息
-- SELECT '数据库初始化完成！' as message;
