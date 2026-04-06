'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Modal } from '@/components/ui/modal'
import { portfolioApi } from '@/lib/api'

interface PortfolioItem {
  ticker: string
  quantity: number
  cost_price: number
  note?: string
  created_at?: string
  updated_at?: string
  current_price?: number
  market_value?: number
  total_cost?: number
  profit_loss?: number
  profit_loss_percent?: number
}

interface FormData {
  ticker: string
  quantity: string
  cost_price: string
  note: string
}

// 防抖函数
function debounce<T extends (...args: any[]) => any>(func: T, delay: number): T {
  let timeoutId: NodeJS.Timeout
  return ((...args: any[]) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }) as unknown as T
}

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([])
  const [loading, setLoading] = useState(true)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false)
  const [editingNoteItem, setEditingNoteItem] = useState<PortfolioItem | null>(null)
  const [formData, setFormData] = useState<FormData>({
    ticker: '',
    quantity: '',
    cost_price: '',
    note: ''
  })
  const [searchQuery, setSearchQuery] = useState('')
  const [saving, setSaving] = useState<string | null>(null)
  const [noteFormData, setNoteFormData] = useState('')

  // 用于跟踪正在编辑的单元格
  const [editingCell, setEditingCell] = useState<{
    ticker: string
    field: 'quantity' | 'cost_price'
    value: string
  } | null>(null)

  // 防抖保存函数
  const debouncedSave = useRef(
    debounce(async (ticker: string, field: 'quantity' | 'cost_price', value: number) => {
      try {
        setSaving(ticker)
        await portfolioApi.update(ticker, { [field]: value })
        // 更新本地状态
        setPortfolio(prev => prev.map(item =>
          item.ticker === ticker ? { ...item, [field]: value } : item
        ))
      } catch (err) {
        console.error('保存失败:', err)
        // 失败时恢复原数据
        const originalItem = portfolio.find(item => item.ticker === ticker)
        if (originalItem) {
          setPortfolio(prev => prev.map(item =>
            item.ticker === ticker ? originalItem : item
          ))
        }
      } finally {
        setSaving(null)
        setEditingCell(null)
      }
    }, 500)
  ).current

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
        { ticker: 'TSLA', quantity: 0, cost_price: 200.00, note: '关注中' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.ticker || !formData.quantity || !formData.cost_price) {
      alert('请填写必填字段')
      return
    }

    try {
      const data = {
        ticker: formData.ticker.toUpperCase(),
        quantity: parseFloat(formData.quantity),
        cost_price: parseFloat(formData.cost_price),
        note: formData.note
      }

      await portfolioApi.add(data)
      await fetchPortfolio()
      resetForm()
      setIsAddModalOpen(false)
    } catch (err) {
      alert('保存失败，请重试')
      console.error('Failed to save portfolio item:', err)
    }
  }

  const handleDelete = async (ticker: string) => {
    if (!confirm(`确定要删除 ${ticker} 吗？`)) {
      return
    }

    try {
      await portfolioApi.delete(ticker)
      await fetchPortfolio()
    } catch (err) {
      alert('删除失败，请重试')
      console.error('Failed to delete portfolio item:', err)
    }
  }

  const resetForm = () => {
    setFormData({
      ticker: '',
      quantity: '',
      cost_price: '',
      note: ''
    })
  }

  const handleCellEditStart = (item: PortfolioItem, field: 'quantity' | 'cost_price') => {
    setEditingCell({
      ticker: item.ticker,
      field,
      value: String(item[field])
    })
  }

  const handleCellEditChange = (value: string) => {
    if (editingCell) {
      setEditingCell({ ...editingCell, value })
    }
  }

  const handleCellEditEnd = () => {
    if (editingCell) {
      const { ticker, field, value } = editingCell
      const parsedValue = parseFloat(value)

      // 验证输入
      if (isNaN(parsedValue) || parsedValue < 0) {
        alert(field === 'quantity' ? '数量必须大于等于0' : '成本价必须大于等于0')
        setEditingCell(null)
        return
      }

      // 更新本地状态（立即显示）
      setPortfolio(prev => prev.map(item =>
        item.ticker === ticker ? { ...item, [field]: parsedValue } : item
      ))

      // 防抖保存到服务器
      debouncedSave(ticker, field, parsedValue)
    }
  }

  const handleNoteEdit = (item: PortfolioItem) => {
    setEditingNoteItem(item)
    setNoteFormData(item.note || '')
    setIsNoteModalOpen(true)
  }

  const handleNoteSave = async () => {
    if (editingNoteItem) {
      try {
        await portfolioApi.update(editingNoteItem.ticker, { note: noteFormData })
        setPortfolio(prev => prev.map(item =>
          item.ticker === editingNoteItem.ticker
            ? { ...item, note: noteFormData }
            : item
        ))
        setIsNoteModalOpen(false)
        setEditingNoteItem(null)
      } catch (err) {
        console.error('保存备注失败:', err)
        alert('保存备注失败')
      }
    }
  }

  const filteredPortfolio = portfolio.filter(item =>
    item.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (item.note && item.note.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const isZeroQuantity = (item: PortfolioItem) => item.quantity === 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">持仓管理</h1>
          <Button onClick={() => setIsAddModalOpen(true)}>
            + 添加持仓
          </Button>
        </div>

        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-lg">持仓列表</CardTitle>
            <CardDescription className="text-sm">
              点击数量或成本价单元格可直接编辑，修改后自动保存
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0 px-4 pb-4">
            <div className="mb-3">
              <Input
                type="text"
                placeholder="搜索股票代码或备注..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {loading ? (
              <div className="text-center py-6">加载中...</div>
            ) : filteredPortfolio.length === 0 ? (
              <div className="text-center py-6 text-gray-500 dark:text-gray-400">
                {searchQuery ? '没有找到匹配的持仓' : '暂无持仓数据，点击上方按钮添加'}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b dark:border-gray-700">
                      <th className="text-left py-2 px-2">代码</th>
                      <th className="text-right py-2 px-2">数量</th>
                      <th className="text-right py-2 px-2">成本价</th>
                      <th className="text-left py-2 px-2">备注</th>
                      <th className="text-center py-2 px-2">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPortfolio.map((item) => {
                      const isEditing = editingCell?.ticker === item.ticker
                      const isSaving = saving === item.ticker
                      const isZeroQty = isZeroQuantity(item)

                      return (
                        <tr
                          key={item.ticker}
                          className={`border-b dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors ${
                            isZeroQty ? 'text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800' : ''
                          }`}
                        >
                          <td className="py-2 px-2 font-medium">
                            {item.ticker}
                            {isZeroQty && (
                              <span className="ml-2 text-xs bg-gray-400 text-white px-1.5 py-0.5 rounded">
                                关注
                              </span>
                            )}
                          </td>
                          <td className="text-right py-2 px-2">
                            {isEditing && editingCell?.field === 'quantity' ? (
                              <Input
                                type="number"
                                value={editingCell.value}
                                onChange={(e) => handleCellEditChange(e.target.value)}
                                onBlur={handleCellEditEnd}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleCellEditEnd()
                                  if (e.key === 'Escape') setEditingCell(null)
                                }}
                                className="w-24 text-right"
                                autoFocus
                              />
                            ) : (
                              <button
                                onClick={() => handleCellEditStart(item, 'quantity')}
                                className="hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-1 rounded transition-colors"
                                disabled={isSaving}
                              >
                                {isSaving ? '保存中...' : item.quantity}
                              </button>
                            )}
                          </td>
                          <td className="text-right py-2 px-2">
                            {isEditing && editingCell?.field === 'cost_price' ? (
                              <Input
                                type="number"
                                step="0.01"
                                value={editingCell.value}
                                onChange={(e) => handleCellEditChange(e.target.value)}
                                onBlur={handleCellEditEnd}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') handleCellEditEnd()
                                  if (e.key === 'Escape') setEditingCell(null)
                                }}
                                className="w-28 text-right"
                                autoFocus
                              />
                            ) : (
                              <button
                                onClick={() => handleCellEditStart(item, 'cost_price')}
                                className="hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-1 rounded transition-colors"
                                disabled={isSaving}
                              >
                                {isSaving ? '保存中...' : `$${item.cost_price.toFixed(2)}`}
                              </button>
                            )}
                          </td>
                          <td className="py-2 px-2 text-sm text-gray-600 dark:text-gray-400">
                            {item.note || '-'}
                            <button
                              onClick={() => handleNoteEdit(item)}
                              className="ml-2 text-xs text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
                            >
                              编辑
                            </button>
                          </td>
                          <td className="text-center py-2 px-2">
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDelete(item.ticker)}
                              disabled={isSaving}
                            >
                              删除
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 添加持仓 Modal */}
        <Modal
          open={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          title="添加持仓"
          description="添加新的持仓到投资组合"
        >
          <form onSubmit={handleAddSubmit} className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1.5">股票代码 *</label>
              <Input
                type="text"
                placeholder="例如: AAPL"
                value={formData.ticker}
                onChange={(e) => setFormData({ ...formData, ticker: e.target.value.toUpperCase() })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">数量 *</label>
              <Input
                type="number"
                placeholder="例如: 100 (0表示关注)"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                step="0.01"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">成本价 *</label>
              <Input
                type="number"
                placeholder="例如: 150.00"
                value={formData.cost_price}
                onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                step="0.01"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">备注</label>
              <Textarea
                placeholder="添加备注信息..."
                value={formData.note}
                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                rows={2}
              />
            </div>

            <div className="flex gap-2 pt-2">
              <Button type="submit" className="flex-1">
                添加
              </Button>
              <Button type="button" variant="outline" onClick={() => setIsAddModalOpen(false)}>
                取消
              </Button>
            </div>
          </form>
        </Modal>

        {/* 备注编辑 Modal */}
        <Modal
          open={isNoteModalOpen}
          onClose={() => setIsNoteModalOpen(false)}
          title="编辑备注"
          description={editingNoteItem ? `编辑 ${editingNoteItem.ticker} 的备注` : ''}
        >
          <div className="space-y-3">
            <div>
              <Textarea
                value={noteFormData}
                onChange={(e) => setNoteFormData(e.target.value)}
                placeholder="输入备注信息..."
                rows={4}
              />
            </div>
            <div className="flex gap-2 pt-2">
              <Button onClick={handleNoteSave} className="flex-1">
                保存
              </Button>
              <Button type="button" variant="outline" onClick={() => setIsNoteModalOpen(false)}>
                取消
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  )
}
