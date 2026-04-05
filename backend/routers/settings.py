"""
设置管理路由
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from storage.settings import SettingsStore, UserSettings
from services.model_adapter import ModelAdapter
from config import config
from dependencies import get_settings_store, get_model_adapter

router = APIRouter()


# Pydantic 模型
class InvestmentStyleUpdate(BaseModel):
    """投资风格更新请求模型"""
    investment_style: str = Field(..., description="投资风格：conservative, growth, value, balanced")


class ModelConfigUpdate(BaseModel):
    """模型配置更新请求模型"""
    provider: str = Field(None, description="模型提供商")
    model: str = Field(None, description="模型名称")
    temperature: float = Field(None, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(None, gt=0, description="最大 token 数")

class AgentModelConfigUpdate(BaseModel):
    """Agent 级模型配置更新请求模型"""
    provider: str = Field(..., description="模型提供商")
    model: str = Field(..., description="模型名称")


class ProviderValidation(BaseModel):
    """提供商验证响应模型"""
    provider: str = Field(..., description="提供商名称")
    configured: bool = Field(..., description="是否已配置 API key")
    base_url: str = Field(..., description="基础 URL")
    default_model: str = Field(..., description="默认模型")


@router.get("/settings", response_model=UserSettings)
async def get_settings(
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    获取用户设置
    
    Returns:
        用户设置
    """
    try:
        settings = settings_store.load()
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设置失败: {str(e)}"
        )


@router.put("/settings/investment-style", response_model=UserSettings)
async def update_investment_style(
    update: InvestmentStyleUpdate,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    更新投资风格
    
    Args:
        update: 投资风格更新
    
    Returns:
        更新后的设置
    """
    try:
        # 验证投资风格
        valid_styles = ["conservative", "growth", "value", "balanced"]
        if update.investment_style not in valid_styles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的投资风格，可选值: {', '.join(valid_styles)}"
            )
        
        settings = settings_store.update_investment_style(update.investment_style)
        return settings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新投资风格失败: {str(e)}"
        )


@router.put("/settings/model-config", response_model=UserSettings)
async def update_model_config(
    update: ModelConfigUpdate,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    更新模型配置
    
    Args:
        update: 模型配置更新
    
    Returns:
        更新后的设置
    """
    try:
        # 验证提供商
        model_adapter_instance = ModelAdapter()
        if update.provider and not model_adapter_instance.validate_provider(update.provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的模型提供商: {update.provider}"
            )
        
        # 构建更新数据
        update_data = {}
        if update.provider is not None:
            update_data["provider"] = update.provider
        if update.model is not None:
            update_data["model"] = update.model
        if update.temperature is not None:
            update_data["temperature"] = update.temperature
        if update.max_tokens is not None:
            update_data["max_tokens"] = update.max_tokens
        
        settings = settings_store.update_llm_config(update_data)
        return settings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新模型配置失败: {str(e)}"
        )


@router.get("/settings/providers", response_model=List[ProviderValidation])
async def get_providers(
    model_adapter: ModelAdapter = Depends(get_model_adapter)
):
    """
    获取支持的模型提供商列表
    
    Returns:
        提供商列表
    """
    try:
        providers = []
        for provider in model_adapter.get_supported_providers():
            provider_config = config.PROVIDER_CONFIGS.get(provider, {})
            providers.append(ProviderValidation(
                provider=provider,
                configured=model_adapter.validate_api_key(provider),
                base_url=provider_config.get("base_url", ""),
                default_model=model_adapter.get_default_model(provider) or ""
            ))
        return providers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提供商列表失败: {str(e)}"
        )


@router.get("/settings/providers/{provider}/validate", response_model=ProviderValidation)
async def validate_provider(
    provider: str,
    model_adapter: ModelAdapter = Depends(get_model_adapter)
):
    """
    验证某个 provider 的 API key 是否配置

    Args:
        provider: 提供商名称

    Returns:
        验证结果
    """
    try:
        if not model_adapter.validate_provider(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的模型提供商: {provider}"
            )

        provider_config = config.PROVIDER_CONFIGS.get(provider, {})

        return ProviderValidation(
            provider=provider,
            configured=model_adapter.validate_api_key(provider),
            base_url=provider_config.get("base_url", ""),
            default_model=model_adapter.get_default_model(provider) or ""
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证提供商失败: {str(e)}"
        )


@router.get("/settings/api-keys", response_model=Dict[str, bool])
async def get_api_keys_status(
    model_adapter: ModelAdapter = Depends(get_model_adapter)
):
    """
    获取所有提供商的 API Key 配置状态

    Returns:
        提供商名称到配置状态的字典
    """
    try:
        api_keys_status = {}
        for provider in model_adapter.get_supported_providers():
            api_keys_status[provider] = model_adapter.validate_api_key(provider)
        return api_keys_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 API Key 状态失败: {str(e)}"
        )

@router.get("/settings/agents/{agent_name}/model-config")
async def get_agent_model_config(
    agent_name: str,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    获取指定 Agent 的模型配置

    Args:
        agent_name: Agent 名称

    Returns:
        Agent 模型配置
    """
    try:
        config = settings_store.get_agent_model_config(agent_name)
        if config is None:
            return {"provider": "openai", "model": "gpt-4"}
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Agent 模型配置失败: {str(e)}"
        )

@router.put("/settings/agents/{agent_name}/model-config", response_model=UserSettings)
async def update_agent_model_config(
    agent_name: str,
    update: AgentModelConfigUpdate,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    更新指定 Agent 的模型配置
    
    Args:
        agent_name: Agent 名称
        update: Agent 模型配置更新
    
    Returns:
        更新后的设置
    """
    try:
        config = {
            "provider": update.provider,
            "model": update.model
        }
        settings = settings_store.update_agent_model_config(agent_name, config)
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新 Agent 模型配置失败: {str(e)}"
        )