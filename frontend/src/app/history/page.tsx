'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { analysisApi } from '@/lib/api'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import MarkdownRenderer from '@/components/MarkdownRenderer'

interface AnalysisTask {
  task_id: string
  ticker: string
  company_name: string
  status: string
  progress: number
  progress_message: string
  progress_stage?: string
  report_id?: string
  error_message?: string
  created_at: string
  updated_at: string
}

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

export default function HistoryPage() {
  const [reports, setReports] = useState<AnalysisReport[]>([])
  const [tasks, setTasks] = useState<AnalysisTask[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTicker, setSearchTicker] = useState('')
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null)
  const [expandedReports, setExpandedReports] = useState<Set<string>>(new Set())
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [showTasks, setShowTasks] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [reportsData, tasksData] = await Promise.all([
        analysisApi.getReports(),
        analysisApi.getAnalysisTasks()
      ])
      // 确保数据是数组类型
      setReports(Array.isArray(reportsData) ? reportsData : [])
      setTasks(Array.isArray(tasksData) ? tasksData : [])
    } catch (err) {
      console.error('Failed to fetch data:', err)
      setReports([])
      setTasks([])
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (reportId: string) => {
    if (!confirm('确定要删除该分析报告吗？此操作无法撤销。')) {
      return
    }

    try {
      setDeleteLoading(reportId)
      await analysisApi.deleteReport(reportId)
      setReports(reports.filter(report => report.report_id !== reportId))
    } catch (err) {
      console.error('Failed to delete report:', err)
    } finally {
      setDeleteLoading(null)
    }
  }

  const filteredReports = searchTicker && Array.isArray(reports)
    ? reports.filter(report => report.ticker.toLowerCase().includes(searchTicker.toLowerCase()))
    : Array.isArray(reports)
    ? reports
    : []

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'yyyy年MM月dd日 HH:mm:ss', { locale: zhCN })
    } catch (error) {
      return dateString
    }
  }

  const toggleReportExpanded = (reportId: string) => {
    const newExpanded = new Set(expandedReports)
    if (newExpanded.has(reportId)) {
      newExpanded.delete(reportId)
    } else {
      newExpanded.add(reportId)
    }
    setExpandedReports(newExpanded)
  }

  const toggleSectionExpanded = (sectionKey: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey)
    } else {
      newExpanded.add(sectionKey)
    }
    setExpandedSections(newExpanded)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">加载中...</div>
      </div>
    )
  }

  // 筛选任务列表
  const filteredTasks = searchTicker && Array.isArray(tasks)
    ? tasks.filter(task => task.ticker.toLowerCase().includes(searchTicker.toLowerCase()))
    : Array.isArray(tasks)
    ? tasks
    : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">分析报告历史</h1>

        <Card className="mb-4">
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-lg">搜索和筛选</CardTitle>
            <CardDescription className="text-sm">查找特定股票的分析报告和任务</CardDescription>
          </CardHeader>
          <CardContent className="pt-0 px-4 pb-4">
            <div className="flex flex-col md:flex-row gap-3">
              <Input
                type="text"
                placeholder="搜索股票代码..."
                value={searchTicker}
                onChange={(e) => setSearchTicker(e.target.value)}
                className="max-w-md"
              />
              <Button onClick={fetchData} size="sm">刷新数据</Button>
              <Button variant="outline" size="sm" onClick={() => setShowTasks(!showTasks)}>
                {showTasks ? '显示报告' : '显示任务'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 任务列表 */}
        {showTasks && filteredTasks.length > 0 && (
          <Card className="mb-4">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-lg">分析任务状态</CardTitle>
              <CardDescription className="text-sm">共 {filteredTasks.length} 个任务</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              <div className="space-y-3">
                {filteredTasks.map((task) => (
                  <div
                    key={task.task_id}
                    className="border rounded-lg p-3 dark:border-gray-700"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{task.ticker}</Badge>
                        <Badge variant={
                          task.status === 'completed' ? 'default' :
                          task.status === 'analyzing' ? 'secondary' :
                          task.status === 'failed' ? 'destructive' : 'outline'
                        }>
                          {task.status === 'pending' ? '待处理' :
                           task.status === 'analyzing' ? '分析中' :
                           task.status === 'completed' ? '已完成' : '失败'}
                        </Badge>
                      </div>
                      {task.status === 'analyzing' && (
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                          <span className="text-xs text-gray-500">{task.progress}%</span>
                        </div>
                      )}
                    </div>
                    <p className="text-sm font-medium mb-1">{task.company_name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      创建时间: {formatDate(task.created_at)}
                    </p>
                    {task.progress_message && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {task.progress_message}
                      </p>
                    )}
                    {task.error_message && (
                      <p className="text-xs text-red-500 dark:text-red-400 mt-1">
                        错误: {task.error_message}
                      </p>
                    )}
                    {task.report_id && (
                      <div className="mt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            document
                              .getElementById(`report-${task.report_id}`)
                              ?.scrollIntoView({ behavior: 'smooth' })
                          }
                        >
                          查看报告
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* 报告列表 */}
          <Card className="lg:col-span-1">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-lg">报告列表</CardTitle>
              <CardDescription className="text-sm">共 {filteredReports.length} 条报告</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {filteredReports.length === 0 ? (
                  <div className="text-center py-6 text-gray-500 dark:text-gray-400">
                    {searchTicker ? '未找到匹配的报告' : '暂无分析报告'}
                  </div>
                ) : (
                  filteredReports.map((report) => (
                    <Card
                      key={report.report_id}
                      className="cursor-pointer hover:border-blue-400 transition-colors"
                      onClick={() =>
                        document
                          .getElementById(`report-${report.report_id}`)
                          ?.scrollIntoView({ behavior: 'smooth' })
                      }
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{report.ticker}</Badge>
                            <Badge variant={
                              report.status === 'completed' ? 'default' : 'secondary'
                            }>
                              {report.status === 'completed' ? '已完成' : report.status}
                            </Badge>
                          </div>
                          <Button
                            variant="destructive"
                            size="sm"
                            disabled={deleteLoading === report.report_id}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDelete(report.report_id)
                            }}
                          >
                            {deleteLoading === report.report_id ? '删除中...' : '删除'}
                          </Button>
                        </div>
                        <p className="text-sm font-medium mb-1">{report.company_name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          创建时间: {formatDate(report.created_at)}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          价格: ${report.current_price.toFixed(2)}
                          <span
                            className={
                              report.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                            }
                          >
                            {' '}
                            ({report.change_percent >= 0 ? '+' : ''}
                            {report.change_percent.toFixed(2)}%)
                          </span>
                        </p>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* 报告详情 */}
          <Card className="lg:col-span-2">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-lg">报告详情</CardTitle>
              <CardDescription className="text-sm">点击左侧报告查看详细内容</CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-4 pb-4">
              <div className="space-y-3">
                {filteredReports.length === 0 ? (
                  <div className="text-center py-10 text-muted-foreground">
                    选择一个报告查看详情
                  </div>
                ) : (
                  filteredReports.map((report) => (
                    <div
                      key={report.report_id}
                      id={`report-${report.report_id}`}
                      className="border rounded-lg p-3 dark:border-gray-700"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <Badge variant="outline">{report.ticker}</Badge>
                        <h3 className="text-lg font-semibold">
                          {report.company_name}
                        </h3>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">创建时间</p>
                          <p className="font-medium text-sm">{formatDate(report.created_at)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">当前价格</p>
                          <p className="font-medium text-sm font-mono-nums">
                            ${report.current_price.toFixed(2)}
                            <span
                              className={
                                report.change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                              }
                            >
                              {' '}
                              ({report.change_percent >= 0 ? '+' : ''}
                              {report.change_percent.toFixed(2)}%)
                            </span>
                          </p>
                        </div>
                      </div>

                      {report.fusion_summary && (
                        <div className="mb-4" data-testid="fusion-summary">
                          <div className="flex items-center justify-between mb-1.5">
                            <h4 className="text-base font-semibold text-blue-600 dark:text-blue-400">
                              Fusion Agent 融合总结
                            </h4>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toggleSectionExpanded(`fusion-${report.report_id}`)}
                            >
                              {expandedSections.has(`fusion-${report.report_id}`) ? '收起' : '展开'}
                            </Button>
                          </div>
                          {expandedSections.has(`fusion-${report.report_id}`) ? (
                            <MarkdownRenderer content={report.fusion_summary} />
                          ) : (
                            <div className="text-sm text-gray-700 dark:text-gray-300">
                              {report.fusion_summary.substring(0, 200)}...
                            </div>
                          )}
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {[
                          { title: 'News Agent', content: report.news_report, emoji: '📰' },
                          { title: 'SEC Agent', content: report.sec_report, emoji: '📋' },
                          { title: 'Fundamentals Agent', content: report.fundamentals_report, emoji: '📊' },
                          { title: 'Technical Agent', content: report.technical_report, emoji: '📈' },
                          { title: 'Custom Skill Agent', content: report.custom_skill_report, emoji: '🔧' },
                        ].map(({ title, content, emoji }) => {
                          const sectionKey = `${title.toLowerCase().replace(/\s+/g, '-')}-${report.report_id}`
                          return (
                            <div key={title} className="border rounded-lg p-2.5" data-testid="agent-report">
                              <div className="flex items-center justify-between mb-1.5">
                                <h5 className="font-semibold flex items-center gap-2 text-sm">
                                  <span>{emoji}</span>
                                  {title}
                                </h5>
                                {content && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => toggleSectionExpanded(sectionKey)}
                                  >
                                    {expandedSections.has(sectionKey) ? '收起' : '展开'}
                                  </Button>
                                )}
                              </div>
                              {content ? (
                                expandedSections.has(sectionKey) ? (
                                  <MarkdownRenderer content={content} />
                                ) : (
                                  <div className="text-xs text-gray-500 dark:text-gray-400">
                                    {content.substring(0, 100)}...
                                  </div>
                                )
                              ) : (
                                <p className="text-xs text-gray-400 italic">暂无内容</p>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
