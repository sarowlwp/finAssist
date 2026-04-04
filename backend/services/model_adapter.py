"""
模型适配层模块
支持多个 AI 模型提供商
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os


class ModelAdapter:
    """模型适配器类"""
    
    # 支持的提供商配置
    PROVIDER_CONFIGS = {
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
    
    # 默认模型配置
    DEFAULT_MODELS = {
        "openrouter": "anthropic/claude-3.5-sonnet",
        "openai": "gpt-4-turbo-preview",
        "grok": "grok-beta",
        "gemini": "gemini-2.0-flash-exp",
        "dashscope": "qwen-max-latest"
    }
    
    def __init__(self):
        self._clients: Dict[str, OpenAI] = {}
    
    def _get_client(self, provider: str) -> OpenAI:
        """
        获取指定提供商的客户端
        
        Args:
            provider: 提供商名称
            
        Returns:
            OpenAI 客户端实例
        """
        if provider not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        if provider not in self._clients:
            config = self.PROVIDER_CONFIGS[provider]
            api_key = os.getenv(config["api_key_env"])
            
            if not api_key:
                raise ValueError(f"API key not found for provider: {provider}")
            
            # 获取 base_url：OpenAI 支持自定义 base_url
            base_url = config["base_url"]
            if provider == "openai":
                custom_base_url = os.getenv("OPENAI_BASE_URL", "")
                if custom_base_url:
                    base_url = custom_base_url
            
            self._clients[provider] = OpenAI(
                base_url=base_url,
                api_key=api_key,
                timeout=300.0  # 300秒超时，适配免费模型和慢速服务
            )
        
        return self._clients[provider]
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = "openrouter",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        调用聊天补全接口
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            provider: 模型提供商
            model: 模型名称，如果为 None 则使用默认模型
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            模型响应文本
        """
        try:
            client = self._get_client(provider)
            
            # 使用默认模型（如果未指定）
            if not model:
                model = self.DEFAULT_MODELS.get(provider)
            
            # 构建请求参数
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # 调用 API
            response = client.chat.completions.create(**request_params)
            
            # 提取响应内容
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            
            return ""
            
        except Exception as e:
            raise RuntimeError(f"Chat completion failed for provider {provider}: {str(e)}")
    
    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = "openrouter",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        流式聊天补全接口
        
        Args:
            messages: 消息列表
            provider: 模型提供商
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Yields:
            响应文本片段
        """
        try:
            client = self._get_client(provider)
            
            if not model:
                model = self.DEFAULT_MODELS.get(provider)
            
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
                **kwargs
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            stream = client.chat.completions.create(**request_params)
            
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
                        
        except Exception as e:
            raise RuntimeError(f"Stream chat completion failed for provider {provider}: {str(e)}")
    
    def get_supported_providers(self) -> List[str]:
        """获取支持的提供商列表"""
        return list(self.PROVIDER_CONFIGS.keys())
    
    def get_default_model(self, provider: str) -> Optional[str]:
        """获取指定提供商的默认模型"""
        return self.DEFAULT_MODELS.get(provider)
    
    def validate_provider(self, provider: str) -> bool:
        """验证提供商是否支持"""
        return provider in self.PROVIDER_CONFIGS
    
    def validate_api_key(self, provider: str) -> bool:
        """验证 API 密钥是否存在"""
        if provider not in self.PROVIDER_CONFIGS:
            return False
        
        config = self.PROVIDER_CONFIGS[provider]
        api_key = os.getenv(config["api_key_env"])
        return bool(api_key)