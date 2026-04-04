'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { portfolioApi, analysisApi } from '@/lib/api'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

interface PortfolioItem {
  ticker: string
  quantity: number
  avg_cost: number
  current_price?: number
  total_cost?: number
  market_value?: number
  profit_loss?: number
  profit_loss_percent?: number
}

interface Summary {
  total_market_value: number
  total_cost: number
  total_profit_loss: number
  total_profit_loss_percent: number
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([])
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [summaryData, portfolioData] = await Promise.all([
        portfolioApi.getSummary().catch(() => null),
        portfolioApi.getAll().catch(() => [])
      ])

      if (summaryData) {
        setSummary(summaryData)
      } else {
        // Mock data if API fails
        setSummary({
          total_market_value: 0,
          total_cost: 0,
          total_profit_loss: 0,
          total_profit_loss_percent: 0
        })
      }

      if (portfolioData.length > 0) {
        // Map backend fields to frontend expected fields
        const mappedPortfolio = portfolioData.map((item: any) => ({
          ticker: item.ticker,
          quantity: item.quantity,
          avg_cost: item.cost_price || item.avg_cost || 0,
          current_price: item.current_price || 0,
          total_cost: item.total_cost || (item.quantity * (item.cost_price || item.avg_cost || 0)),
          market_value: item.market_value || 0,
          profit_loss: item.profit_loss || 0,
          profit_loss_percent: item.profit_loss_percent || 0,
        }))
        setPortfolio(mappedPortfolio)
      } else {
        // Mock data
        setPortfolio([
          { ticker: 'AAPL', quantity: 100, avg_cost: 150.00, current_price: 175.50, total_cost: 15000, market_value: 17550, profit_loss: 2550, profit_loss_percent: 17.0 },
          { ticker: 'GOOGL', quantity: 50, avg_cost: 120.00, current_price: 135.20, total_cost: 6000, market_value: 6760, profit_loss: 760, profit_loss_percent: 12.67 },
          { ticker: 'TSLA', quantity: 30, avg_cost: 200.00, current_price: 180.50, total_cost: 6000, market_value: 5415, profit_loss: -585, profit_loss_percent: -9.75 },
        ])
      }
    } catch (err) {
      setError('加载数据失败，请检查后端服务是否启动')
      console.error('Failed to fetch data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzePortfolio = async () => {
    try {
      setAnalyzing(true)
      const tickers = portfolio.map(item => item.ticker)
      await analysisApi.analyzePortfolio(tickers)
      alert('分析已开始，请稍后在分析页面查看结果')
    } catch (err) {
      alert('分析失败，请重试')
      console.error('Failed to analyze portfolio:', err)
    } finally {
      setAnalyzing(false)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2
    }).format(value)
  }

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  const pieData = portfolio.map(item => ({
    name: item.ticker,
    value: item.market_value || 0,
    profit_loss: item.profit_loss || 0
  }))

  const COLORS = portfolio.map(item => 
    (item.profit_loss || 0) >= 0 ? '#10b981' : '#ef4444'
  )

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">加载中...</div>
      </div>
    )
  }

  if (error && !summary) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">投资仪表盘</h1>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>总市值</CardDescription>
              <CardTitle className="text-2xl">{formatCurrency(summary?.total_market_value || 0)}</CardTitle>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>总成本</CardDescription>
              <CardTitle className="text-2xl">{formatCurrency(summary?.total_cost || 0)}</CardTitle>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>总盈亏</CardDescription>
              <CardTitle className={`text-2xl ${(summary?.total_profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(summary?.total_profit_loss || 0)}
              </CardTitle>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>盈亏率</CardDescription>
              <CardTitle className={`text-2xl ${(summary?.total_profit_loss_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercent(summary?.total_profit_loss_percent || 0)}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Pie Chart */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>持仓分布</CardTitle>
              <CardDescription>按市值分布</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Portfolio Table */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>持仓列表</CardTitle>
              <CardDescription>当前所有持仓</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2">代码</th>
                      <th className="text-right py-3 px-2">数量</th>
                      <th className="text-right py-3 px-2">成本价</th>
                      <th className="text-right py-3 px-2">当前价</th>
                      <th className="text-right py-3 px-2">盈亏</th>
                      <th className="text-right py-3 px-2">盈亏率</th>
                      <th className="text-center py-3 px-2">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.map((item) => (
                      <tr key={item.ticker} className="border-b hover:bg-slate-50">
                        <td className="py-3 px-2 font-medium">{item.ticker}</td>
                        <td className="text-right py-3 px-2">{item.quantity}</td>
                        <td className="text-right py-3 px-2">{formatCurrency(item.avg_cost)}</td>
                        <td className="text-right py-3 px-2">{formatCurrency(item.current_price || 0)}</td>
                        <td className={`text-right py-3 px-2 ${(item.profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(item.profit_loss || 0)}
                        </td>
                        <td className={`text-right py-3 px-2 ${(item.profit_loss_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatPercent(item.profit_loss_percent || 0)}
                        </td>
                        <td className="text-center py-3 px-2">
                          <Link href={`/analysis/${item.ticker}`}>
                            <Button variant="outline" size="sm">
                              分析
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Analyze Button */}
        <div className="flex justify-center">
          <Button 
            onClick={handleAnalyzePortfolio}
            disabled={analyzing || portfolio.length === 0}
            size="lg"
            className="w-full md:w-auto"
          >
            {analyzing ? '分析中...' : '今日分析'}
          </Button>
        </div>
      </div>
    </div>
  )
}
