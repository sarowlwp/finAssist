'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { portfolioApi } from '@/lib/api'

interface PortfolioItem {
  ticker: string
  quantity: number
  cost_price: number
  note?: string
}

interface FormData {
  ticker: string
  quantity: string
  cost_price: string
  note: string
}

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([])
  const [loading, setLoading] = useState(true)
  const [editingItem, setEditingItem] = useState<PortfolioItem | null>(null)
  const [formData, setFormData] = useState<FormData>({
    ticker: '',
    quantity: '',
    cost_price: '',
    note: ''
  })
  const [searchQuery, setSearchQuery] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchPortfolio()
  }, [])

  const fetchPortfolio = async () => {
    try {
      setLoading(true)
      const data = await portfolioApi.getAll()
      setPortfolio(data)
    } catch (err) {
      console.error('Failed to fetch portfolio:', err)
      // Mock data if API fails
      setPortfolio([
        { ticker: 'AAPL', quantity: 100, cost_price: 150.00, note: '长期持有' },
        { ticker: 'GOOGL', quantity: 50, cost_price: 120.00, note: '科技股' },
        { ticker: 'TSLA', quantity: 30, cost_price: 200.00, note: '新能源' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.ticker || !formData.quantity || !formData.cost_price) {
      alert('请填写必填字段')
      return
    }

    try {
      setSaving(true)
      const data = {
        ticker: formData.ticker.toUpperCase(),
        quantity: parseFloat(formData.quantity),
        cost_price: parseFloat(formData.cost_price),
        note: formData.note
      }

      if (editingItem) {
        await portfolioApi.update(editingItem.ticker, data)
      } else {
        await portfolioApi.add(data)
      }

      await fetchPortfolio()
      resetForm()
    } catch (err) {
      alert('保存失败，请重试')
      console.error('Failed to save portfolio item:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = (item: PortfolioItem) => {
    setEditingItem(item)
    setFormData({
      ticker: item.ticker,
      quantity: item.quantity.toString(),
      cost_price: item.cost_price.toString(),
      note: item.note || ''
    })
  }

  const handleDelete = async (ticker: string) => {
    if (!confirm(`确定要删除 ${ticker} 吗？`)) {
      return
    }

    try {
      await portfolioApi.remove(ticker)
      await fetchPortfolio()
    } catch (err) {
      alert('删除失败，请重试')
      console.error('Failed to delete portfolio item:', err)
    }
  }

  const resetForm = () => {
    setEditingItem(null)
    setFormData({
      ticker: '',
      quantity: '',
      cost_price: '',
      note: ''
    })
  }

  const filteredPortfolio = portfolio.filter(item =>
    item.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (item.note && item.note.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">持仓管理</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>{editingItem ? '编辑持仓' : '添加持仓'}</CardTitle>
              <CardDescription>
                {editingItem ? '修改持仓信息' : '添加新的持仓到投资组合'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">股票代码 *</label>
                  <Input
                    type="text"
                    placeholder="例如: AAPL"
                    value={formData.ticker}
                    onChange={(e) => setFormData({ ...formData, ticker: e.target.value.toUpperCase() })}
                    disabled={!!editingItem}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">数量 *</label>
                  <Input
                    type="number"
                    placeholder="例如: 100"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    step="0.01"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">成本价 *</label>
                  <Input
                    type="number"
                    placeholder="例如: 150.00"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                    step="0.01"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">备注</label>
                  <Textarea
                    placeholder="添加备注信息..."
                    value={formData.note}
                    onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                    rows={3}
                  />
                </div>
                
                <div className="flex gap-2">
                  <Button type="submit" disabled={saving} className="flex-1">
                    {saving ? '保存中...' : (editingItem ? '更新' : '添加')}
                  </Button>
                  {editingItem && (
                    <Button type="button" variant="outline" onClick={resetForm}>
                      取消
                    </Button>
                  )}
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Portfolio List */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>持仓列表</CardTitle>
              <CardDescription>管理您的投资组合</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Input
                  type="text"
                  placeholder="搜索股票代码或备注..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {loading ? (
                <div className="text-center py-8">加载中...</div>
              ) : filteredPortfolio.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {searchQuery ? '没有找到匹配的持仓' : '暂无持仓数据'}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-2">代码</th>
                        <th className="text-right py-3 px-2">数量</th>
                        <th className="text-right py-3 px-2">成本价</th>
                        <th className="text-left py-3 px-2">备注</th>
                        <th className="text-center py-3 px-2">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPortfolio.map((item) => (
                        <tr key={item.ticker} className="border-b hover:bg-slate-50">
                          <td className="py-3 px-2 font-medium">{item.ticker}</td>
                          <td className="text-right py-3 px-2">{item.quantity}</td>
                          <td className="text-right py-3 px-2">
                            ${item.cost_price.toFixed(2)}
                          </td>
                          <td className="py-3 px-2 text-sm text-gray-600">
                            {item.note || '-'}
                          </td>
                          <td className="text-center py-3 px-2">
                            <div className="flex gap-2 justify-center">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleEdit(item)}
                              >
                                编辑
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDelete(item.ticker)}
                              >
                                删除
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
