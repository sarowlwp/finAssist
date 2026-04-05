"""
Supervisor Agent - 投资分析总控专家
负责协调多个专业分析 Agent 完成对股票的全面分析
"""

from typing import Dict, Any
from .base import BaseAgent, AgentMessage
from .prompts import get_supervisor_prompt


class SupervisorAgent(BaseAgent):
    """Supervisor Agent - 投资分析总控专家"""
    
    def __init__(self, model_config: dict = None):
        system_prompt = get_supervisor_prompt(
            investment_style="{investment_style}",
            ticker_note="{ticker_note}"
        )
        super().__init__(
            name="Supervisor",
            system_prompt=system_prompt,
            model_config=model_config,
            prompt_key="supervisor",
            format_params={
                "investment_style": "{investment_style}",
                "ticker_note": "{ticker_note}"
            },
        )
    
    async def run(self, input_data: Dict[str, Any]) -> AgentMessage:
        """
        执行 Supervisor Agent 的主要逻辑

        Args:
            input_data: 包含以下字段的字典
                - tickers: 股票代码列表
                - investment_style: 用户投资风格（保守型/成长型/价值型/均衡型）
                - ticker_notes: 各股票的专属笔记（字典，ticker -> note）

        Returns:
            AgentMessage: 包含任务分配方案的 AgentMessage
        """
        tickers = input_data.get('tickers', [])
        investment_style = input_data.get('investment_style', '均衡型')
        ticker_notes = input_data.get('ticker_notes', {})

        # 更新格式化参数
        self.update_format_params({
            "investment_style": investment_style,
            "ticker_note": ticker_notes.get(tickers[0] if tickers else '', '无专属笔记')
        })

        # 现在 self.system_prompt 已经是格式化后的，不需要再调用 format 方法
        full_prompt = self.system_prompt
        
        # 构建用户输入
        user_input = f"""
请为以下股票制定分析任务分配方案：

股票代码：{', '.join(tickers)}
投资风格：{investment_style}
专属笔记：{ticker_notes}

请按照以下步骤进行：
1. 根据投资风格，确定各专项 Agent 的优先级和权重
2. 为每个 Agent 分配具体的分析任务
3. 给出分析优先级排序
4. 指出风险关注重点

请以 JSON 格式输出任务分配方案。
"""
        
        # 调用模型适配层（异步，不阻塞事件循环）
        response = await self._acall_model(full_prompt, user_input)
        
        # 构建返回消息
        return AgentMessage(
            role=self.name,
            content=response,
            metadata={
                'tickers': tickers,
                'investment_style': investment_style,
                'agent_type': 'supervisor'
            }
        )
