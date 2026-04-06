"""
Analysis Orchestrator - 分析编排器
负责编排整个多 Agent 分析流程
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional
from .supervisor import SupervisorAgent
from .analysis_agent import create_agent, AGENT_REGISTRY
from .fusion_agent import FusionAgent
from services.finnhub_service import FinnhubService
from storage.settings import SettingsStore
from storage.portfolio import PortfolioStore
from config import config


class AnalysisOrchestrator:
    """分析编排器，负责协调多个 Agent 完成完整的投资分析流程"""

    def __init__(self, model_config: dict = None, agent_model_configs: dict = None):
        """
        初始化编排器

        Args:
            model_config: 通用模型配置字典（作为默认配置）
            agent_model_configs: Agent 级模型配置字典，key 为 agent 名称，value 为模型配置
        """
        self.model_config = model_config or {}
        self.agent_model_configs = agent_model_configs or {}

        # 初始化各 Agent，优先使用 Agent 级配置，无配置时使用通用配置
        self.supervisor = SupervisorAgent(self.agent_model_configs.get('supervisor', self.model_config))
        self.fusion_agent = FusionAgent(self.agent_model_configs.get('fusion', self.model_config))

        # 通过注册表创建 5 个分析 Agent
        self.analysis_agents = {
            key: create_agent(key, self.agent_model_configs.get(key, self.model_config))
            for key in AGENT_REGISTRY
        }
        
        # 初始化服务
        self.finnhub_service = FinnhubService(config.FINNHUB_API_KEY) if config.FINNHUB_API_KEY else None
        self.settings_store = SettingsStore(config.DATA_DIR)
        self.portfolio_store = PortfolioStore(config.DATA_DIR)
    
    async def analyze_ticker(
        self, 
        ticker: str, 
        user_settings: Dict[str, Any] = None,
        progress_callback: Optional[Callable[[str, str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        分析单个股票
        
        Args:
            ticker: 股票代码
            user_settings: 用户设置，包含：
                - investment_style: 投资风格
                - ticker_notes: ticker 专属笔记
                - skills: 已安装的技能列表
            progress_callback: 进度回调函数，参数为 (stage, message, progress)
        
        Returns:
            完整分析报告字典
        """
        # 获取用户设置
        if user_settings is None:
            user_settings = {}
        
        investment_style = user_settings.get('investment_style', '均衡型')
        ticker_notes = user_settings.get('ticker_notes', {})
        skills = user_settings.get('skills', [])
        agent_skills_map = user_settings.get('agent_skills', {})
        
        # 辅助函数：发送进度（支持可选的 agent_name 和 agent_content 参数）
        def emit_progress(stage: str, message: str, progress: float, agent_name: str = None, agent_content: str = None):
            if progress_callback:
                progress_callback(stage, message, progress, agent_name=agent_name, agent_content=agent_content)
        
        # 为各 Agent 安装对应的技能（按 agent 维度）
        all_agent_instances = {
            'supervisor': self.supervisor,
            'fusion': self.fusion_agent,
            **self.analysis_agents,
        }
        for agent_key, agent_instance in all_agent_instances.items():
            per_agent_skills = agent_skills_map.get(agent_key, {})
            for skill_name, skill_data in per_agent_skills.items():
                agent_instance.install_skill({
                    "name": skill_name,
                    **skill_data,
                })
        
        # 兼容旧的 skills 列表格式（仅安装到 custom_skill agent）
        custom_skill_agent = self.analysis_agents.get('custom_skill')
        if custom_skill_agent:
            for skill in skills:
                custom_skill_agent.install_skill(skill)
        
        # 步骤 1: Supervisor 拆解任务
        emit_progress("supervisor", "Supervisor 正在拆解分析任务...", 5.0)
        supervisor_input = {
            'tickers': [ticker],
            'investment_style': investment_style,
            'ticker_notes': ticker_notes
        }
        supervisor_output = await self.supervisor.run(supervisor_input)
        emit_progress("supervisor", "Supervisor 任务拆解完成", 15.0)
        
        # 步骤 2: 并行调用所有注册的分析 Agent
        # 获取数据（同步方法，不用 await）
        news_data = []
        fundamentals_data = {}
        technical_data = {}
        if self.finnhub_service:
            raw_news = self.finnhub_service.get_company_news(ticker)
            if isinstance(raw_news, dict) and raw_news.get("success"):
                news_data = raw_news.get("news", [])
            elif isinstance(raw_news, list):
                news_data = raw_news
            
            raw_fundamentals = self.finnhub_service.get_financials(ticker)
            if isinstance(raw_fundamentals, dict) and raw_fundamentals.get("success"):
                fundamentals_data = {"metric": raw_fundamentals}
            
            raw_technical = self.finnhub_service.get_technical_indicators(ticker)
            if isinstance(raw_technical, dict) and raw_technical.get("success"):
                technical_data = raw_technical
        sec_data = {}  # SEC 数据全部靠大模型分析
        
        # 内置 Agent 的专属输入数据
        # 对于 custom_skill，使用已安装到 agent.skills 中的技能列表
        custom_skill_agent = self.analysis_agents.get('custom_skill')
        installed_skills = custom_skill_agent.skills if custom_skill_agent else []
        
        builtin_agent_inputs = {
            'news': {'ticker': ticker, 'news_data': news_data, 'investment_style': investment_style},
            'sec': {'ticker': ticker, 'sec_data': sec_data, 'investment_style': investment_style},
            'fundamentals': {'ticker': ticker, 'fundamentals_data': fundamentals_data, 'investment_style': investment_style},
            'technical': {'ticker': ticker, 'technical_data': technical_data, 'investment_style': investment_style},
            'custom_skill': {'ticker': ticker, 'skills': installed_skills, 'investment_style': investment_style},
        }
        # 通用基础输入（用于自定义 Agent）
        base_input = {'ticker': ticker, 'investment_style': investment_style}
        
        # 动态构建 agent_key → (显示名, 输入数据) 映射
        agent_task_configs = {}
        for agent_key, agent_instance in self.analysis_agents.items():
            display_name = agent_instance.agent_config.description or agent_instance.name
            task_input = builtin_agent_inputs.get(agent_key, base_input)
            agent_task_configs[agent_key] = (display_name, task_input)
        
        total_agents = len(agent_task_configs)
        emit_progress("agents", f"正在并行执行 {total_agents} 个专项 Agent 分析...", 20.0)
        
        # 使用 asyncio.as_completed 风格：为每个 Agent 创建带名称的 task
        agent_outputs_dict = {}
        completed_count = 0
        total_agents = len(agent_task_configs)
        
        async def run_agent_with_name(agent_key: str, agent, input_data: dict):
            result = await agent.run(input_data)
            return agent_key, result
        
        tasks = [
            asyncio.create_task(run_agent_with_name(key, self.analysis_agents[key], task_input))
            for key, (_, task_input) in agent_task_configs.items()
        ]
        
        for coro in asyncio.as_completed(tasks):
            agent_key, result = await coro
            completed_count += 1
            # 使用 "{key}_agent" 格式保持与前端的兼容性
            output_key = f"{agent_key}_agent"
            agent_outputs_dict[output_key] = result.content
            display_name = agent_task_configs[agent_key][0]
            agent_progress = 20.0 + (50.0 * completed_count / total_agents)
            emit_progress(
                "agents",
                f"{display_name} 分析完成 ({completed_count}/{total_agents})",
                agent_progress,
                agent_name=output_key,
                agent_content=result.content
            )
        
        emit_progress("agents", "所有专项 Agent 分析完成", 70.0)
        
        # 步骤 3: Fusion Agent 融合结果
        emit_progress("fusion", "Fusion Agent 正在融合分析结果...", 75.0)
        fusion_input = {
            'ticker': ticker,
            'agent_outputs': agent_outputs_dict,
            'investment_style': investment_style,
            'ticker_note': ticker_notes.get(ticker, '')
        }
        fusion_output = await self.fusion_agent.run(fusion_input)
        emit_progress("fusion", "Fusion Agent 融合完成", 95.0)
        
        # 步骤 4: 返回完整分析报告
        full_report = {
            'ticker': ticker,
            'investment_style': investment_style,
            'supervisor_output': supervisor_output.content,
            'agent_outputs': agent_outputs_dict,
            'fusion_output': fusion_output.content,
            'metadata': {
                'timestamp': self._get_current_timestamp(),
                'data_sources': {
                    'news': len(news_data),
                    'sec': len(sec_data) if sec_data else 0,
                    'fundamentals': bool(fundamentals_data),
                    'technical': bool(technical_data)
                }
            }
        }
        
        return full_report
    
    async def analyze_portfolio(self, tickers: List[str], user_settings: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        批量分析多个股票
        
        Args:
            tickers: 股票代码列表
            user_settings: 用户设置
        
        Returns:
            分析报告列表
        """
        # 并行分析多个股票
        analysis_tasks = [
            self.analyze_ticker(ticker, user_settings)
            for ticker in tickers
        ]
        
        portfolio_reports = await asyncio.gather(*analysis_tasks)
        
        return portfolio_reports
    
    async def chat_with_agent(self, agent_name: str, message: str, model_config: dict = None) -> str:
        """
        与单个 Agent 聊天
        
        Args:
            agent_name: Agent 名称（supervisor/news/sec/fundamentals/technical/custom_skill/fusion）
            message: 用户消息
            model_config: 模型配置（可选，覆盖默认配置）
        
        Returns:
            Agent 的回复
        """
        # 获取对应的 Agent
        agent_map = {
            'supervisor': self.supervisor,
            'fusion': self.fusion_agent,
            **self.analysis_agents,
        }
        
        agent = agent_map.get(agent_name.lower())
        if agent is None:
            return f"未找到 Agent: {agent_name}。可用的 Agent: {', '.join(agent_map.keys())}"
        
        # 加载该 Agent 的已安装技能（从持久化存储中）
        try:
            settings = self.settings_store.load()
            agent_skills_map = settings.agent_skills or {}
            per_agent_skills = agent_skills_map.get(agent_name.lower(), {})
            for skill_name, skill_data in per_agent_skills.items():
                # 避免重复安装（检查是否已存在同名技能）
                existing_names = {s["name"] for s in agent.skills}
                if skill_name not in existing_names:
                    agent.install_skill({
                        "name": skill_name,
                        **skill_data,
                    })
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"加载 Agent 技能失败: {exc}")
        
        # 如果提供了特定的 model_config，临时更新
        if model_config:
            original_config = agent.model_config
            agent.model_config = model_config
        
        try:
            # 调用 Agent 的通用 chat 方法
            result = await agent.chat(message)
            return result.content
        finally:
            # 恢复原始配置
            if model_config:
                agent.model_config = original_config
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
