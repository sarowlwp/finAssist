# 持仓页面基本面数据展示实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为持仓页面添加股票基本面数据展示和管理功能，支持SQLite缓存和手动更新

**Architecture:** 复用现有API和组件，扩展后端接口，增强前端页面，使用Finnhub API获取数据，SQLite进行缓存管理

**Tech Stack:** Python, FastAPI, SQLite, React, Next.js, Tailwind CSS, Finnhub API

---

## 文件结构

### 后端文件
- `backend/routers/portfolio.py` - 扩展持仓管理接口
- `backend/services/finnhub_cache_service.py` - 优化缓存服务
- `backend/services/finnhub_service.py` - 复用现有数据获取服务
- `backend/database.py` - 复用现有数据库连接

### 前端文件
- `frontend/src/app/portfolio/page.tsx` - 增强持仓页面
- `frontend/src/components/portfolio/FundamentalsModal.tsx` - 基本面数据详情模态框
- `frontend/src/components/portfolio/DataRefreshButton.tsx` - 数据刷新组件
- `frontend/src/lib/api.ts` - 扩展API接口定义

---

## Task 1: 扩展后端API接口

**Files:**
- Modify: `backend/routers/portfolio.py`

- [ ] **Step 1: 新增获取单只股票基本面数据接口**

```python
@router.get("/portfolio/{ticker}/fundamentals")
async def get_portfolio_fundamentals(
    ticker: str,
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取单只股票的基本面数据
    
    Args:
        ticker: 股票代码
    
    Returns:
        包含公司概况、财务指标、技术指标的基本面数据
    """
    try:
        if not finnhub_service:
            return {
                "success": False,
                "error": "Finnhub服务不可用"
            }
        
        # 获取公司概况
        company_profile = finnhub_service.get_company_profile(ticker)
        # 获取财务指标
        financials = finnhub_service.get_financials(ticker)
        # 获取技术指标
        technical_indicators = finnhub_service.get_technical_indicators(ticker)
        
        # 整合数据
        result = {
            "success": True,
            "ticker": ticker,
            "company_profile": company_profile,
            "financials": financials,
            "technical_indicators": technical_indicators
        }
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基本面数据失败: {str(e)}"
        )
```

- [ ] **Step 2: 新增手动刷新数据接口**

```python
@router.post("/portfolio/{ticker}/fundamentals/refresh")
async def refresh_portfolio_fundamentals(
    ticker: str,
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    手动刷新单只股票的基本面数据
    
    Args:
        ticker: 股票代码
    
    Returns:
        更新后的基本面数据
    """
    try:
        if not finnhub_service:
            return {
                "success": False,
                "error": "Finnhub服务不可用"
            }
        
        # 强制获取最新数据（不使用缓存）
        company_profile = finnhub_service.get_company_profile(ticker, use_cache=False)
        financials = finnhub_service.get_financials(ticker, use_cache=False)
        technical_indicators = finnhub_service.get_technical_indicators(ticker, use_cache=False)
        
        result = {
            "success": True,
            "ticker": ticker,
            "company_profile": company_profile,
            "financials": financials,
            "technical_indicators": technical_indicators,
            "message": "数据已成功刷新"
        }
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新数据失败: {str(e)}"
        )
```

- [ ] **Step 3: 扩展获取所有持仓接口，添加数据状态**

```python
@router.get("/portfolio")
async def get_all_portfolio(
    portfolio_store: PortfolioStore = Depends(get_portfolio_store),
    finnhub_service: Optional[FinnhubService] = Depends(get_finnhub_service)
):
    """
    获取所有持仓（包含实时价格和盈亏计算，新增数据更新状态）
    
    Returns:
        持仓列表（含计算字段和数据状态）
    """
    try:
        holdings = portfolio_store.get_all()
        result = []
        
        for holding in holdings:
            # 获取当前价格
            current_price = 0.0
            if finnhub_service:
                quote = finnhub_service.get_quote(holding.ticker)
                if quote.get("success"):
                    current_price = quote.get("current_price", 0.0)
            
            cost = holding.quantity * holding.cost_price
            market_value = holding.quantity * current_price
            profit_loss = market_value - cost
            profit_loss_percent = (profit_loss / cost * 100) if cost > 0 else 0.0
            
            # 检查数据缓存状态（简化版）
            data_status = {
                "last_updated": None,
                "is_stale": False
            }
            
            result.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "cost_price": holding.cost_price,
                "current_price": current_price,
                "market_value": market_value,
                "total_cost": cost,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
                "note": holding.note,
                "created_at": holding.created_at,
                "updated_at": holding.updated_at,
                "data_status": data_status
            })
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取持仓失败: {str(e)}"
        )
```

- [ ] **Step 4: 运行测试验证接口**

Run: `pytest tests/backend/routers/test_portfolio.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/routers/portfolio.py
git commit -m "feat: 新增持仓基本面数据接口"
```

---

## Task 2: 优化缓存服务

**Files:**
- Modify: `backend/services/finnhub_cache_service.py`

- [ ] **Step 1: 优化缓存过期时间**

```python
class FinnhubCacheService:
    """
    Finnhub API 数据缓存服务
    
    提供缓存的增删改查操作，支持自定义过期时间
    """
    def __init__(self, db_session):
        self.db_session = db_session
    
    def set_cache(self, data_type: str, ticker: str, data: dict, expires_in: int = None):
        """
        设置缓存
        
        Args:
            data_type: 数据类型 (quote, company_profile, financials, etc.)
            ticker: 股票代码
            data: 要缓存的数据
            expires_in: 过期时间（秒），默认根据数据类型设置
        """
        if expires_in is None:
            # 根据数据类型设置默认过期时间
            if data_type == "company_profile":
                expires_in = 24 * 60 * 60  # 24小时
            elif data_type == "financials":
                expires_in = 12 * 60 * 60  # 12小时
            elif data_type == "technical_indicators":
                expires_in = 6 * 60 * 60  # 6小时
            else:
                expires_in = 1 * 60 * 60  # 默认1小时
        
        cache_key = f"{data_type}_{ticker}"
        
        # 检查是否已存在
        existing = self.db_session.query(FinnhubCache).filter(
            FinnhubCache.cache_key == cache_key
        ).first()
        
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        if existing:
            existing.data = data
            existing.expires_at = expires_at
        else:
            new_cache = FinnhubCache(
                cache_key=cache_key,
                data_type=data_type,
                ticker=ticker,
                data=data,
                expires_at=expires_at
            )
            self.db_session.add(new_cache)
        
        self.db_session.commit()
```

- [ ] **Step 2: 运行测试验证缓存服务**

Run: `pytest tests/backend/services/test_finnhub_cache_service.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/services/finnhub_cache_service.py
git commit -m "feat: 优化Finnhub缓存过期策略"
```

---

## Task 3: 扩展前端API接口

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: 新增API接口定义**

```typescript
// 基本面数据类型定义
export interface CompanyProfile {
  success: boolean;
  ticker: string;
  company_name: string;
  country: string;
  currency: string;
  exchange: string;
  industry: string;
  market_cap: number;
  description: string;
  website: string;
  logo: string;
  timestamp: string;
}

export interface Financials {
  success: boolean;
  ticker: string;
  pe_ratio: number;
  pb_ratio: number;
  ps_ratio: number;
  roe: number;
  roa: number;
  profit_margin: number;
  dividend_yield: number;
  debt_to_equity: number;
  current_ratio: number;
  quick_ratio: number;
  revenue_growth: number;
  earnings_growth: number;
  timestamp: string;
}

export interface TechnicalIndicators {
  success: boolean;
  ticker: string;
  current_price: number;
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger_bands: {
    upper: number;
    middle: number;
    lower: number;
  };
  rsi_signal: string;
  timestamp: string;
}

export interface FundamentalsData {
  success: boolean;
  ticker: string;
  company_profile: CompanyProfile;
  financials: Financials;
  technical_indicators: TechnicalIndicators;
}

// API接口定义
export const portfolioApi = {
  // 现有的接口保持不变
  // ...
  
  // 新增获取基本面数据接口
  getFundamentals: async (ticker: string): Promise<FundamentalsData> => {
    const response = await fetch(`/api/portfolio/${ticker}/fundamentals`);
    if (!response.ok) {
      throw new Error(`获取基本面数据失败: ${response.statusText}`);
    }
    return await response.json();
  },
  
  // 新增刷新基本面数据接口
  refreshFundamentals: async (ticker: string): Promise<FundamentalsData> => {
    const response = await fetch(`/api/portfolio/${ticker}/fundamentals/refresh`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`刷新数据失败: ${response.statusText}`);
    }
    return await response.json();
  }
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: 新增基本面数据API接口定义"
```

---

## Task 4: 创建基本面数据详情模态框

**Files:**
- Create: `frontend/src/components/portfolio/FundamentalsModal.tsx`

- [ ] **Step 1: 实现模态框组件**

```tsx
import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataRefreshButton } from './DataRefreshButton';
import { portfolioApi, type CompanyProfile, type Financials, type TechnicalIndicators } from '@/lib/api';

interface FundamentalsModalProps {
  ticker: string;
  isOpen: boolean;
  onClose: () => void;
}

export function FundamentalsModal({ ticker, isOpen, onClose }: FundamentalsModalProps) {
  const [data, setData] = useState<{
    company_profile?: CompanyProfile;
    financials?: Financials;
    technical_indicators?: TechnicalIndicators;
  }>({});
  const [loading, setLoading] = useState(false);

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const response = await portfolioApi.getFundamentals(ticker);
      setData({
        company_profile: response.company_profile,
        financials: response.financials,
        technical_indicators: response.technical_indicators
      });
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const refreshData = async () => {
    setLoading(true);
    try {
      const response = await portfolioApi.refreshFundamentals(ticker);
      setData({
        company_profile: response.company_profile,
        financials: response.financials,
        technical_indicators: response.technical_indicators
      });
    } catch (error) {
      console.error('刷新数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 格式化数字
  const formatNumber = (value: number | undefined, decimals: number = 2): string => {
    if (value === undefined || value === null) {
      return '-';
    }
    return value.toFixed(decimals);
  };

  // 格式化百分比
  const formatPercent = (value: number | undefined, decimals: number = 2): string => {
    if (value === undefined || value === null) {
      return '-';
    }
    return `${(value * 100).toFixed(decimals)}%`;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex justify-between items-center">
            <DialogTitle>
              {ticker} - 基本面数据
            </DialogTitle>
            <DataRefreshButton
              onClick={refreshData}
              isLoading={loading}
            />
          </div>
        </DialogHeader>
        
        {loading ? (
          <div className="flex justify-center items-center py-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">加载中...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* 公司概况 */}
            <Card>
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-lg">公司概况</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-4 pb-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      公司名称
                    </label>
                    <div className="text-sm">
                      {data.company_profile?.company_name || '-'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      行业
                    </label>
                    <div className="text-sm">
                      {data.company_profile?.industry || '-'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      市值 (USD)
                    </label>
                    <div className="text-sm">
                      {data.company_profile?.market_cap ? 
                        new Intl.NumberFormat('en-US', { notation: 'compact' }).format(data.company_profile.market_cap) : 
                        '-'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      市场
                    </label>
                    <div className="text-sm">
                      {data.company_profile?.exchange || '-'}
                    </div>
                  </div>
                </div>
                {data.company_profile?.description && (
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      公司描述
                    </label>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {data.company_profile.description}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 财务指标 */}
            <Card>
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-lg">财务指标</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-4 pb-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      市盈率 (PE)
                    </label>
                    <div className="text-sm">
                      {formatNumber(data.financials?.pe_ratio)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      市净率 (PB)
                    </label>
                    <div className="text-sm">
                      {formatNumber(data.financials?.pb_ratio)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      市销率 (PS)
                    </label>
                    <div className="text-sm">
                      {formatNumber(data.financials?.ps_ratio)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      股息率
                    </label>
                    <div className="text-sm">
                      {formatPercent(data.financials?.dividend_yield)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      净资产收益率 (ROE)
                    </label>
                    <div className="text-sm">
                      {formatPercent(data.financials?.roe)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      资产收益率 (ROA)
                    </label>
                    <div className="text-sm">
                      {formatPercent(data.financials?.roa)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      净利润率
                    </label>
                    <div className="text-sm">
                      {formatPercent(data.financials?.profit_margin)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      营收增长率 (5年)
                    </label>
                    <div className="text-sm">
                      {formatPercent(data.financials?.revenue_growth)}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 财务健康 */}
            <Card>
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-lg">财务健康</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-4 pb-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      负债率
                    </label>
                    <div className="text-sm">
                      {formatPercent(data.financials?.debt_to_equity)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      流动比率
                    </label>
                    <div className="text-sm">
                      {formatNumber(data.financials?.current_ratio)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      速动比率
                    </label>
                    <div className="text-sm">
                      {formatNumber(data.financials?.quick_ratio)}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/portfolio/FundamentalsModal.tsx
git commit -m "feat: 创建基本面数据详情模态框"
```

---

## Task 4: 创建数据刷新按钮组件

**Files:**
- Create: `frontend/src/components/portfolio/DataRefreshButton.tsx`

- [ ] **Step 1: 实现数据刷新按钮**

```tsx
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';

interface DataRefreshButtonProps {
  onClick: () => void;
  isLoading: boolean;
  className?: string;
}

export function DataRefreshButton({ 
  onClick, 
  isLoading, 
  className = "" 
}: DataRefreshButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={isLoading}
      size="sm"
      variant="outline"
      className={className}
    >
      <RefreshCw 
        className={`h-4 w-4 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} 
      />
      {isLoading ? '刷新中...' : '刷新数据'}
    </Button>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/portfolio/DataRefreshButton.tsx
git commit -m "feat: 创建数据刷新按钮组件"
```

---

## Task 5: 增强持仓页面

**Files:**
- Modify: `frontend/src/app/portfolio/page.tsx`

- [ ] **Step 1: 导入组件**

```typescript
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { portfolioApi } from '@/lib/api';
import { FundamentalsModal } from '@/components/portfolio/FundamentalsModal';
import { Eye } from 'lucide-react';
```

- [ ] **Step 2: 新增状态管理**

```typescript
export default function PortfolioPage() {
  // 现有的状态保持不变
  // ...
  
  // 新增状态
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [showFundamentalsModal, setShowFundamentalsModal] = useState(false);
  
  // 新增显示基本面数据的函数
  const handleShowFundamentals = (ticker: string) => {
    setSelectedTicker(ticker);
    setShowFundamentalsModal(true);
  };
  
  // 其他函数保持不变
  // ...
```

- [ ] **Step 3: 增强表格渲染**

```typescript
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b dark:border-gray-700">
                        <th className="text-left py-2 px-2">代码</th>
                        <th className="text-right py-2 px-2">数量</th>
                        <th className="text-right py-2 px-2">成本价</th>
                        <th className="text-right py-2 px-2">当前价</th>
                        <th className="text-right py-2 px-2">盈亏</th>
                        <th className="text-left py-2 px-2">备注</th>
                        <th className="text-center py-2 px-2">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPortfolio.map((item) => (
                        <tr key={item.ticker} className="border-b dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-slate-800">
                          <td className="py-2 px-2 font-medium">{item.ticker}</td>
                          <td className="text-right py-2 px-2">{item.quantity}</td>
                          <td className="text-right py-2 px-2">
                            ${item.cost_price.toFixed(2)}
                          </td>
                          <td className="text-right py-2 px-2">
                            ${item.current_price.toFixed(2)}
                          </td>
                          <td className="text-right py-2 px-2">
                            <span className={
                              item.profit_loss >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                            }>
                              {item.profit_loss >= 0 ? '+' : ''}
                              ${item.profit_loss.toFixed(2)} 
                              ({item.profit_loss_percent >= 0 ? '+' : ''}
                              {item.profit_loss_percent.toFixed(2)}%)
                            </span>
                          </td>
                          <td className="py-2 px-2 text-sm text-gray-600 dark:text-gray-400">
                            {item.note || '-'}
                          </td>
                          <td className="text-center py-2 px-2">
                            <div className="flex gap-2 justify-center">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleShowFundamentals(item.ticker)}
                              >
                                <Eye className="h-3.5 w-3.5 mr-1" />
                                查看数据
                              </Button>
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
```

- [ ] **Step 4: 添加模态框**

```typescript
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">持仓管理</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Form */}
          {/* ... 现有的表单代码保持不变 ... */}

          {/* Portfolio List */}
          <Card className="lg:col-span-2">
            {/* ... 现有的卡片代码保持不变 ... */}
          </Card>
        </div>

        {/* 基本面数据模态框 */}
        {selectedTicker && (
          <FundamentalsModal
            ticker={selectedTicker}
            isOpen={showFundamentalsModal}
            onClose={() => setShowFundamentalsModal(false)}
          />
        )}
      </div>
    </div>
  )
```

- [ ] **Step 5: 运行测试验证页面**

Run: `npm run test:e2e`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/portfolio/page.tsx
git commit -m "feat: 增强持仓页面，添加基本面数据查看功能"
```

---

## Task 6: 运行测试和修复问题

**Files:**
- All modified files

- [ ] **Step 1: 运行后端测试**

Run: `pytest tests/backend -v`
Expected: PASS

- [ ] **Step 2: 运行前端测试**

Run: `npm run test:e2e`
Expected: PASS

- [ ] **Step 3: 修复发现的问题**

根据测试结果，修复任何发现的问题，如类型错误、布局问题等。

- [ ] **Step 4: Commit 修复的问题**

```bash
# 提交所有修复的文件
git add backend/ frontend/
git commit -m "fix: 修复基本面数据展示相关问题"
```

---

## Task 7: 部署和测试

**Files:**
- All files

- [ ] **Step 1: 停止旧服务**

Run: `pkill -f "uvicorn main:app" || true`
Run: `pkill -f "next dev" || true`

- [ ] **Step 2: 重启后端服务**

Run: `cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8001 &`

- [ ] **Step 3: 重启前端服务**

Run: `cd frontend && npm run dev &`

- [ ] **Step 4: 测试功能**

1. 访问 http://localhost:3000/portfolio
2. 检查页面是否正常加载
3. 点击"查看数据"按钮，测试模态框是否正常显示
4. 测试数据刷新功能是否正常

---

## 验证标准

1. 所有页面功能正常工作
2. 数据展示准确
3. 刷新按钮功能正常
4. 支持浅色/深色模式
5. 页面响应迅速
6. 测试覆盖率达标

---

**完成时间预计:** 4-6小时
