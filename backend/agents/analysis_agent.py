"""
AnalysisAgent - 通用分析 Agent
将 NewsAgent、SECAgent、FundamentalsAgent、TechnicalAgent、CustomSkillAgent
统一抽象为一个可配置的执行类，通过 AgentConfig 区分行为。
"""

from typing import Dict, Any, Callable, Optional
from .base import BaseAgent, AgentMessage


# ============================================================
# 数据摘要构建函数（从各 Agent 的 _build_xxx_summary 提取）
# ============================================================

def build_news_summary(input_data: Dict[str, Any]) -> str:
    """构建新闻数据摘要"""
    news_data = input_data.get('news_data', [])
    lines = [
        f"- {news.get('headline', '')} ({news.get('source', '')})"
        for news in news_data[:10]
    ]
    news_summary = "\n".join(lines)
    return f"最新新闻（共{len(news_data)}条）：\n{news_summary}"


def build_sec_summary(input_data: Dict[str, Any]) -> str:
    """构建 SEC 数据摘要"""
    sec_data = input_data.get('sec_data', {})
    summary_parts = []

    if 'form4' in sec_data:
        form4_data = sec_data['form4']
        summary_parts.append(f"Form 4 (内部人交易): {len(form4_data)} 条记录")
        if form4_data:
            recent_trade = form4_data[0]
            summary_parts.append(
                f"  最新交易: {recent_trade.get('transaction_type', 'N/A')} "
                f"- {recent_trade.get('shares', 'N/A')} 股"
            )

    if 'form13f' in sec_data:
        form13f_data = sec_data['form13f']
        summary_parts.append(f"Form 13F (机构持仓): {len(form13f_data)} 条记录")
        if form13f_data:
            top_holder = form13f_data[0]
            summary_parts.append(f"  最大持仓机构: {top_holder.get('manager_name', 'N/A')}")

    if 'financial_filings' in sec_data:
        filings = sec_data['financial_filings']
        summary_parts.append(f"财务报告文件: {len(filings)} 条记录")
        if filings:
            latest_filing = filings[0]
            summary_parts.append(
                f"  最新报告: {latest_filing.get('form', 'N/A')} "
                f"- {latest_filing.get('filed_date', 'N/A')}"
            )

    if 'form8k' in sec_data:
        form8k_data = sec_data['form8k']
        summary_parts.append(f"Form 8-K (重大事件): {len(form8k_data)} 条记录")
        if form8k_data:
            recent_event = form8k_data[0]
            summary_parts.append(
                f"  最新事件: {recent_event.get('category', 'N/A')} "
                f"- {recent_event.get('filed_date', 'N/A')}"
            )

    return "\n".join(summary_parts) if summary_parts else "暂无 SEC 数据"


def build_fundamentals_summary(input_data: Dict[str, Any]) -> str:
    """构建基本面数据摘要"""
    fundamentals_data = input_data.get('fundamentals_data', {})
    summary_parts = []

    if 'metric' in fundamentals_data:
        metric = fundamentals_data['metric']

        summary_parts.append("基本指标:")
        summary_parts.append(f"  市值: {metric.get('marketCapitalization', 'N/A')}")
        summary_parts.append(f"  当前价格: {metric.get('currentPrice', 'N/A')}")
        summary_parts.append(f"  52周最高: {metric.get('52WeekHigh', 'N/A')}")
        summary_parts.append(f"  52周最低: {metric.get('52WeekLow', 'N/A')}")

        summary_parts.append("\n估值指标:")
        summary_parts.append(f"  P/E Ratio: {metric.get('peBasicExclExtraTTM', 'N/A')}")
        summary_parts.append(f"  P/B Ratio: {metric.get('pbQuarterly', 'N/A')}")
        summary_parts.append(f"  P/S Ratio: {metric.get('psTTM', 'N/A')}")
        summary_parts.append(f"  EV/EBITDA: {metric.get('evToEbitdaTTM', 'N/A')}")

        summary_parts.append("\n盈利能力:")
        summary_parts.append(f"  Gross Margin TTM: {metric.get('grossMarginTTM', 'N/A')}")
        summary_parts.append(f"  Operating Margin TTM: {metric.get('operatingMarginTTM', 'N/A')}")
        summary_parts.append(f"  Net Margin TTM: {metric.get('netMarginTTM', 'N/A')}")
        summary_parts.append(f"  ROE TTM: {metric.get('roeTTM', 'N/A')}")
        summary_parts.append(f"  ROA TTM: {metric.get('roaTTM', 'N/A')}")

        summary_parts.append("\n成长性:")
        summary_parts.append(f"  Revenue Growth (YoY): {metric.get('revenueGrowth', 'N/A')}")
        summary_parts.append(f"  EPS Growth (YoY): {metric.get('epsGrowth', 'N/A')}")

        summary_parts.append("\n财务健康度:")
        summary_parts.append(f"  Debt-to-Equity: {metric.get('totalDebtToEquityQuarterly', 'N/A')}")
        summary_parts.append(f"  Current Ratio: {metric.get('currentRatioQuarterly', 'N/A')}")
        summary_parts.append(f"  Quick Ratio: {metric.get('quickRatioQuarterly', 'N/A')}")
        summary_parts.append(f"  Interest Coverage: {metric.get('interestCoverageTTM', 'N/A')}")

    return "\n".join(summary_parts) if summary_parts else "暂无基本面数据"


def build_technical_summary(input_data: Dict[str, Any]) -> str:
    """构建技术指标数据摘要"""
    technical_data = input_data.get('technical_data', {})
    summary_parts = []

    if 'sma' in technical_data:
        sma = technical_data['sma']
        summary_parts.append("移动平均线 (SMA):")
        summary_parts.append(f"  SMA20: {sma.get('sma20', 'N/A')}")
        summary_parts.append(f"  SMA50: {sma.get('sma50', 'N/A')}")
        summary_parts.append(f"  SMA200: {sma.get('sma200', 'N/A')}")

    if 'ema' in technical_data:
        ema = technical_data['ema']
        summary_parts.append("\n指数移动平均线 (EMA):")
        summary_parts.append(f"  EMA12: {ema.get('ema12', 'N/A')}")
        summary_parts.append(f"  EMA26: {ema.get('ema26', 'N/A')}")

    if 'macd' in technical_data:
        macd = technical_data['macd']
        summary_parts.append("\nMACD:")
        summary_parts.append(f"  MACD: {macd.get('macd', 'N/A')}")
        summary_parts.append(f"  Signal: {macd.get('signal', 'N/A')}")
        summary_parts.append(f"  Histogram: {macd.get('histogram', 'N/A')}")

    if 'rsi' in technical_data:
        rsi = technical_data['rsi']
        summary_parts.append("\nRSI (相对强弱指标):")
        summary_parts.append(f"  RSI14: {rsi.get('rsi14', 'N/A')}")
        summary_parts.append(f"  RSI (超买线: 70, 超卖线: 30)")

    if 'bbands' in technical_data:
        bbands = technical_data['bbands']
        summary_parts.append("\n布林带 (Bollinger Bands):")
        summary_parts.append(f"  上轨: {bbands.get('upper_band', 'N/A')}")
        summary_parts.append(f"  中轨: {bbands.get('middle_band', 'N/A')}")
        summary_parts.append(f"  下轨: {bbands.get('lower_band', 'N/A')}")

    if 'volume' in technical_data:
        volume = technical_data['volume']
        summary_parts.append("\n成交量:")
        summary_parts.append(f"  当前成交量: {volume.get('current_volume', 'N/A')}")
        summary_parts.append(f"  平均成交量: {volume.get('avg_volume', 'N/A')}")

    if 'adx' in technical_data:
        adx = technical_data['adx']
        summary_parts.append("\nADX (平均方向指数):")
        summary_parts.append(f"  ADX: {adx.get('adx', 'N/A')}")
        summary_parts.append(f"  +DI: {adx.get('plus_di', 'N/A')}")
        summary_parts.append(f"  -DI: {adx.get('minus_di', 'N/A')}")

    if 'stochastic' in technical_data:
        stochastic = technical_data['stochastic']
        summary_parts.append("\n随机指标 (Stochastic):")
        summary_parts.append(f"  %K: {stochastic.get('k_percent', 'N/A')}")
        summary_parts.append(f"  %D: {stochastic.get('d_percent', 'N/A')}")

    return "\n".join(summary_parts) if summary_parts else "暂无技术指标数据"


def build_skills_summary(input_data: Dict[str, Any]) -> str:
    """构建技能列表摘要"""
    skills = input_data.get('skills', [])
    summary_parts = []
    for index, skill in enumerate(skills, 1):
        summary_parts.append(f"{index}. {skill.get('name', 'N/A')}")
        summary_parts.append(f"   描述: {skill.get('description', 'N/A')}")
        if skill.get('prompt_injection'):
            summary_parts.append(f"   使用指南: {skill.get('prompt_injection', 'N/A')}")
    return "\n".join(summary_parts) if summary_parts else "无已安装技能"


def build_generic_summary(input_data: Dict[str, Any]) -> str:
    """
    通用数据摘要构建函数，用于用户自定义 Agent。
    将 input_data 中除 ticker/investment_style 外的所有数据格式化输出。
    """
    import json
    excluded_keys = {'ticker', 'investment_style'}
    extra_data = {k: v for k, v in input_data.items() if k not in excluded_keys}
    if not extra_data:
        return "无额外数据"
    return json.dumps(extra_data, ensure_ascii=False, indent=2, default=str)


# ============================================================
# User Input 模板
# ============================================================

NEWS_USER_INPUT_TEMPLATE = """
请分析以下股票的最新新闻对投资的影响：

股票代码：{ticker}
用户投资风格：{investment_style}

{data_summary}

请按照以下维度进行分析：
1. 关键新闻摘要（3-5条最重要新闻）
2. 情绪分析（整体情绪、情绪评分、置信度）
3. 影响评估（短期影响、长期影响、价格影响估算）
4. 关键风险点
5. 投资机会

请以 JSON 格式输出分析报告。
"""

SEC_USER_INPUT_TEMPLATE = """
请分析以下股票的 SEC 文件信息：

股票代码：{ticker}
用户投资风格：{investment_style}

SEC 文件信息：
{data_summary}

请按照以下维度进行分析：
1. 关键文件变化摘要
2. 内部人交易信号（近期活动、交易模式、信号强度、交易情绪）
3. 合规风险（风险等级、风险因素、监管关注点）
4. 公司治理评估（治理评分、优势、劣势）
5. 重大事件（如有）
6. 机构活动（机构持仓变化、知名机构动向）

请以 JSON 格式输出分析报告。
"""

FUNDAMENTALS_USER_INPUT_TEMPLATE = """
请分析以下股票的基本面情况：

股票代码：{ticker}
用户投资风格：{investment_style}

基本面数据：
{data_summary}

请按照以下维度进行分析：
1. 估值分析（估值指标、估值评估、估值理由）
2. 盈利能力分析（盈利指标、盈利趋势、盈利评分）
3. 成长性分析（成长指标、成长轨迹、成长评分）
4. 财务健康度（健康指标、健康评估、健康评分）
5. 业务质量（竞争优势、护城河强度、质量评分）
6. 综合评分
7. 投资论点（3-5条）
8. 关键关注点

请以 JSON 格式输出分析报告。
"""

TECHNICAL_USER_INPUT_TEMPLATE = """
请分析以下股票的技术面情况：

股票代码：{ticker}
用户投资风格：{investment_style}

技术指标数据：
{data_summary}

请按照以下维度进行分析：
1. 趋势分析（当前趋势、趋势强度、趋势确认信号）
2. 关键价位（支撑位、阻力位、当前位置）
3. 技术指标汇总（趋势指标、动量指标、成交量指标、波动率指标）
4. 交易信号（买入信号、卖出信号、信号强度）
5. 技术评分
6. 形态识别（如有）
7. 风险评估（止损位、风险收益比）

请以 JSON 格式输出分析报告。
"""

CUSTOM_SKILL_USER_INPUT_TEMPLATE = """
请使用以下已安装的技能分析股票：

股票代码：{ticker}
用户投资风格：{investment_style}

已安装的技能：
{data_summary}

请按照以下步骤进行：
1. 对于每个技能，按照其描述和 prompt_injection 执行分析
2. 将各技能的输出结果整合到统一的结构中
3. 识别技能之间的冲突点（如有）
4. 汇总各技能的关键发现，提供自定义洞察

请以 JSON 格式输出分析报告，包含：
- installed_skills: 已安装技能列表
- skill_analysis_results: 各技能的分析结果
- skill_conflicts: 技能冲突点（如有）
- custom_insights: 自定义洞察
"""


# ============================================================
# Agent 配置注册表
# ============================================================

class AgentConfig:
    """Agent 配置，描述一个分析 Agent 的所有可变部分"""

    def __init__(
        self,
        name: str,
        prompt_key: str,
        default_prompt_attr: str,
        data_builder: Callable[[Dict[str, Any]], str],
        user_input_template: str,
        agent_type: str,
        description: str = "",
        builtin: bool = True,
        extra_metadata_keys: Optional[list] = None,
        skip_when_empty_key: Optional[str] = None,
        empty_report_builder: Optional[Callable[[Dict[str, Any]], AgentMessage]] = None,
    ):
        """
        Args:
            name: Agent 显示名称，如 "NewsAgent"
            prompt_key: 用于从 prompts/ 目录加载 md 文件的 key，如 "news"
            default_prompt_attr: prompts.py 中默认 prompt 常量的属性名，如 "NEWS_AGENT_SYSTEM_PROMPT"
            data_builder: 数据摘要构建函数，接收 input_data 返回摘要字符串
            user_input_template: user_input 模板字符串，包含 {ticker}, {investment_style}, {data_summary} 占位符
            agent_type: metadata 中的 agent_type 值，如 "news"
            description: Agent 描述信息
            builtin: 是否为内置 Agent（内置 Agent 不可删除）
            extra_metadata_keys: 需要额外从 input_data 提取到 metadata 的 key 列表
            skip_when_empty_key: 如果指定，当 input_data 中该 key 对应的值为空时跳过模型调用
            empty_report_builder: 当 skip_when_empty_key 触发时，用于构建空报告的函数
        """
        self.name = name
        self.prompt_key = prompt_key
        self.default_prompt_attr = default_prompt_attr
        self.data_builder = data_builder
        self.user_input_template = user_input_template
        self.agent_type = agent_type
        self.description = description
        self.builtin = builtin
        self.extra_metadata_keys = extra_metadata_keys or []
        self.skip_when_empty_key = skip_when_empty_key
        self.empty_report_builder = empty_report_builder


def _build_custom_skill_empty_report(input_data: Dict[str, Any]) -> AgentMessage:
    """CustomSkillAgent 无技能时的空报告"""
    ticker = input_data.get('ticker', '')
    investment_style = input_data.get('investment_style', '均衡型')
    empty_report = {
        'installed_skills': [],
        'message': '当前未安装任何自定义技能，建议从技能市场安装相关分析技能以获得更多维度分析',
        'suggestions': [
            'ESG 分析技能：评估公司的环境、社会和治理表现',
            '期权链分析技能：分析期权持仓和隐含波动率',
            '行业对比技能：与同行业公司进行横向对比',
            '分红分析技能：分析分红历史和可持续性'
        ]
    }
    return AgentMessage(
        role="CustomSkillAgent",
        content=str(empty_report),
        metadata={
            'ticker': ticker,
            'investment_style': investment_style,
            'agent_type': 'custom_skill',
            'has_skills': False
        }
    )


# 导入默认 prompt 常量
from .prompts import (
    NEWS_AGENT_SYSTEM_PROMPT,
    SEC_AGENT_SYSTEM_PROMPT,
    FUNDAMENTALS_AGENT_SYSTEM_PROMPT,
    TECHNICAL_AGENT_SYSTEM_PROMPT,
    CUSTOM_SKILL_AGENT_SYSTEM_PROMPT,
)

# Agent 配置注册表：key 与 orchestrator 中使用的 agent_key 一致
AGENT_REGISTRY: Dict[str, AgentConfig] = {
    "news": AgentConfig(
        name="NewsAgent",
        prompt_key="news",
        default_prompt_attr="NEWS_AGENT_SYSTEM_PROMPT",
        data_builder=build_news_summary,
        user_input_template=NEWS_USER_INPUT_TEMPLATE,
        agent_type="news",
        description="News Agent - 专门分析新闻和市场情绪",
        builtin=True,
        extra_metadata_keys=["news_count"],
    ),
    "sec": AgentConfig(
        name="SECAgent",
        prompt_key="sec",
        default_prompt_attr="SEC_AGENT_SYSTEM_PROMPT",
        data_builder=build_sec_summary,
        user_input_template=SEC_USER_INPUT_TEMPLATE,
        agent_type="sec",
        description="SEC Agent - 分析 SEC 文件和监管信息",
        builtin=True,
    ),
    "fundamentals": AgentConfig(
        name="FundamentalsAgent",
        prompt_key="fundamentals",
        default_prompt_attr="FUNDAMENTALS_AGENT_SYSTEM_PROMPT",
        data_builder=build_fundamentals_summary,
        user_input_template=FUNDAMENTALS_USER_INPUT_TEMPLATE,
        agent_type="fundamentals",
        description="Fundamentals Agent - 分析基本面和财务数据",
        builtin=True,
    ),
    "technical": AgentConfig(
        name="TechnicalAgent",
        prompt_key="technical",
        default_prompt_attr="TECHNICAL_AGENT_SYSTEM_PROMPT",
        data_builder=build_technical_summary,
        user_input_template=TECHNICAL_USER_INPUT_TEMPLATE,
        agent_type="technical",
        description="Technical Agent - 分析技术指标和趋势",
        builtin=True,
    ),
    "custom_skill": AgentConfig(
        name="CustomSkillAgent",
        prompt_key="custom_skill",
        default_prompt_attr="CUSTOM_SKILL_AGENT_SYSTEM_PROMPT",
        data_builder=build_skills_summary,
        user_input_template=CUSTOM_SKILL_USER_INPUT_TEMPLATE,
        agent_type="custom_skill",
        description="Custom Skill Agent - 执行自定义技能",
        builtin=True,
        skip_when_empty_key="skills",
        empty_report_builder=_build_custom_skill_empty_report,
    ),
}

# 默认 prompt 常量映射（用于按名称查找）
_DEFAULT_PROMPTS: Dict[str, str] = {
    "NEWS_AGENT_SYSTEM_PROMPT": NEWS_AGENT_SYSTEM_PROMPT,
    "SEC_AGENT_SYSTEM_PROMPT": SEC_AGENT_SYSTEM_PROMPT,
    "FUNDAMENTALS_AGENT_SYSTEM_PROMPT": FUNDAMENTALS_AGENT_SYSTEM_PROMPT,
    "TECHNICAL_AGENT_SYSTEM_PROMPT": TECHNICAL_AGENT_SYSTEM_PROMPT,
    "CUSTOM_SKILL_AGENT_SYSTEM_PROMPT": CUSTOM_SKILL_AGENT_SYSTEM_PROMPT,
}


# ============================================================
# 通用分析 Agent
# ============================================================

class AnalysisAgent(BaseAgent):
    """
    通用分析 Agent，通过 AgentConfig 配置来区分不同类型的分析行为。
    替代原来的 NewsAgent、SECAgent、FundamentalsAgent、TechnicalAgent、CustomSkillAgent。
    """

    def __init__(self, config: AgentConfig, model_config: dict = None):
        """
        初始化通用分析 Agent

        Args:
            config: Agent 配置
            model_config: 模型配置字典
        """
        self.agent_config = config
        default_prompt = _DEFAULT_PROMPTS.get(config.default_prompt_attr, "")

        super().__init__(
            name=config.name,
            system_prompt=default_prompt,
            model_config=model_config,
            prompt_key=config.prompt_key,
        )

    async def run(self, input_data: Dict[str, Any]) -> AgentMessage:
        """
        执行分析 Agent 的主要逻辑

        Args:
            input_data: 包含 ticker、investment_style 及领域数据的字典

        Returns:
            AgentMessage: 包含分析报告的消息
        """
        config = self.agent_config
        ticker = input_data.get('ticker', '')
        investment_style = input_data.get('investment_style', '均衡型')

        # 检查是否需要跳过（如 CustomSkillAgent 无技能时）
        if config.skip_when_empty_key:
            skip_data = input_data.get(config.skip_when_empty_key, [])
            if not skip_data and config.empty_report_builder:
                return config.empty_report_builder(input_data)

        # 构建数据摘要
        data_summary = config.data_builder(input_data)

        # 构建 user_input
        user_input = config.user_input_template.format(
            ticker=ticker,
            investment_style=investment_style,
            data_summary=data_summary,
        )

        # 获取完整 prompt 并调用模型
        full_prompt = self.get_full_prompt()
        response = await self._acall_model(full_prompt, user_input)

        # 构建 metadata
        metadata = {
            'ticker': ticker,
            'investment_style': investment_style,
            'agent_type': config.agent_type,
        }
        # 添加额外的 metadata
        for key in config.extra_metadata_keys:
            if key == "news_count":
                metadata[key] = len(input_data.get('news_data', []))
            elif key in input_data:
                metadata[key] = input_data[key]

        if config.agent_type == "custom_skill":
            skills = input_data.get('skills', [])
            metadata['has_skills'] = bool(skills)
            metadata['skill_count'] = len(skills)

        return AgentMessage(
            role=self.name,
            content=response,
            metadata=metadata,
        )


def create_agent(agent_key: str, model_config: dict = None) -> AnalysisAgent:
    """
    工厂函数：根据 agent_key 创建对应的 AnalysisAgent 实例

    Args:
        agent_key: Agent 标识名（news / sec / fundamentals / technical / custom_skill 或自定义 key）
        model_config: 模型配置

    Returns:
        AnalysisAgent 实例

    Raises:
        ValueError: 未知的 agent_key
    """
    config = AGENT_REGISTRY.get(agent_key)
    if config is None:
        available_keys = ", ".join(AGENT_REGISTRY.keys())
        raise ValueError(f"未知的 agent_key: {agent_key}，可用的 key: {available_keys}")
    return AnalysisAgent(config, model_config)


# ============================================================
# 内置 Agent key 集合（不可删除）
# ============================================================

BUILTIN_AGENT_KEYS = frozenset(
    key for key, cfg in AGENT_REGISTRY.items() if cfg.builtin
)

# 用于用户自定义 Agent 的通用 user_input 模板
GENERIC_USER_INPUT_TEMPLATE = """
请分析以下股票：

股票代码：{ticker}
用户投资风格：{investment_style}

相关数据：
{data_summary}

请以 JSON 格式输出分析报告。
"""


def register_agent(
    agent_key: str,
    name: str,
    description: str,
    system_prompt: str,
    user_input_template: str = "",
) -> AgentConfig:
    """
    动态注册一个新的自定义 Agent 到 AGENT_REGISTRY。

    Args:
        agent_key: Agent 唯一标识（不能与已有 key 冲突）
        name: Agent 显示名称
        description: Agent 描述
        system_prompt: Agent 的 system prompt
        user_input_template: user_input 模板（可选，为空时使用通用模板）

    Returns:
        创建的 AgentConfig

    Raises:
        ValueError: agent_key 已存在
    """
    if agent_key in AGENT_REGISTRY:
        raise ValueError(f"agent_key '{agent_key}' 已存在，请使用其他名称")

    template = user_input_template.strip() if user_input_template else GENERIC_USER_INPUT_TEMPLATE

    config = AgentConfig(
        name=name,
        prompt_key=agent_key,
        default_prompt_attr="",
        data_builder=build_generic_summary,
        user_input_template=template,
        agent_type=agent_key,
        description=description,
        builtin=False,
    )

    # 将自定义 prompt 注入到 _DEFAULT_PROMPTS 中，供 AnalysisAgent.__init__ 使用
    prompt_attr_key = f"_CUSTOM_{agent_key.upper()}_PROMPT"
    _DEFAULT_PROMPTS[prompt_attr_key] = system_prompt
    config.default_prompt_attr = prompt_attr_key

    AGENT_REGISTRY[agent_key] = config
    return config


def unregister_agent(agent_key: str) -> None:
    """
    从 AGENT_REGISTRY 中移除一个自定义 Agent。

    Args:
        agent_key: 要移除的 Agent 标识

    Raises:
        ValueError: agent_key 不存在或为内置 Agent
    """
    if agent_key not in AGENT_REGISTRY:
        raise ValueError(f"agent_key '{agent_key}' 不存在")

    if agent_key in BUILTIN_AGENT_KEYS:
        raise ValueError(f"内置 Agent '{agent_key}' 不可删除")

    config = AGENT_REGISTRY.pop(agent_key)

    # 清理 _DEFAULT_PROMPTS 中的自定义 prompt
    if config.default_prompt_attr in _DEFAULT_PROMPTS:
        del _DEFAULT_PROMPTS[config.default_prompt_attr]


def load_custom_agents_from_settings(settings_store) -> None:
    """
    从持久化存储中加载用户自定义 Agent 并注册到 AGENT_REGISTRY。
    应在应用启动时调用。

    Args:
        settings_store: SettingsStore 实例
    """
    try:
        settings = settings_store.load()
        custom_agents = settings.custom_agents or {}
        for agent_key, agent_data in custom_agents.items():
            if agent_key not in AGENT_REGISTRY:
                register_agent(
                    agent_key=agent_key,
                    name=agent_data.get("name", agent_key),
                    description=agent_data.get("description", ""),
                    system_prompt=agent_data.get("system_prompt", ""),
                    user_input_template=agent_data.get("user_input_template", ""),
                )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(f"加载自定义 Agent 失败: {exc}")
