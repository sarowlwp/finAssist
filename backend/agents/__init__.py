"""
Agents 模块 - 多 Agent 协作系统
包含所有 Agent 类和编排器
"""

from .base import BaseAgent, AgentMessage
from .supervisor import SupervisorAgent
from .analysis_agent import AnalysisAgent, create_agent, AGENT_REGISTRY
from .fusion_agent import FusionAgent
from .orchestrator import AnalysisOrchestrator
from .prompts import (
    SUPERVISOR_SYSTEM_PROMPT,
    NEWS_AGENT_SYSTEM_PROMPT,
    SEC_AGENT_SYSTEM_PROMPT,
    FUNDAMENTALS_AGENT_SYSTEM_PROMPT,
    TECHNICAL_AGENT_SYSTEM_PROMPT,
    CUSTOM_SKILL_AGENT_SYSTEM_PROMPT,
    FUSION_AGENT_SYSTEM_PROMPT,
    get_supervisor_prompt,
    get_fusion_prompt
)

# 向后兼容：保留旧类名作为别名
NewsAgent = lambda model_config=None: create_agent("news", model_config)
SECAgent = lambda model_config=None: create_agent("sec", model_config)
FundamentalsAgent = lambda model_config=None: create_agent("fundamentals", model_config)
TechnicalAgent = lambda model_config=None: create_agent("technical", model_config)
CustomSkillAgent = lambda model_config=None: create_agent("custom_skill", model_config)

__all__ = [
    # 基类
    'BaseAgent',
    'AgentMessage',
    
    # 通用分析 Agent
    'AnalysisAgent',
    'create_agent',
    'AGENT_REGISTRY',
    
    # 特殊 Agent
    'SupervisorAgent',
    'FusionAgent',
    
    # 向后兼容的旧类名
    'NewsAgent',
    'SECAgent',
    'FundamentalsAgent',
    'TechnicalAgent',
    'CustomSkillAgent',
    
    # 编排器
    'AnalysisOrchestrator',
    
    # Prompt 模板
    'SUPERVISOR_SYSTEM_PROMPT',
    'NEWS_AGENT_SYSTEM_PROMPT',
    'SEC_AGENT_SYSTEM_PROMPT',
    'FUNDAMENTALS_AGENT_SYSTEM_PROMPT',
    'TECHNICAL_AGENT_SYSTEM_PROMPT',
    'CUSTOM_SKILL_AGENT_SYSTEM_PROMPT',
    'FUSION_AGENT_SYSTEM_PROMPT',
    'get_supervisor_prompt',
    'get_fusion_prompt',
]
