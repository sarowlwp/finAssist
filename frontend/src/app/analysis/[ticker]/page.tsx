'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { marketApi, analysisApi } from '@/lib/api'

// 导入 SSE 事件类型（从 lib/api 复制或重新定义）
interface StreamEvent {
  type: 'start' | 'progress' | 'agent_result' | 'fusion_result' | 'complete' | 'error';
  [key: string]: any;
}

interface AnalysisData {
  ticker: string
  company_name?: string
  current_price?: number
  change_percent?: number
  fusion_summary?: string
  news_report?: string
  sec_report?: string
  fundamentals_report?: string
  technical_report?: string
  custom_skill_report?: string
  status?: string
}

export default function AnalysisPage() {
  const params = useParams()
  const ticker = params.ticker as string
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 流式分析进度
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')
  const [progressStage, setProgressStage] = useState('')
  const cancelStreamRef = useRef<(() => void) | null>(null)

  // Collapsed state for each agent report
  const [collapsed, setCollapsed] = useState({
    news: false,
    sec: false,
    fundamentals: false,
    technical: false,
    custom_skill: false
  })

  // Handle reanalyze with useCallback to fix dependency issues
  const handleReanalyze = useCallback(() => {
    try {
      setAnalyzing(true)
      setProgress(0)
      setProgressMessage('开始分析...')
      setProgressStage('')

      // 清空之前的分析结果，准备接收新的分析结果
      setAnalysis(prev => prev ? {
        ...prev,
        fusion_summary: '',
        news_report: '',
        sec_report: '',
        fundamentals_report: '',
        technical_report: '',
        custom_skill_report: '',
        status: 'analyzing'
      } : null)

      // 使用流式 API
      cancelStreamRef.current = analysisApi.analyzeTickerStream(
        ticker,
        (data: StreamEvent) => {
          const agentFieldMap: Record<string, keyof AnalysisData> = {
            'news_agent': 'news_report',
            'sec_agent': 'sec_report',
            'fundamentals_agent': 'fundamentals_report',
            'technical_agent': 'technical_report',
            'custom_skill_agent': 'custom_skill_report',
          }

          if (data.type === 'start') {
            setProgress(data.progress || 0)
            setProgressMessage(data.message || '开始分析...')
          } else if (data.type === 'progress') {
            setProgress(data.progress)
            setProgressMessage(data.message)
            setProgressStage(data.stage)

            // 实时更新子 Agent 卡片：当某个 Agent 完成时，立即显示其报告
            if (data.agent_name && data.agent_content) {
              const field = agentFieldMap[data.agent_name]
              if (field) {
                setAnalysis(prev => ({
                  ...(prev || { ticker, status: 'analyzing' }),
                  ticker: prev?.ticker || ticker,
                  [field]: data.agent_content,
                  status: 'analyzing'
                }))
              }
            }
          } else if (data.type === 'agent_result') {
            // 后端分拆发送的各 Agent 最终输出
            if (data.agent_name && data.agent_content) {
              const field = agentFieldMap[data.agent_name]
              if (field) {
                setAnalysis(prev => ({
                  ...(prev || { ticker, status: 'analyzing' }),
                  ticker: prev?.ticker || ticker,
                  [field]: data.agent_content,
                  status: 'analyzing'
                }))
              }
            }
          } else if (data.type === 'fusion_result') {
            // 后端分拆发送的 Fusion 输出
            const fusionContent = typeof data.fusion_output === 'string'
              ? data.fusion_output
              : JSON.stringify(data.fusion_output || '')
            setAnalysis(prev => ({
              ...(prev || { ticker, status: 'analyzing' }),
              ticker: prev?.ticker || ticker,
              fusion_summary: fusionContent,
              status: 'analyzing'
            }))
            setProgress(95)
            setProgressMessage('Fusion Agent 融合完成')
            setProgressStage('fusion')
          } else if (data.type === 'complete') {
            setProgress(100)
            setProgressMessage('分析完成')
            // 标记分析完成（数据已通过 agent_result / fusion_result 事件更新）
            setAnalysis(prev => prev ? { ...prev, status: 'completed' } : null)
            setAnalyzing(false)
          } else if (data.type === 'error') {
            setProgressMessage(`错误: ${data.message}`)
            setAnalyzing(false)
          }
        },
        (error) => {
          setProgressMessage(`错误: ${error}`)
          setAnalyzing(false)
        }
      )
    } catch (err) {
      alert('重新分析失败，请重试')
      console.error('Failed to reanalyze:', err)
      setAnalyzing(false)
    }
  }, [ticker])
  
  // 取消分析
  const handleCancelAnalysis = () => {
    if (cancelStreamRef.current) {
      cancelStreamRef.current()
      cancelStreamRef.current = null
    }
    setAnalyzing(false)
    setProgress(0)
    setProgressMessage('已取消')
  }

  // Fetch analysis data on load
  const fetchAnalysis = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch market data
      const [profileData, quoteData] = await Promise.all([
        marketApi.getProfile(ticker).catch(() => null),
        marketApi.getQuote(ticker).catch(() => null)
      ])

      // Initialize analysis data with market data only
      const initialAnalysis: AnalysisData = {
        ticker,
        company_name: profileData?.company_name || `${ticker} 公司`,
        current_price: quoteData?.price || 0,
        change_percent: quoteData?.change_percent || 0,
        fusion_summary: '',
        news_report: '',
        sec_report: '',
        fundamentals_report: '',
        technical_report: '',
        custom_skill_report: '',
        status: 'pending'
      }

      setAnalysis(initialAnalysis)

      // Start analysis immediately
      handleReanalyze()
    } catch (err) {
      setError('加载分析数据失败')
      console.error('Failed to fetch analysis:', err)
    } finally {
      setLoading(false)
    }
  }, [ticker, handleReanalyze])

  // Load data on initial render
  useEffect(() => {
    fetchAnalysis()
  }, [fetchAnalysis])

  const toggleCollapse = (key: keyof typeof collapsed) => {
    setCollapsed(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const renderMarkdown = (content: string) => {
    // Simple markdown rendering
    const lines = content.split('\n')
    return lines.map((line, index) => {
      if (line.startsWith('## ')) {
        return <h3 key={index} className="text-xl font-bold mt-4 mb-2">{line.replace('## ', '')}</h3>
      } else if (line.startsWith('### ')) {
        return <h4 key={index} className="text-lg font-semibold mt-3 mb-1">{line.replace('### ', '')}</h4>
      } else if (line.startsWith('- ')) {
        return <li key={index} className="ml-4">{line.replace('- ', '')}</li>
      } else if (line.startsWith('**') && line.endsWith('**')) {
        return <p key={index} className="font-semibold mt-2 mb-1">{line.replace(/\*\*/g, '')}</p>
      } else if (line.trim()) {
        return <p key={index} className="mb-1">{line}</p>
      }
      return <br key={index} />
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">加载中...</div>
      </div>
    )
  }

  if (error && !analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">{ticker} 分析报告</h1>
            <div className="flex items-center gap-3">
              <span className="text-base text-gray-600 dark:text-gray-300">{analysis?.company_name}</span>
              <Badge variant={analysis?.status === 'completed' ? 'default' : 'secondary'}>
                {analysis?.status === 'completed' ? '已完成' : '分析中'}
              </Badge>
            </div>
          </div>
          <div className="flex gap-2">
            {analyzing && (
              <Button variant="outline" onClick={handleCancelAnalysis}>
                取消
              </Button>
            )}
            <Button onClick={handleReanalyze} disabled={analyzing}>
              {analyzing ? '分析中...' : '重新分析'}
            </Button>
          </div>
        </div>
        
        {/* Progress Bar */}
        {analyzing && (
          <Card className="mb-6 border-2 border-blue-500">
            <CardContent className="p-6">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-blue-600">
                    {progressStage === 'supervisor' && '📋 Supervisor 任务拆解'}
                    {progressStage === 'agents' && '🤖 专项 Agent 分析'}
                    {progressStage === 'fusion' && '🔄 Fusion 融合结果'}
                    {!progressStage && '正在分析...'}
                  </span>
                  <span className="text-gray-500">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-blue-500 h-full rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600">{progressMessage}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Price Info */}
        <Card className="mb-4">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mb-0.5">当前价格</div>
                <div className="text-2xl font-bold">
                  ${analysis?.current_price?.toFixed(2) || '0.00'}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mb-0.5">涨跌幅</div>
                <div className={`text-xl font-semibold ${(analysis?.change_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(analysis?.change_percent || 0) >= 0 ? '+' : ''}{(analysis?.change_percent || 0).toFixed(2)}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Fusion Summary */}
        <Card className="mb-4 border-2 border-blue-500 dark:border-blue-700">
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-blue-600 dark:text-blue-400 text-lg">Fusion Agent 融合总结</CardTitle>
            <CardDescription className="text-sm">多Agent综合分析结果</CardDescription>
          </CardHeader>
          <CardContent className="pt-0 px-4 pb-4">
            <div className="prose prose-slate dark:prose-invert max-w-none text-sm">
              {analysis?.fusion_summary ? (
                renderMarkdown(analysis.fusion_summary)
              ) : analyzing ? (
                <div className="flex items-center gap-2 text-gray-400 py-3">
                  <span className="animate-spin">⏳</span>
                  <span>等待所有专项 Agent 完成后进行融合分析...</span>
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>

        {/* Individual Agent Reports */}
        <div className="space-y-3">
          {[
            { key: 'news', title: 'News Agent 报告', emoji: '📰', content: analysis?.news_report },
            { key: 'sec', title: 'SEC Agent 报告', emoji: '📋', content: analysis?.sec_report },
            { key: 'fundamentals', title: 'Fundamentals Agent 报告', emoji: '📊', content: analysis?.fundamentals_report },
            { key: 'technical', title: 'Technical Agent 报告', emoji: '📈', content: analysis?.technical_report },
            { key: 'custom_skill', title: 'Custom Skill Agent 报告', emoji: '🔧', content: analysis?.custom_skill_report },
          ].map((report) => (
            <Card key={report.key} className={report.content ? '' : analyzing ? 'opacity-70' : 'hidden'}>
              <CardHeader
                className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors py-2 px-3"
                onClick={() => toggleCollapse(report.key as keyof typeof collapsed)}
              >
                <div className="flex justify-between items-center">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <span>{report.emoji}</span>
                    {report.title}
                    {!report.content && analyzing && (
                      <span className="text-xs font-normal text-gray-400 animate-pulse">分析中...</span>
                    )}
                    {report.content && analyzing && (
                      <Badge variant="outline" className="text-green-600 border-green-300 dark:text-green-400 dark:border-green-700 text-xs">✓ 完成</Badge>
                    )}
                  </CardTitle>
                  <span className="text-gray-400 text-sm">
                    {collapsed[report.key as keyof typeof collapsed] ? '▼' : '▲'}
                  </span>
                </div>
              </CardHeader>
              {!collapsed[report.key as keyof typeof collapsed] && (
                <CardContent className="pt-0 px-3 pb-3">
                  {report.content ? (
                    <div className="prose prose-slate dark:prose-invert max-w-none text-sm">
                      {renderMarkdown(report.content)}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-gray-400 py-3">
                      <span className="animate-spin">⏳</span>
                      <span>正在分析中，请稍候...</span>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
