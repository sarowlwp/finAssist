"""
Agent 交互路由
"""
import logging
import tempfile
import shutil
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from agents.orchestrator import AnalysisOrchestrator
from agents.analysis_agent import (
    AGENT_REGISTRY,
    BUILTIN_AGENT_KEYS,
    register_agent,
    unregister_agent,
    load_custom_agents_from_settings,
)
from storage.settings import SettingsStore
from dependencies import get_settings_store

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = APIRouter()


# Pydantic 模型
class AgentInfo(BaseModel):
    """Agent 信息模型"""
    name: str = Field(..., description="Agent 名称")
    description: str = Field(..., description="Agent 描述")
    builtin: bool = Field(default=True, description="是否为内置 Agent（内置不可删除）")


class AgentChatRequest(BaseModel):
    """Agent 聊天请求模型"""
    message: str = Field(..., description="用户消息")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="模型配置（可选）")


class AgentChatResponse(BaseModel):
    """Agent 聊天响应模型"""
    agent_name: str = Field(..., description="Agent 名称")
    response: str = Field(..., description="Agent 回复")


class SkillInfo(BaseModel):
    """技能信息模型"""
    name: str = Field(..., description="技能名称")
    description: str = Field(default="", description="技能描述")
    prompt_injection: str = Field(default="", description="提示词注入")
    source: str = Field(default="manual", description="来源：manual / github")
    source_url: str = Field(default="", description="来源 URL（GitHub 链接）")
    installed: bool = Field(default=True, description="是否已安装")

class SkillCreateRequest(BaseModel):
    """手动创建技能请求模型"""
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能描述")
    prompt_injection: str = Field(default="", description="提示词注入")

class SkillInstallFromGithubRequest(BaseModel):
    """从 GitHub 安装技能请求模型"""
    github_url: str = Field(..., description="GitHub 仓库或文件链接")

class AgentCreateRequest(BaseModel):
    """创建自定义 Agent 请求模型"""
    agent_key: str = Field(..., description="Agent 唯一标识（英文，如 esg、options 等）")
    name: str = Field(..., description="Agent 显示名称")
    description: str = Field(..., description="Agent 描述")
    system_prompt: str = Field(..., description="Agent 的 system prompt")
    user_input_template: str = Field(default="", description="user_input 模板（可选，包含 {ticker}, {investment_style}, {data_summary} 占位符）")


def _get_available_agents() -> List[AgentInfo]:
    """
    动态生成可用 Agent 列表，包含内置的 supervisor/fusion 和 AGENT_REGISTRY 中的所有分析 Agent。
    """
    agents = [
        AgentInfo(name="supervisor", description="Supervisor Agent - 负责任务拆解和协调", builtin=True),
    ]
    for agent_key, config in AGENT_REGISTRY.items():
        agents.append(AgentInfo(
            name=agent_key,
            description=config.description or f"{config.name} Agent",
            builtin=config.builtin,
        ))
    agents.append(AgentInfo(name="fusion", description="Fusion Agent - 融合多个 Agent 的分析结果", builtin=True))
    return agents

def get_orchestrator(model_config: Dict[str, Any] = None, agent_model_configs: Dict[str, Dict[str, Any]] = None) -> AnalysisOrchestrator:
    """
    获取或创建 AnalysisOrchestrator 实例

    Args:
        model_config: 通用模型配置（默认配置）
        agent_model_configs: Agent 级模型配置

    Returns:
        AnalysisOrchestrator 实例
    """
    return AnalysisOrchestrator(model_config=model_config, agent_model_configs=agent_model_configs)


@router.get("/agents", response_model=List[AgentInfo])
async def get_agents():
    """
    获取所有 Agent 列表（动态生成，包含内置和自定义 Agent）
    
    Returns:
        Agent 列表
    """
    try:
        return _get_available_agents()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Agent 列表失败: {str(e)}"
        )


@router.post("/agents/{agent_name}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    agent_name: str,
    request: AgentChatRequest,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    与单个 Agent 聊天
    
    Args:
        agent_name: Agent 名称
        request: 聊天请求
        settings_store: 设置存储
    
    Returns:
        Agent 回复
    """
    logger.info(f"=== 收到 Agent 聊天请求 ===")
    logger.info(f"Agent: {agent_name}")
    logger.info(f"Message: {request.message}")
    logger.info(f"LLM Config: {request.llm_config}")
    
    try:
        # 验证 Agent 是否存在
        available_agents = _get_available_agents()
        agent_names = [agent.name for agent in available_agents]
        if agent_name not in agent_names:
            logger.error(f"Agent 不存在: {agent_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到 Agent: {agent_name}。可用的 Agent: {', '.join(agent_names)}"
            )
        
        # 获取模型配置
        llm_cfg = request.llm_config
        agent_model_configs = {}
        if not llm_cfg:
            logger.info("从设置中加载 LLM 配置")
            settings = settings_store.load()
            llm_cfg = settings.llm_config
            agent_model_configs = settings.agent_model_configs or {}
        logger.info(f"使用的 LLM 配置: {llm_cfg}")
        logger.info(f"使用的 Agent 模型配置: {agent_model_configs}")

        # 创建 orchestrator 并聊天
        logger.info("创建 Orchestrator...")
        orchestrator = get_orchestrator(llm_cfg, agent_model_configs)
        
        logger.info("调用 chat_with_agent...")
        response = await orchestrator.chat_with_agent(
            agent_name,
            request.message,
            llm_cfg
        )
        logger.info(f"收到响应: {response[:100]}..." if len(response) > 100 else f"收到响应: {response}")
        
        return AgentChatResponse(
            agent_name=agent_name,
            response=response
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Agent 聊天失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"与 Agent 聊天失败: {str(e)}"
        )


def _validate_agent_exists(agent_name: str) -> None:
    """验证 Agent 是否存在"""
    available = _get_available_agents()
    agent_names = [agent.name for agent in available]
    if agent_name not in agent_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到 Agent: {agent_name}"
        )


@router.get("/agents/{agent_name}/skills", response_model=List[SkillInfo])
async def get_agent_skills(
    agent_name: str,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    获取 Agent 的已安装技能
    """
    try:
        _validate_agent_exists(agent_name)

        settings = settings_store.load()
        agent_skills_map = settings.agent_skills or {}
        current_agent_skills = agent_skills_map.get(agent_name, {})
        skill_list: List[SkillInfo] = []
        for skill_name, skill_data in current_agent_skills.items():
            skill_list.append(SkillInfo(
                name=skill_name,
                description=skill_data.get("description", ""),
                prompt_injection=skill_data.get("prompt_injection", ""),
                source=skill_data.get("source", "manual"),
                source_url=skill_data.get("source_url", ""),
                installed=True,
            ))
        return skill_list
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Agent 技能失败: {str(e)}"
        )


@router.post("/agents/{agent_name}/skills/create", response_model=Dict[str, str])
async def create_skill(
    agent_name: str,
    request: SkillCreateRequest,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    手动创建并安装技能（create-skill）
    """
    try:
        _validate_agent_exists(agent_name)

        settings = settings_store.load()
        if not settings.agent_skills:
            settings.agent_skills = {}
        if agent_name not in settings.agent_skills:
            settings.agent_skills[agent_name] = {}

        if request.name in settings.agent_skills[agent_name]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"技能 {request.name} 已存在，请先卸载后再创建"
            )

        settings.agent_skills[agent_name][request.name] = {
            "description": request.description,
            "prompt_injection": request.prompt_injection,
            "source": "manual",
            "source_url": "",
            "installed": True,
        }
        settings_store.save(settings)

        return {"message": f"技能 {request.name} 已成功创建并安装到 Agent {agent_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建技能失败: {str(e)}"
        )


def _parse_github_skill(github_url: str) -> Dict[str, Any]:
    """
    从 GitHub 链接解析技能信息。
    支持的链接格式：
      - https://github.com/user/repo  （仓库级别，读取 README 或 SKILL.md）
      - https://github.com/user/repo/blob/main/SKILL.md  （直接指向技能描述文件）
    """
    import subprocess

    # 规范化 URL
    url = github_url.strip().rstrip("/")

    # 从 URL 中提取仓库名作为默认技能名
    repo_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", url)
    if not repo_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的 GitHub 链接，请提供 https://github.com/user/repo 格式的链接"
        )

    owner = repo_match.group(1)
    repo_name = repo_match.group(2).replace(".git", "")
    default_skill_name = repo_name

    # 克隆仓库到临时目录
    tmp_dir = Path(tempfile.mkdtemp(prefix="skill_"))
    try:
        clone_result = subprocess.run(
            ["git", "clone", "--depth", "1", f"https://github.com/{owner}/{repo_name}.git", str(tmp_dir / repo_name)],
            capture_output=True, text=True, timeout=60
        )
        if clone_result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"克隆 GitHub 仓库失败: {clone_result.stderr.strip()}"
            )

        cloned_path = tmp_dir / repo_name

        # 优先读取 SKILL.md，其次 README.md
        description = ""
        prompt_injection = ""
        for candidate in ["SKILL.md", "skill.md", "README.md", "readme.md"]:
            skill_file = cloned_path / candidate
            if skill_file.exists():
                content = skill_file.read_text(encoding="utf-8", errors="replace")
                if candidate.lower().startswith("skill"):
                    prompt_injection = content
                    # 取第一行非空行作为描述
                    for line in content.splitlines():
                        stripped = line.strip().lstrip("#").strip()
                        if stripped:
                            description = stripped[:200]
                            break
                else:
                    description = content[:300].replace("\n", " ").strip()
                break

        if not description:
            description = f"从 GitHub 安装的技能: {owner}/{repo_name}"

        return {
            "name": default_skill_name,
            "description": description,
            "prompt_injection": prompt_injection,
            "source": "github",
            "source_url": github_url,
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/agents/{agent_name}/skills/install-from-github", response_model=Dict[str, str])
async def install_skill_from_github(
    agent_name: str,
    request: SkillInstallFromGithubRequest,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    从 GitHub 链接下载并安装技能
    """
    try:
        _validate_agent_exists(agent_name)

        skill_data = _parse_github_skill(request.github_url)

        settings = settings_store.load()
        if not settings.agent_skills:
            settings.agent_skills = {}
        if agent_name not in settings.agent_skills:
            settings.agent_skills[agent_name] = {}

        skill_name = skill_data["name"]
        if skill_name in settings.agent_skills[agent_name]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"技能 {skill_name} 已存在，请先卸载后再安装"
            )

        settings.agent_skills[agent_name][skill_name] = {
            "description": skill_data["description"],
            "prompt_injection": skill_data["prompt_injection"],
            "source": skill_data["source"],
            "source_url": skill_data["source_url"],
            "installed": True,
        }
        settings_store.save(settings)

        return {"message": f"技能 {skill_name} 已从 GitHub 成功安装到 Agent {agent_name}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"从 GitHub 安装技能失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从 GitHub 安装技能失败: {str(e)}"
        )

@router.delete("/agents/{agent_name}/skills/{skill_name}", response_model=Dict[str, str])
async def uninstall_agent_skill(
    agent_name: str,
    skill_name: str,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    从 Agent 卸载技能
    
    Args:
        agent_name: Agent 名称
        skill_name: 技能名称
        settings_store: 设置存储
    
    Returns:
        卸载结果
    """
    try:
        _validate_agent_exists(agent_name)
        
        # 获取当前设置
        settings = settings_store.load()
        
        # 检查技能是否存在
        agent_skills_map = settings.agent_skills or {}
        current_agent_skills = agent_skills_map.get(agent_name, {})
        if skill_name not in current_agent_skills:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到技能: {skill_name}"
            )
        
        # 移除技能
        del settings.agent_skills[agent_name][skill_name]
        
        # 保存设置
        settings_store.save(settings)
        
        return {
            "message": f"技能 {skill_name} 已成功从 Agent {agent_name} 卸载"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"卸载技能失败: {str(e)}"
        )


# ==================== Agent 动态管理 API ====================

@router.post("/agents/create", response_model=Dict[str, str])
async def create_custom_agent(
    request: AgentCreateRequest,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    创建自定义 Agent

    用户提供 agent_key、name、description、system_prompt，
    系统会将其注册到内存注册表并持久化到 settings.json。
    """
    try:
        # 检查 agent_key 是否与 supervisor/fusion 冲突
        reserved_keys = {"supervisor", "fusion"}
        if request.agent_key in reserved_keys:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{request.agent_key}' 是系统保留名称，请使用其他名称"
            )

        # 注册到内存注册表（会检查重复）
        try:
            register_agent(
                agent_key=request.agent_key,
                name=request.name,
                description=request.description,
                system_prompt=request.system_prompt,
                user_input_template=request.user_input_template,
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(ve)
            )

        # 持久化到 settings.json
        settings = settings_store.load()
        if not settings.custom_agents:
            settings.custom_agents = {}
        settings.custom_agents[request.agent_key] = {
            "name": request.name,
            "description": request.description,
            "system_prompt": request.system_prompt,
            "user_input_template": request.user_input_template,
        }
        settings_store.save(settings)

        return {"message": f"自定义 Agent '{request.name}' (key={request.agent_key}) 创建成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"创建自定义 Agent 失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建自定义 Agent 失败: {str(e)}"
        )


@router.delete("/agents/{agent_name}", response_model=Dict[str, str])
async def delete_agent(
    agent_name: str,
    settings_store: SettingsStore = Depends(get_settings_store)
):
    """
    删除自定义 Agent（内置 Agent 不可删除）

    Args:
        agent_name: 要删除的 Agent 名称（即 agent_key）
    """
    try:
        # 检查是否为系统保留 Agent
        reserved_keys = {"supervisor", "fusion"}
        if agent_name in reserved_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"系统 Agent '{agent_name}' 不可删除"
            )

        # 从内存注册表中移除（会检查是否内置）
        try:
            unregister_agent(agent_name)
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )

        # 从持久化存储中移除
        settings = settings_store.load()
        if settings.custom_agents and agent_name in settings.custom_agents:
            del settings.custom_agents[agent_name]

        # 同时清理该 Agent 的技能配置
        if settings.agent_skills and agent_name in settings.agent_skills:
            del settings.agent_skills[agent_name]

        settings_store.save(settings)

        return {"message": f"Agent '{agent_name}' 已成功删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"删除 Agent 失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除 Agent 失败: {str(e)}"
        )
