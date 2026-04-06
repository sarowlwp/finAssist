"""
用户设置存储模块
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import json
from datetime import datetime


class UserSettings(BaseModel):
    """用户设置模型"""
    investment_style: str = Field(default="balanced", description="投资风格：conservative, balanced, aggressive")
    llm_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        description="LLM 配置"
    )
    agent_model_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent 级模型配置，key 为 agent 名称，value 为模型配置"
    )
    agent_skills: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent 已安装技能，按 agent 维度存储。key 为 agent 名称，value 为该 agent 的技能字典（技能名称 -> 技能详情）"
    )
    custom_agents: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="用户自定义 Agent 配置。key 为 agent_key，value 包含 name, description, system_prompt, user_input_template"
    )
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")
    


class SettingsStore:
    """设置存储类"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.settings_file = data_dir / "settings.json"
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """确保数据文件存在"""
        if not self.settings_file.exists():
            self._save_initial_data()
    
    def _save_initial_data(self) -> None:
        """保存初始默认设置"""
        initial_data = UserSettings().model_dump()
        self._write_file(initial_data)
    
    def _write_file(self, data: Dict[str, Any]) -> None:
        """写入文件"""
        self.settings_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def _read_file(self) -> Dict[str, Any]:
        """读取文件"""
        try:
            content = self.settings_file.read_text(encoding="utf-8")
            return json.loads(content) if content else {}
        except Exception as e:
            print(f"Error reading settings file: {e}")
            return {}
    
    def load(self) -> UserSettings:
        """加载设置"""
        data = self._read_file()
        if not data:
            return UserSettings()
        return UserSettings(**data)
    
    def save(self, settings: UserSettings) -> None:
        """保存设置"""
        data = settings.model_dump()
        self._write_file(data)
    
    def update_investment_style(self, style: str) -> UserSettings:
        """更新投资风格"""
        settings = self.load()
        settings.investment_style = style
        settings.updated_at = datetime.now().isoformat()
        self.save(settings)
        return settings
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        settings = self.load()
        return settings.llm_config
    
    def update_llm_config(self, config: Dict[str, Any]) -> UserSettings:
        """更新 LLM 配置"""
        settings = self.load()
        settings.llm_config.update(config)
        settings.updated_at = datetime.now().isoformat()
        self.save(settings)
        return settings
    
    def get_agent_model_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取指定 Agent 的模型配置"""
        settings = self.load()
        return settings.agent_model_configs.get(agent_name)
    
    def get_agent_model_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取指定 Agent 的模型配置"""
        settings = self.load()
        return settings.agent_model_configs.get(agent_name)

    def update_agent_model_config(self, agent_name: str, config: Dict[str, Any]) -> UserSettings:
        """更新指定 Agent 的模型配置"""
        settings = self.load()
        settings.agent_model_configs[agent_name] = config
        settings.updated_at = datetime.now().isoformat()
        self.save(settings)
        return settings
