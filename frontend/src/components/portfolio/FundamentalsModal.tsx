'use client'

import React, { useState, useEffect } from 'react'
import { X, Loader2 } from 'lucide-react'
import { Modal } from '@/components/ui/modal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { portfolioApi, type FundamentalsData } from '@/lib/api'
import DataRefreshButton from './DataRefreshButton'

interface FundamentalsModalProps {
  ticker: string
  isOpen: boolean
  onClose: () => void
}

const FundamentalsModal: React.FC<FundamentalsModalProps> = ({ ticker, isOpen, onClose }) => {
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [data, setData] = useState<FundamentalsData | null>(null)

  // 格式化数字
  const formatNumber = (value: number | undefined, decimals: number = 2): string => {
    if (value === undefined || value === null || isNaN(value)) {
      return '-'
    }
    return value.toFixed(decimals)
  }

  // 格式化百分比
  const formatPercentage = (value: number | undefined, decimals: number = 2): string => {
    if (value === undefined || value === null || isNaN(value)) {
      return '-'
    }
    return `${(value * 100).toFixed(decimals)}%`
  }

  // 格式化大数字（如市值）
  const formatLargeNumber = (value: number | undefined): string => {
    if (value === undefined || value === null || isNaN(value)) {
      return '-'
    }

    if (value >= 1000000000) {
      return `${(value / 1000000000).toFixed(2)}B` // 十亿
    } else if (value >= 1000000) {
      return `${(value / 1000000).toFixed(2)}M` // 百万
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}K` // 千
    }

    return value.toFixed(2)
  }

  // 加载数据
  const loadData = async () => {
    if (!isOpen || !ticker) return

    setLoading(true)
    try {
      const result = await portfolioApi.getFundamentals(ticker)
      setData(result)
    } catch (error) {
      console.error('Failed to load fundamentals:', error)
    } finally {
      setLoading(false)
    }
  }

  // 刷新数据
  const refreshData = async () => {
    if (!ticker) return

    setRefreshing(true)
    try {
      const result = await portfolioApi.refreshFundamentals(ticker)
      setData(result)
    } catch (error) {
      console.error('Failed to refresh fundamentals:', error)
    } finally {
      setRefreshing(false)
    }
  }

  // 当模态框打开时加载数据
  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen, ticker]) // eslint-disable-line react-hooks/exhaustive-deps

  // 渲染加载状态
  const renderLoading = () => (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
      <span className="ml-2 text-slate-500">加载中...</span>
    </div>
  )

  // 渲染公司概况
  const renderCompanyProfile = () => (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold">公司概况</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">公司名称</p>
            <p className="font-medium">{data?.company_profile?.company_name || data?.companyProfile?.name || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">行业</p>
            <p className="font-medium">{data?.company_profile?.industry || data?.companyProfile?.industry || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">市值</p>
            <p className="font-medium">{formatLargeNumber(data?.company_profile?.market_cap || data?.companyProfile?.marketCapitalization)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">市场</p>
            <p className="font-medium">{data?.company_profile?.exchange || data?.companyProfile?.exchange || '-'}</p>
          </div>
          <div className="md:col-span-2">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">公司描述</p>
            <p className="text-sm leading-relaxed">{data?.company_profile?.description || data?.companyProfile?.description || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">投资者关系</p>
            {data?.company_profile?.ir_website || data?.companyProfile?.ir_website ? (
              <a
                href={data.company_profile?.ir_website || data.companyProfile?.ir_website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 truncate"
              >
                {data.company_profile?.ir_website || data.companyProfile?.ir_website}
              </a>
            ) : (
              <span className="text-gray-400">-</span>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">财报信息</p>
            {data?.company_profile?.earnings_url || data?.companyProfile?.earnings_url ? (
              <a
                href={data.company_profile?.earnings_url || data.companyProfile?.earnings_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 truncate"
              >
                {data.company_profile?.earnings_url || data.companyProfile?.earnings_url}
              </a>
            ) : (
              <span className="text-gray-400">-</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )

  // 渲染财务指标
  const renderFinancials = () => (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold">财务指标</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">PE</p>
            <p className="font-medium">{formatNumber(data?.financials?.pe_ratio || data?.financials?.peRatio)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">PB</p>
            <p className="font-medium">{formatNumber(data?.financials?.pb_ratio || data?.financials?.pbRatio)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">PS</p>
            <p className="font-medium">{formatNumber(data?.financials?.ps_ratio || data?.financials?.psRatio)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">股息率</p>
            <p className="font-medium">{formatPercentage(data?.financials?.dividend_yield || data?.financials?.dividendYield)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">ROE</p>
            <p className="font-medium">{formatPercentage(data?.financials?.roe)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">ROA</p>
            <p className="font-medium">{formatPercentage(data?.financials?.roa)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">净利润率</p>
            <p className="font-medium">{formatPercentage(data?.financials?.profit_margin || data?.financials?.netMargin)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">营收增长率</p>
            <p className="font-medium">{formatPercentage(data?.financials?.revenue_growth || data?.financials?.revenueGrowth)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  // 渲染财务健康
  const renderFinancialHealth = () => (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold">财务健康</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">负债率</p>
            <p className="font-medium">{formatPercentage(data?.financials?.debt_to_equity || data?.financials?.debtToEquity)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">流动比率</p>
            <p className="font-medium">{formatNumber(data?.financials?.current_ratio || data?.financials?.currentRatio)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">速动比率</p>
            <p className="font-medium">{formatNumber(data?.financials?.quick_ratio || data?.financials?.quickRatio)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  // 渲染技术指标
  const renderTechnicalIndicators = () => (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold">技术指标</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">RSI</p>
            <p className="font-medium">{formatNumber(data?.technical_indicators?.rsi || data?.technicalIndicators?.rsi)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">MACD</p>
            <p className="font-medium">{formatNumber(typeof data?.technicalIndicators?.macd === 'number'
              ? data.technicalIndicators.macd
              : data?.technical_indicators?.macd?.macd)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">布林带上轨</p>
            <p className="font-medium">{formatNumber(data?.technical_indicators?.bollinger_bands?.upper || data?.technicalIndicators?.bollingerUpper)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">布林带中轨</p>
            <p className="font-medium">{formatNumber(data?.technical_indicators?.bollinger_bands?.middle || data?.technicalIndicators?.bollingerMiddle)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">布林带下轨</p>
            <p className="font-medium">{formatNumber(data?.technical_indicators?.bollinger_bands?.lower || data?.technicalIndicators?.bollingerLower)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title={`${ticker} - 基本面数据`}
      className="max-w-4xl max-h-[80vh] overflow-y-auto"
    >
      <div className="flex justify-end mb-4">
        <DataRefreshButton
          onClick={refreshData}
          isLoading={refreshing}
          className="flex items-center"
        />
      </div>

      {loading ? (
        renderLoading()
      ) : data ? (
        <div className="space-y-4 py-2">
          {renderCompanyProfile()}
          {renderFinancials()}
          {renderFinancialHealth()}
          {renderTechnicalIndicators()}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          无数据可用
        </div>
      )}

      <div className="flex justify-end mt-6">
        <Button onClick={onClose} variant="outline">
          关闭
        </Button>
      </div>
    </Modal>
  )
}

export default FundamentalsModal
