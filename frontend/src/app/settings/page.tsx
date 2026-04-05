'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { settingsApi } from '@/lib/api'

interface Settings {
  investment_style?: string
  llm_config?: {
    provider?: string
    model?: string
    temperature?: number
    max_tokens?: number
  }
  model_config?: {
    provider?: string
    model?: string
    temperature?: number
    max_tokens?: number
  }
  api_keys?: {
    [provider: string]: boolean
  }
}

const INVESTMENT_STYLE_OPTIONS: { value: string; label: string }[] = [
  { value: 'conservative', label: '保守型' },
  { value: 'growth', label: '成长型' },
  { value: 'value', label: '价值型' },
  { value: 'balanced', label: '均衡型' },
]

const PROVIDER_OPTIONS: { value: string; label: string }[] = [
  { value: 'openrouter', label: 'OpenRouter' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'grok', label: 'Grok' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'dashscope', label: 'DashScope' },
]

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const [settingsData, apiKeysData] = await Promise.all([
        settingsApi.get(),
        settingsApi.getApiKeys()
      ])

      setSettings({
        ...settingsData,
        api_keys: apiKeysData
      })
    } catch (err) {
      console.error('Failed to fetch settings:', err)
      // Mock data
      setSettings({
        investment_style: 'balanced',
        model_config: {
          provider: 'openai',
          model: 'gpt-4',
          temperature: 0.7,
          max_tokens: 2000,
        },
        api_keys: {
          openai: true,
          openrouter: false,
          grok: false,
          gemini: false,
          dashscope: true,
        },
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSaveInvestmentStyle = async () => {
    try {
      setSaving(true)
      await settingsApi.updateInvestmentStyle(settings.investment_style || 'balanced')
      showMessage('success', '投资风格已保存')
    } catch (err) {
      showMessage('error', '保存失败，请重试')
      console.error('Failed to save investment style:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveModelConfig = async () => {
    try {
      setSaving(true)
      await settingsApi.updateModelConfig((settings.llm_config || settings.model_config) || {})
      showMessage('success', '模型配置已保存')
    } catch (err) {
      showMessage('error', '保存失败，请重试')
      console.error('Failed to save model config:', err)
    } finally {
      setSaving(false)
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">加载中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">设置</h1>

        {message && (
          <div
            className={`mb-4 p-3 rounded-lg ${
              message.type === 'success' ? 'bg-green-50 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-50 text-red-800 dark:bg-red-900 dark:text-red-200'
            }`}
          >
            {message.text}
          </div>
        )}

        <div className="space-y-4">
          {/* Investment Style */}
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-lg">投资风格</CardTitle>
              <CardDescription className="text-sm">选择您的投资偏好</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1.5">投资风格</label>
                  <Select
                    options={INVESTMENT_STYLE_OPTIONS}
                    value={settings.investment_style || 'balanced'}
                    onChange={(e) => setSettings({ ...settings, investment_style: e.target.value })}
                  />
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <p className="font-medium mb-1.5">风格说明：</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li><strong>保守型</strong>：注重资本保值，选择低风险资产</li>
                    <li><strong>成长型</strong>：追求高增长潜力，接受较高风险</li>
                    <li><strong>价值型</strong>：寻找被低估的优质资产</li>
                    <li><strong>均衡型</strong>：平衡风险和收益，分散投资</li>
                  </ul>
                </div>
                <Button onClick={handleSaveInvestmentStyle} disabled={saving} size="sm">
                  {saving ? '保存中...' : '保存投资风格'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Model Configuration */}
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-lg">模型配置</CardTitle>
              <CardDescription className="text-sm">配置 AI 模型参数</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1.5">Provider</label>
                  <Select
                    options={PROVIDER_OPTIONS}
                    value={(settings.llm_config || settings.model_config)?.provider || 'openai'}
                    onChange={(e) => setSettings({
                      ...settings,
                      model_config: { ...(settings.llm_config || settings.model_config), provider: e.target.value }
                    })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1.5">Model 名称</label>
                  <Input
                    type="text"
                    value={(settings.llm_config || settings.model_config)?.model || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      model_config: { ...(settings.llm_config || settings.model_config), model: e.target.value }
                    })}
                    placeholder="例如: gpt-4, gpt-3.5-turbo"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1.5">Temperature</label>
                  <Input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={(settings.llm_config || settings.model_config)?.temperature || 0.7}
                    onChange={(e) => setSettings({
                      ...settings,
                      model_config: { ...(settings.llm_config || settings.model_config), temperature: parseFloat(e.target.value) }
                    })}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    控制输出的随机性：0（更确定）到 2（更随机）
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1.5">Max Tokens</label>
                  <Input
                    type="number"
                    min="1"
                    step="100"
                    value={(settings.llm_config || settings.model_config)?.max_tokens || 2000}
                    onChange={(e) => setSettings({
                      ...settings,
                      model_config: { ...(settings.llm_config || settings.model_config), max_tokens: parseInt(e.target.value) }
                    })}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    控制输出的最大长度
                  </p>
                </div>

                <Button onClick={handleSaveModelConfig} disabled={saving} size="sm">
                  {saving ? '保存中...' : '保存模型配置'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* API Key Status */}
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-lg">API Key 配置状态</CardTitle>
              <CardDescription className="text-sm">查看各 Provider 的 API Key 配置情况</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              <div className="space-y-2">
                {PROVIDER_OPTIONS.map((provider) => {
                  const isConfigured = settings.api_keys?.[provider.value] || false
                  return (
                    <div key={provider.value} className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <span className="font-medium text-sm">{provider.label}</span>
                      <Badge variant={isConfigured ? 'default' : 'secondary'}>
                        {isConfigured ? '已配置' : '未配置'}
                      </Badge>
                    </div>
                  )
                })}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
                注意：此处仅显示配置状态，不显示实际的 API Key。API Key 的配置请在后端进行。
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
