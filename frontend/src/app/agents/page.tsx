'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Modal } from '@/components/ui/modal'
import { agentApi, settingsApi } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Agent {
  name: string
  description: string
  builtin?: boolean
}

interface Skill {
  name: string
  description: string
  prompt_injection?: string
  source?: string
  source_url?: string
}

const PROVIDER_OPTIONS: { value: string; label: string }[] = [
  { value: 'openrouter', label: 'OpenRouter' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'grok', label: 'Grok' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'dashscope', label: 'DashScope' },
]

// 从 localStorage 加载历史记录（将 timestamp 字符串还原为 Date 对象）
const loadHistoryFromStorage = (): Record<string, Message[]> => {
  try {
    const saved = localStorage.getItem('agent_chat_history')
    if (!saved) return {}
    const parsed = JSON.parse(saved) as Record<string, Message[]>
    // JSON.parse 后 timestamp 是字符串，需要还原为 Date 对象
    for (const agentName of Object.keys(parsed)) {
      parsed[agentName] = parsed[agentName].map((msg) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }))
    }
    return parsed
  } catch {
    return {}
  }
}

// 保存历史记录到 localStorage
const saveHistoryToStorage = (history: Record<string, Message[]>) => {
  try {
    localStorage.setItem('agent_chat_history', JSON.stringify(history))
  } catch (err) {
    console.error('Failed to save history:', err)
  }
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loadingAgents, setLoadingAgents] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState('supervisor')
  const [messages, setMessages] = useState<Message[]>([])
  const [agentHistory, setAgentHistory] = useState<Record<string, Message[]>>({})

  // Load history from localStorage on mount
  useEffect(() => {
    setAgentHistory(loadHistoryFromStorage())
  }, [])
  const [inputMessage, setInputMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [modelConfig, setModelConfig] = useState({
    provider: 'openai',
    model: 'gpt-4',
  })
  const [skills, setSkills] = useState<Skill[]>([])
  const [loadingSkills, setLoadingSkills] = useState(false)
  const [installingSkill, setInstallingSkill] = useState(false)
  const [newSkill, setNewSkill] = useState({ name: '', description: '', prompt_injection: '' })
  const [githubUrl, setGithubUrl] = useState('')
  const [installTab, setInstallTab] = useState<'create' | 'github'>('create')
  const [showCreateAgent, setShowCreateAgent] = useState(false)
  const [creatingAgent, setCreatingAgent] = useState(false)
  const [newAgent, setNewAgent] = useState({
    agent_key: '',
    name: '',
    description: '',
    system_prompt: '',
    user_input_template: '',
  })
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 从后端加载 Agent 列表
  const fetchAgents = async () => {
    try {
      setLoadingAgents(true)
      const data = await agentApi.getAll()
      setAgents(data)
    } catch (err) {
      console.error('Failed to fetch agents:', err)
    } finally {
      setLoadingAgents(false)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [])

  useEffect(() => {
    fetchSkills()
    loadAgentModelConfig(selectedAgent)
    setMessages(agentHistory[selectedAgent] || [])
  }, [selectedAgent])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 当 messages 变化时，更新 agentHistory 并持久化
  useEffect(() => {
    const newHistory = { ...agentHistory, [selectedAgent]: messages }
    setAgentHistory(newHistory)
    saveHistoryToStorage(newHistory)
  }, [messages])

  const loadAgentModelConfig = async (agentName: string) => {
    try {
      const config = await settingsApi.getAgentModelConfig(agentName)
      setModelConfig({
        provider: config.provider || 'openai',
        model: config.model || 'gpt-4',
      })
    } catch (err) {
      console.error('Failed to load agent model config:', err)
      setModelConfig({ provider: 'openai', model: 'gpt-4' })
    }
  }

  const saveAgentModelConfig = async (config: typeof modelConfig) => {
    try {
      await settingsApi.updateAgentModelConfig(selectedAgent, config)
    } catch (err) {
      console.error('Failed to save agent model config:', err)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchSkills = async () => {
    try {
      setLoadingSkills(true)
      const data = await agentApi.getSkills(selectedAgent)
      setSkills(data)
    } catch (err) {
      console.error('Failed to fetch skills:', err)
      // Mock data
      setSkills([
        { name: 'stock_analysis', description: '股票分析技能' },
        { name: 'market_sentiment', description: '市场情绪分析' },
      ])
    } finally {
      setLoadingSkills(false)
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setSending(true)

    try {
      const response = await agentApi.chat(selectedAgent, inputMessage, modelConfig)
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response || '处理完成',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `错误: ${err instanceof Error ? err.message : JSON.stringify(err)}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      console.error('Failed to send message:', err)
    } finally {
      setSending(false)
    }
  }

  const handleCreateSkill = async () => {
    if (!newSkill.name.trim()) {
      alert('请输入技能名称')
      return
    }
    if (!newSkill.description.trim()) {
      alert('请输入技能描述')
      return
    }

    try {
      setInstallingSkill(true)
      await agentApi.createSkill(selectedAgent, newSkill)
      await fetchSkills()
      setNewSkill({ name: '', description: '', prompt_injection: '' })
      alert('技能创建成功')
    } catch (err) {
      alert(`创建技能失败: ${err instanceof Error ? err.message : '请重试'}`)
      console.error('Failed to create skill:', err)
    } finally {
      setInstallingSkill(false)
    }
  }

  const handleInstallFromGithub = async () => {
    if (!githubUrl.trim()) {
      alert('请输入 GitHub 链接')
      return
    }
    if (!githubUrl.startsWith('https://github.com/')) {
      alert('请输入有效的 GitHub 链接（https://github.com/...）')
      return
    }

    try {
      setInstallingSkill(true)
      await agentApi.installFromGithub(selectedAgent, githubUrl)
      await fetchSkills()
      setGithubUrl('')
      alert('从 GitHub 安装技能成功')
    } catch (err) {
      alert(`从 GitHub 安装失败: ${err instanceof Error ? err.message : '请重试'}`)
      console.error('Failed to install from GitHub:', err)
    } finally {
      setInstallingSkill(false)
    }
  }

  const handleUninstallSkill = async (skillName: string) => {
    if (!confirm(`确定要卸载 ${skillName} 技能吗？`)) {
      return
    }

    try {
      await agentApi.uninstallSkill(selectedAgent, skillName)
      await fetchSkills()
    } catch (err) {
      alert('卸载技能失败，请重试')
      console.error('Failed to uninstall skill:', err)
    }
  }

  // 清空当前 Agent 的历史记录
  const clearCurrentHistory = () => {
    if (!confirm(`确定要清空 ${selectedAgent} 的所有聊天记录吗？`)) {
      return
    }
    
    const newHistory = { ...agentHistory }
    delete newHistory[selectedAgent]
    setAgentHistory(newHistory)
    setMessages([])
    saveHistoryToStorage(newHistory)
  }

  // 清空所有 Agent 的历史记录
  const clearAllHistory = () => {
    if (!confirm('确定要清空所有 Agent 的聊天记录吗？此操作不可恢复！')) {
      return
    }
    
    setAgentHistory({})
    setMessages([])
    saveHistoryToStorage({})
  }

  // 创建自定义 Agent
  const handleCreateAgent = async () => {
    if (!newAgent.agent_key.trim()) {
      alert('请输入 Agent Key（英文标识）')
      return
    }
    if (!newAgent.name.trim()) {
      alert('请输入 Agent 名称')
      return
    }
    if (!newAgent.system_prompt.trim()) {
      alert('请输入 System Prompt')
      return
    }

    try {
      setCreatingAgent(true)
      await agentApi.createAgent(newAgent)
      await fetchAgents()
      setNewAgent({ agent_key: '', name: '', description: '', system_prompt: '', user_input_template: '' })
      setShowCreateAgent(false)
      setSelectedAgent(newAgent.agent_key)
      alert('Agent 创建成功')
    } catch (err) {
      alert(`创建 Agent 失败: ${err instanceof Error ? err.message : '请重试'}`)
      console.error('Failed to create agent:', err)
    } finally {
      setCreatingAgent(false)
    }
  }

  // 删除自定义 Agent
  const handleDeleteAgent = async (agentName: string) => {
    if (!confirm(`确定要删除 Agent "${agentName}" 吗？此操作不可恢复！`)) {
      return
    }

    try {
      await agentApi.deleteAgent(agentName)
      await fetchAgents()
      if (selectedAgent === agentName) {
        setSelectedAgent('supervisor')
      }
      alert('Agent 已删除')
    } catch (err) {
      alert(`删除 Agent 失败: ${err instanceof Error ? err.message : '请重试'}`)
      console.error('Failed to delete agent:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Agent 调试</h1>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Agent List */}
          <Card className="lg:col-span-1">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-lg">Agent 列表</CardTitle>
              <CardDescription className="text-sm">选择要调试的 Agent</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              {loadingAgents ? (
                <div className="text-center py-3 text-muted-foreground">加载中...</div>
              ) : (
                <div className="space-y-1.5">
                  {agents.map((agent) => (
                    <div key={agent.name} className="relative group">
                      <button
                        onClick={() => setSelectedAgent(agent.name)}
                        className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${
                          selectedAgent === agent.name
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-card hover:bg-accent'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{agent.name}</span>
                          {!agent.builtin && (
                            <Badge variant="secondary" className="text-xs">自定义</Badge>
                          )}
                        </div>
                        <div className={`text-xs ${selectedAgent === agent.name ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
                          {agent.description}
                        </div>
                      </button>
                      {!agent.builtin && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteAgent(agent.name) }}
                          className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive/80 text-xs px-1.5 py-0.5 rounded hover:bg-destructive/10"
                          title="删除 Agent"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* 新增 Agent 按钮 */}
              <div className="mt-3 pt-3 border-t">
                <Button
                  onClick={() => setShowCreateAgent(true)}
                  variant="outline"
                  className="w-full"
                  size="sm"
                >
                  + 新增 Agent
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Chat Interface */}
          <Card className="lg:col-span-3">
            <CardHeader className="py-3 px-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{selectedAgent} 聊天</CardTitle>
                  <CardDescription className="text-sm">与 Agent 进行交互调试</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={clearCurrentHistory}
                    variant="outline"
                    size="sm"
                    disabled={messages.length === 0}
                  >
                    清空当前对话
                  </Button>
                  <Button
                    onClick={clearAllHistory}
                    variant="destructive"
                    size="sm"
                  >
                    清空所有历史
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              {/* Model Config */}
              <div className="mb-3 p-3 bg-muted rounded-lg">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Provider</label>
                    <Select
                      options={PROVIDER_OPTIONS}
                      value={modelConfig.provider}
                      onChange={(e) => setModelConfig({ ...modelConfig, provider: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Model</label>
                    <Input
                      type="text"
                      value={modelConfig.model}
                      onChange={(e) => setModelConfig({ ...modelConfig, model: e.target.value })}
                      placeholder="gpt-4"
                    />
                  </div>
                </div>
                <div className="mt-3 flex justify-end">
                  <Button
                    onClick={() => saveAgentModelConfig(modelConfig)}
                    variant="outline"
                    size="sm"
                  >
                    保存配置
                  </Button>
                </div>
              </div>

              {/* Messages */}
              <div className="h-80 overflow-y-auto mb-3 p-3 bg-card rounded-lg border">
                {messages.length === 0 ? (
                  <div className="text-center text-muted-foreground py-6">
                    开始与 {selectedAgent} 对话
                  </div>
                ) : (
                  <div className="space-y-3">
                    {messages.map((msg, index) => (
                      <div
                        key={index}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[70%] px-3 py-2 rounded-lg text-sm ${
                            msg.role === 'user'
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-secondary text-secondary-foreground'
                          }`}
                        >
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                          <div className="text-xs mt-1 opacity-70">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="flex gap-2">
                <Textarea
                  placeholder="输入消息..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  rows={2}
                  className="flex-1 text-sm"
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={sending || !inputMessage.trim()}
                  className="self-end"
                  size="sm"
                >
                  {sending ? '发送中...' : '发送'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Skills Management */}
        <Card className="mt-4">
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-lg">已安装技能</CardTitle>
            <CardDescription className="text-sm">管理 {selectedAgent} 的技能</CardDescription>
          </CardHeader>
          <CardContent className="pt-0 px-4 pb-4">
            {loadingSkills ? (
              <div className="text-center py-3">加载中...</div>
            ) : skills.length === 0 ? (
              <div className="text-center py-3 text-muted-foreground">暂无已安装的技能</div>
            ) : (
              <div className="space-y-1.5">
                {skills.map((skill) => (
                  <div
                    key={skill.name}
                    className="flex items-center justify-between p-2 bg-muted rounded-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{skill.name}</span>
                        <Badge variant={skill.source === 'github' ? 'default' : 'secondary'} className="text-xs">
                          {skill.source === 'github' ? 'GitHub' : '手动创建'}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground truncate">{skill.description}</div>
                      {skill.source_url && (
                        <div className="text-xs text-primary truncate mt-0.5">{skill.source_url}</div>
                      )}
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="ml-2 shrink-0"
                      onClick={() => handleUninstallSkill(skill.name)}
                    >
                      卸载
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Install Skill Tabs */}
            <div className="mt-6 pt-6 border-t">
              <h4 className="font-medium mb-4">安装新技能</h4>

              {/* Tab Switcher */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setInstallTab('create')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    installTab === 'create'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                >
                  ✏️ 手动创建
                </button>
                <button
                  onClick={() => setInstallTab('github')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    installTab === 'github'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                >
                  🔗 从 GitHub 安装
                </button>
              </div>

              {/* Create Skill Form */}
              {installTab === 'create' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                      placeholder="技能名称（必填）"
                      value={newSkill.name}
                      onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
                    />
                    <Input
                      placeholder="技能描述（必填）"
                      value={newSkill.description}
                      onChange={(e) => setNewSkill({ ...newSkill, description: e.target.value })}
                    />
                  </div>
                  <Textarea
                    placeholder="提示词注入（可选）- 该技能执行时注入到 Agent 的 prompt"
                    value={newSkill.prompt_injection}
                    onChange={(e) => setNewSkill({ ...newSkill, prompt_injection: e.target.value })}
                    rows={3}
                  />
                  <Button
                    onClick={handleCreateSkill}
                    disabled={installingSkill}
                  >
                    {installingSkill ? '创建中...' : '创建技能'}
                  </Button>
                </div>
              )}

              {/* GitHub Install Form */}
              {installTab === 'github' && (
                <div className="space-y-4">
                  <Input
                    placeholder="GitHub 仓库链接，如 https://github.com/user/skill-repo"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    支持 GitHub 仓库链接，系统将自动克隆仓库并读取 SKILL.md 或 README.md 作为技能描述
                  </p>
                  <Button
                    onClick={handleInstallFromGithub}
                    disabled={installingSkill}
                  >
                    {installingSkill ? '安装中...' : '从 GitHub 安装'}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

      </div>

      {/* 新增 Agent Modal */}
      <Modal
        open={showCreateAgent}
        onClose={() => {
          setShowCreateAgent(false)
          setNewAgent({ agent_key: '', name: '', description: '', system_prompt: '', user_input_template: '' })
        }}
        title="创建自定义 Agent"
        description="配置新的 Agent，创建后将自动加入分析流程"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Agent Key <span className="text-red-500">*</span></label>
            <Input
              placeholder="英文标识，如 esg、sentiment"
              value={newAgent.agent_key}
              onChange={(e) => setNewAgent({ ...newAgent, agent_key: e.target.value })}
            />
            <p className="text-xs text-muted-foreground mt-1">唯一标识符，创建后不可修改</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">显示名称 <span className="text-red-500">*</span></label>
            <Input
              placeholder="如 ESG Agent、情绪分析 Agent"
              value={newAgent.name}
              onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">描述</label>
            <Input
              placeholder="简短描述 Agent 的功能"
              value={newAgent.description}
              onChange={(e) => setNewAgent({ ...newAgent, description: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">System Prompt <span className="text-red-500">*</span></label>
            <Textarea
              placeholder="定义 Agent 的角色、能力和输出格式..."
              value={newAgent.system_prompt}
              onChange={(e) => setNewAgent({ ...newAgent, system_prompt: e.target.value })}
              rows={6}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">User Input 模板</label>
            <Textarea
              placeholder="可选。可用占位符: {ticker}, {investment_style}, {data_summary}"
              value={newAgent.user_input_template}
              onChange={(e) => setNewAgent({ ...newAgent, user_input_template: e.target.value })}
              rows={3}
            />
            <p className="text-xs text-muted-foreground mt-1">留空时使用通用模板</p>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              onClick={() => {
                setShowCreateAgent(false)
                setNewAgent({ agent_key: '', name: '', description: '', system_prompt: '', user_input_template: '' })
              }}
              variant="outline"
            >
              取消
            </Button>
            <Button
              onClick={handleCreateAgent}
              disabled={creatingAgent || !newAgent.agent_key.trim() || !newAgent.name.trim() || !newAgent.system_prompt.trim()}
            >
              {creatingAgent ? '创建中...' : '创建 Agent'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}