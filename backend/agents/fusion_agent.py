"""
Fusion Agent - 高级投资决策融合专家
负责综合多个专业 Agent 的分析结果，通过平衡型融合逻辑，为用户提供可行动的投资建议
"""

from typing import Dict, Any
from .base import BaseAgent, AgentMessage
from .prompts import get_fusion_prompt


class FusionAgent(BaseAgent):
    """Fusion Agent - 高级投资决策融合专家"""
    
    def __init__(self, model_config: dict = None):
        system_prompt = get_fusion_prompt(
            investment_style="{investment_style}",
            ticker_note="{ticker_note}"
        )
        super().__init__(
            name="FusionAgent",
            system_prompt=system_prompt,
            model_config=model_config,
            prompt_key="fusion",
            format_params={
                "investment_style": "{investment_style}",
                "ticker_note": "{ticker_note}"
            },
        )
    
    async def run(self, input_data: Dict[str, Any]) -> AgentMessage:
        """
        执行 Fusion Agent 的主要逻辑

        Args:
            input_data: 包含以下字段的字典
                - ticker: 股票代码
                - agent_outputs: 各专项 Agent 的输出结果（字典）
                - investment_style: 用户投资风格
                - ticker_note: ticker 专属笔记

        Returns:
            AgentMessage: 包含融合分析报告的 AgentMessage
        """
        ticker = input_data.get('ticker', '')
        agent_outputs = input_data.get('agent_outputs', {})
        investment_style = input_data.get('investment_style', '均衡型')
        ticker_note = input_data.get('ticker_note', '')

        # 更新格式化参数
        self.update_format_params({
            "investment_style": investment_style,
            "ticker_note": ticker_note
        })

        # 现在 self.system_prompt 已经是格式化后的，不需要再调用 format 方法
        full_prompt = self.system_prompt
        
        # 构建各 Agent 输出摘要
        agent_outputs_summary = self._build_agent_outputs_summary(agent_outputs)
        
        user_input = f"""
请综合以下各专业 Agent 的分析结果，通过平衡型融合逻辑，为用户提供可行动的投资建议：

股票代码：{ticker}
用户投资风格：{investment_style}
Ticker 专属笔记：{ticker_note}

各 Agent 分析结果：
{agent_outputs_summary}

请按照平衡型融合逻辑进行：
1. 根据投资风格动态调整各 Agent 权重
2. 识别各 Agent 的共识点和分歧点
3. 综合评估风险（市场风险、公司风险、行业风险、政策风险等）
4. 给出可行动建议（强烈买入/买入/持有/观望/卖出/强烈卖出）
5. 提供具体的行动建议（入场策略、仓位建议、止损位、止盈位等）
6. 评估建议与用户投资风格的匹配度
7. 整合 ticker 专属笔记的影响

请以 JSON 格式输出融合分析报告，包含：
- fusion_summary: 融合总结
- agent_weights: 各 Agent 权重
- consensus_analysis: 共识分析（强共识、中等共识、分歧点）
- risk_assessment: 风险评估
- actionable_recommendations: 可行动建议
- investment_style_alignment: 投资风格匹配度
- ticker_specific_notes: Ticker 专属笔记整合
- disclaimer: 免责声明
"""
        
        # 调用模型适配层（异步，不阻塞事件循环）
        response = await self._acall_model(full_prompt, user_input)
        
        # 构建返回消息
        return AgentMessage(
            role=self.name,
            content=response,
            metadata={
                'ticker': ticker,
                'investment_style': investment_style,
                'agent_type': 'fusion',
                'fusion_style': 'balanced'
            }
        )
    
    def _build_agent_outputs_summary(self, agent_outputs: Dict[str, Any]) -> str:
        """构建各 Agent 输出摘要"""
        summary_parts = []
        
        # News Agent 输出
        if 'news_agent' in agent_outputs:
            summary_parts.append("=== News Agent (新闻分析) ===")
            summary_parts.append(agent_outputs['news_agent'])
            summary_parts.append("")
        
        # SEC Agent 输出
        if 'sec_agent' in agent_outputs:
            summary_parts.append("=== SEC Agent (SEC 分析) ===")
            summary_parts.append(agent_outputs['sec_agent'])
            summary_parts.append("")
        
        # Fundamentals Agent 输出
        if 'fundamentals_agent' in agent_outputs:
            summary_parts.append("=== Fundamentals Agent (基本面分析) ===")
            summary_parts.append(agent_outputs['fundamentals_agent'])
            summary_parts.append("")
        
        # Technical Agent 输出
        if 'technical_agent' in agent_outputs:
            summary_parts.append("=== Technical Agent (技术分析) ===")
            summary_parts.append(agent_outputs['technical_agent'])
            summary_parts.append("")
        
        # Custom Skill Agent 输出
        if 'custom_skill_agent' in agent_outputs:
            summary_parts.append("=== Custom Skill Agent (自定义技能分析) ===")
            summary_parts.append(agent_outputs['custom_skill_agent'])
            summary_parts.append("")
        
        return "\n".join(summary_parts) if summary_parts else "暂无 Agent 输出"
