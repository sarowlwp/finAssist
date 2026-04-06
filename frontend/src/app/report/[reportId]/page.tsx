'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabList, TabTrigger, TabContent } from '@/components/ui/tabs'
import { analysisApi } from '@/lib/api'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface AnalysisReport {
  report_id: string
  ticker: string
  company_name: string
  created_at: string
  status: string
  current_price: number
  change_percent: number
  fusion_summary: string
  news_report: string
  sec_report: string
  fundamentals_report: string
  technical_report: string
  custom_skill_report: string
}

export default function ReportPage() {
  const params = useParams()
  const router = useRouter()
  const reportId = params.reportId as string
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true)
        const reportData = await analysisApi.getReport(reportId)
        setReport(reportData)
      } catch (err) {
        setError('加载报告失败')
        console.error('Failed to fetch report:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchReport()
  }, [reportId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">加载中...</div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500">
          {error || '未找到报告'}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold">分析报告详情</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {report.company_name} ({report.ticker})
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push('/history')}>
              返回历史列表
            </Button>
          </div>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{report.ticker}</Badge>
              <CardTitle className="text-lg">{report.company_name}</CardTitle>
            </div>
            <CardDescription>
              报告 ID: {report.report_id} | 创建时间: {format(new Date(report.created_at), 'yyyy年MM月dd日 HH:mm:ss', { locale: zhCN })}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">股票代码</p>
                <p className="font-semibold">{report.ticker}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">当前价格</p>
                <p className="font-semibold">${report.current_price.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">涨跌幅</p>
                <p className={`font-semibold ${report.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {report.change_percent >= 0 ? '+' : ''}{report.change_percent.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">状态</p>
                <Badge variant={report.status === 'completed' ? 'default' : 'secondary'}>
                  {report.status === 'completed' ? '已完成' : report.status}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {report.fusion_summary && (
          <Card className="mb-6 border-2 border-blue-500 dark:border-blue-700">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-blue-600 dark:text-blue-400 text-lg">Fusion Agent 融合总结</CardTitle>
              <CardDescription className="text-sm">多Agent综合分析结果</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              <div className="prose prose-slate dark:prose-invert max-w-none text-sm">
                <MarkdownRenderer content={report.fusion_summary} />
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs defaultValue="news">
          <TabList>
            <TabTrigger value="news">📰 News Agent</TabTrigger>
            <TabTrigger value="sec">📋 SEC Agent</TabTrigger>
            <TabTrigger value="fundamentals">📊 Fundamentals Agent</TabTrigger>
            <TabTrigger value="technical">📈 Technical Agent</TabTrigger>
            <TabTrigger value="custom">🔧 Custom Skill Agent</TabTrigger>
          </TabList>

          <TabContent value="news">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>📰</span>
                  News Agent
                </CardTitle>
              </CardHeader>
              <CardContent>
                {report.news_report ? (
                  <div className="prose prose-slate dark:prose-invert max-w-none">
                    <MarkdownRenderer content={report.news_report} />
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无内容</div>
                )}
              </CardContent>
            </Card>
          </TabContent>

          <TabContent value="sec">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>📋</span>
                  SEC Agent
                </CardTitle>
              </CardHeader>
              <CardContent>
                {report.sec_report ? (
                  <div className="prose prose-slate dark:prose-invert max-w-none">
                    <MarkdownRenderer content={report.sec_report} />
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无内容</div>
                )}
              </CardContent>
            </Card>
          </TabContent>

          <TabContent value="fundamentals">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>📊</span>
                  Fundamentals Agent
                </CardTitle>
              </CardHeader>
              <CardContent>
                {report.fundamentals_report ? (
                  <div className="prose prose-slate dark:prose-invert max-w-none">
                    <MarkdownRenderer content={report.fundamentals_report} />
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无内容</div>
                )}
              </CardContent>
            </Card>
          </TabContent>

          <TabContent value="technical">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>📈</span>
                  Technical Agent
                </CardTitle>
              </CardHeader>
              <CardContent>
                {report.technical_report ? (
                  <div className="prose prose-slate dark:prose-invert max-w-none">
                    <MarkdownRenderer content={report.technical_report} />
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无内容</div>
                )}
              </CardContent>
            </Card>
          </TabContent>

          <TabContent value="custom">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>🔧</span>
                  Custom Skill Agent
                </CardTitle>
              </CardHeader>
              <CardContent>
                {report.custom_skill_report ? (
                  <div className="prose prose-slate dark:prose-invert max-w-none">
                    <MarkdownRenderer content={report.custom_skill_report} />
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无内容</div>
                )}
              </CardContent>
            </Card>
          </TabContent>
        </Tabs>
      </div>
    </div>
  )
}
