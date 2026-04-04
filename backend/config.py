"""
全局配置模块
读取环境变量并提供默认配置
"""
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os
from pathlib import Path

# 加载环境变量
load_dotenv()

class Config:
    """全局配置类"""
    
    # API 密钥
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    
    # 数据目录
    DATA_DIR: Path = Path(__file__).parent / "data"
    
    # 默认模型配置
    DEFAULT_MODEL_CONFIG: Dict[str, Any] = {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    # 支持的模型提供商配置
    PROVIDER_CONFIGS: Dict[str, Dict[str, str]] = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key_env": "OPENROUTER_API_KEY"
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY"
        },
        "grok": {
            "base_url": "https://api.x.ai/v1",
            "api_key_env": "GROK_API_KEY"
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key_env": "GEMINI_API_KEY"
        },
        "dashscope": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY"
        }
    }
    
    # Finnhub API 配置
    FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1"
    
    @classmethod
    def get_api_key(cls, provider: str) -> str:
        """获取指定提供商的 API 密钥"""
        provider_config = cls.PROVIDER_CONFIGS.get(provider, {})
        env_key = provider_config.get("api_key_env", "")
        return os.getenv(env_key, "")
    
    @classmethod
    def get_base_url(cls, provider: str) -> str:
        """获取指定提供商的基础 URL"""
        provider_config = cls.PROVIDER_CONFIGS.get(provider, {})
        return provider_config.get("base_url", "")


# 全局配置实例
config = Config()
