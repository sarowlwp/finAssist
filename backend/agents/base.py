from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json
import logging
import asyncio
import concurrent.futures
import re

# 配置日志
logger = logging.getLogger(__name__)

# 共享线程池，避免每次调用都创建新线程池
_model_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)

# prompt md 文件存放目录
PROMPTS_DIR = Path(__file__).parent / "prompts"


def parse_prompt_md(file_path: Path) -> Tuple[str, List[str]]:
    """
    解析 prompt markdown 文件，提取 frontmatter 中的 skills 和正文内容。

    Frontmatter 格式示例：
    ---
    skills:
      - stock_analysis
      - market_sentiment
    ---
    正文 prompt 内容...

    Args:
        file_path: prompt md 文件路径

    Returns:
        (prompt_content, skill_names) 元组
    """
    content = file_path.read_text(encoding="utf-8")
    skill_names: List[str] = []
    prompt_body = content

    # 解析 YAML frontmatter（--- 包裹的部分）
    frontmatter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = frontmatter_pattern.match(content)
    if match:
        frontmatter_text = match.group(1)
        prompt_body = content[match.end():]

        # 简易解析 skills 列表，避免引入 pyyaml 依赖
        # 支持两种格式：
        #   skills: []
        #   skills:
        #     - skill_name_1
        #     - skill_name_2
        in_skills_block = False
        for line in frontmatter_text.splitlines():
            stripped = line.strip()

            # 检测 "skills: []" 单行空数组
            if re.match(r"^skills:\s*\[\s*\]\s*$", stripped):
                in_skills_block = False
                continue

            # 检测 "skills: [a, b, c]" 单行内联数组
            inline_match = re.match(r"^skills:\s*\[(.+)\]\s*$", stripped)
            if inline_match:
                items = inline_match.group(1).split(",")
                skill_names.extend(item.strip().strip("'\"") for item in items if item.strip())
                in_skills_block = False
                continue

            # 检测 "skills:" 多行块开始
            if re.match(r"^skills:\s*$", stripped):
                in_skills_block = True
                continue

            # 在 skills 块中解析 "- skill_name"
            if in_skills_block:
                item_match = re.match(r"^-\s+(.+)$", stripped)
                if item_match:
                    skill_names.append(item_match.group(1).strip().strip("'\""))
                elif stripped and not stripped.startswith("#"):
                    # 遇到非列表项、非注释行，结束 skills 块
                    in_skills_block = False

    return prompt_body.strip(), skill_names


def load_prompt_from_file(agent_key: str) -> Optional[Tuple[str, List[str]]]:
    """
    尝试从文件系统加载 Agent 的 prompt md 文件。

    Args:
        agent_key: Agent 标识名（如 news, sec, supervisor 等）

    Returns:
        (prompt_content, skill_names) 元组，文件不存在时返回 None
    """
    prompt_file = PROMPTS_DIR / f"{agent_key}.md"
    if not prompt_file.exists():
        logger.debug(f"Prompt 文件不存在: {prompt_file}，将使用代码默认 prompt")
        return None

    try:
        prompt_content, skill_names = parse_prompt_md(prompt_file)
        logger.info(f"从文件加载 prompt: {prompt_file}，skills: {skill_names}")
        return prompt_content, skill_names
    except Exception as exc:
        logger.warning(f"解析 prompt 文件失败: {prompt_file}，错误: {exc}，将使用代码默认 prompt")
        return None


class AgentMessage(BaseModel):
    """Agent 消息基类"""
    role: str  # agent name
    content: str
    metadata: dict = {}

class BaseAgent:
    """Agent 基类，提供所有 Agent 的通用功能"""
    
    def __init__(self, name: str, system_prompt: str, model_config: dict = None,
                 prompt_key: str = None, format_params: dict = None):
        """
        初始化 Agent。

        Args:
            name: Agent 显示名称
            system_prompt: 代码中的默认 system prompt（fallback）
            model_config: 模型配置
            prompt_key: 用于从文件系统加载 prompt 的标识名（如 "news"、"sec"）。
                        如果提供，会优先从 prompts/{prompt_key}.md 加载 prompt，
                        并自动安装 md frontmatter 中声明的 skills。
            format_params: 用于格式化 prompt 的参数字典（可选）。
                          如果提供，会在加载 prompt 后使用这些参数进行格式化。
        """
        self.name = name
        self.model_config = model_config or {}
        logger.info(f"[{name}] 初始化，收到的 model_config: {self.model_config}")
        self.skills: list[dict] = []
        self.prompt_key = prompt_key
        self._unformatted_system_prompt = None  # 保存未格式化的 prompt
        self._format_params = format_params or {}  # 保存格式化参数

        # 优先从文件系统加载 prompt
        loaded = load_prompt_from_file(prompt_key) if prompt_key else None
        if loaded:
            self._unformatted_system_prompt = loaded[0]
            # 自动安装 frontmatter 中声明的 skills
            for skill_name in loaded[1]:
                self.install_skill({
                    "name": skill_name,
                    "description": f"从 prompt 文件声明的技能: {skill_name}",
                    "prompt_injection": "",
                    "source": "prompt_file",
                })
        else:
            self._unformatted_system_prompt = system_prompt

        # 格式化 prompt
        self._format_system_prompt()    
    def _format_system_prompt(self):
        """格式化系统提示"""
        try:
            self.system_prompt = self._unformatted_system_prompt.format(**self._format_params)
        except Exception as e:
            logger.warning(f"格式化系统 prompt 失败: {str(e)}")
            self.system_prompt = self._unformatted_system_prompt

    def update_format_params(self, new_params: dict):
        """更新格式化参数并重新格式化"""
        self._format_params.update(new_params)
        self._format_system_prompt()

    async def run(self, input_data: dict) -> AgentMessage:
        """执行 Agent 的主要逻辑，子类必须实现"""
        raise NotImplementedError
    
    async def chat(self, message: str) -> AgentMessage:
        """
        通用聊天方法，用于 Agent 调试页面
        
        Args:
            message: 用户消息
        
        Returns:
            AgentMessage: Agent 的回复
        """
        logger.info(f"[{self.name}] chat 方法被调用")
        logger.info(f"[{self.name}] 消息: {message}")
        
        # 在线程池中运行同步的模型调用，避免阻塞事件循环
        import asyncio
        import concurrent.futures
        
        try:
            loop = asyncio.get_event_loop()
            logger.info(f"[{self.name}] 开始调用模型...")
            response = await loop.run_in_executor(
                _model_executor,
                self._call_model,
                self.get_full_prompt(),
                message
            )
            logger.info(f"[{self.name}] 模型调用完成")
            
            return AgentMessage(
                role=self.name,
                content=response,
                metadata={'chat_mode': True}
            )
        except Exception as e:
            logger.exception(f"[{self.name}] chat 方法失败: {str(e)}")
            raise
    
    def install_skill(self, skill: dict):
        """安装技能"""
        self.skills.append(skill)
    
    def uninstall_skill(self, skill_name: str):
        """卸载技能"""
        self.skills = [s for s in self.skills if s['name'] != skill_name]
    
    def get_full_prompt(self) -> str:
        """获取完整的 prompt，包含系统 prompt 和已安装的技能"""
        prompt = self.system_prompt
        if self.skills:
            prompt += "\n\n## 已安装的技能\n"
            for skill in self.skills:
                prompt += f"- {skill['name']}: {skill['description']}\n"
                if skill.get('prompt_injection'):
                    prompt += f"  使用指南: {skill['prompt_injection']}\n"
        return prompt
    
    def _call_model(self, system_prompt: str, user_message: str) -> str:
        """调用模型获取响应（同步版本，会阻塞事件循环，仅用于 chat 等场景）"""
        logger.info(f"[{self.name}] _call_model 开始")
        logger.info(f"[{self.name}] Provider: {self.model_config.get('provider', 'openrouter')}")
        logger.info(f"[{self.name}] Model: {self.model_config.get('model', 'default')}")
        
        try:
            from services.model_adapter import ModelAdapter
            adapter = ModelAdapter()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            provider = self.model_config.get("provider", "openrouter")
            model = self.model_config.get("model", None)
            temperature = self.model_config.get("temperature", 0.7)
            max_tokens = self.model_config.get("max_tokens", None)
            
            logger.info(f"[{self.name}] 调用 adapter.chat_completion...")
            result = adapter.chat_completion(
                messages=messages,
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"[{self.name}] 调用成功，响应长度: {len(result)}")
            return result
        except Exception as e:
            logger.exception(f"[{self.name}] _call_model 失败: {str(e)}")
            return self._format_model_error(e)
    
    async def _acall_model(self, system_prompt: str, user_message: str) -> str:
        """
        异步调用模型获取响应（在线程池中执行，不阻塞事件循环）。
        所有 Agent 的 run() 方法应使用此方法代替 _call_model。
        """
        logger.info(f"[{self.name}] _acall_model 开始（异步）")
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                _model_executor,
                self._call_model,
                system_prompt,
                user_message
            )
            return result
        except Exception as e:
            logger.exception(f"[{self.name}] _acall_model 失败: {str(e)}")
            return self._format_model_error(e)
    
    def _format_model_error(self, error: Exception) -> str:
        """格式化模型调用错误为用户友好的消息"""
        error_msg = str(error)
        provider = self.model_config.get("provider", "openrouter")
        if "API key not found" in error_msg:
            return f"⚠️ 配置错误：未找到 {provider} 的 API Key。请在设置中配置相应的 API Key。"
        elif "Chat completion failed" in error_msg:
            return f"⚠️ 模型调用失败：{error_msg}"
        else:
            return f"⚠️ 发生错误：{error_msg}"
