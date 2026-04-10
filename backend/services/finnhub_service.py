"""
Finnhub 数据服务模块
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import finnhub
from finnhub import Client as FinnhubClient
import math

logger = logging.getLogger(__name__)


class FinnhubService:
    """Finnhub API 服务类"""

    def __init__(self, api_key: str, db=None):
        self.client = FinnhubClient(api_key=api_key)
        self.db = db

    def _generate_ir_website(self, ticker: str, company_website: str = "") -> str:
        """
        生成投资者关系网站链接

        Args:
            ticker: 股票代码
            company_website: 公司官网

        Returns:
            投资者关系网站URL
        """
        # 如果公司官网存在，尝试构造IR子域名
        if company_website:
            import re
            # 提取域名
            domain_match = re.search(r'https?://([^/]+)', company_website)
            if domain_match:
                domain = domain_match.group(1)
                # 尝试常见的IR子域名模式
                ir_subdomains = ['ir.', 'investor.', 'investors.', 'investor-relations.']
                for sub in ir_subdomains:
                    if sub in domain:
                        return company_website
                # 尝试构造IR网址
                base_domain = re.sub(r'^www\.', '', domain)
                # 使用最常见的 IR 路径
                return company_website.rstrip('/') + '/investor-relations'

        # 默认使用SEC EDGAR
        return f"https://www.sec.gov/edgar/browse/?CIK={ticker}"

    def _generate_earnings_url(self, ticker: str) -> str:
        """
        生成财报链接

        Args:
            ticker: 股票代码

        Returns:
            财报页面URL
        """
        try:
            # 尝试从 Finnhub API 获取最新的 SEC 文件
            filings = self.client.filings(symbol=ticker, _from=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                                       to=datetime.now().strftime("%Y-%m-%d"))

            # 筛选 10-K（年度报告）和 10-Q（季度报告）
            financial_filings = [f for f in filings if f.get('form') in ['10-K', '10-Q']]

            if financial_filings:
                # 按提交日期排序，最新的在前面
                sorted_filings = sorted(financial_filings, key=lambda x: x.get('filedDate'), reverse=True)
                latest_filing = sorted_filings[0]
                return latest_filing.get('filingUrl', f"https://www.sec.gov/edgar/browse/?CIK={ticker}")

        except Exception as e:
            print(f"Error fetching earnings filings: {e}")

        # 默认使用SEC EDGAR搜索页面
        return f"https://www.sec.gov/edgar/browse/?CIK={ticker}"
    
    def _handle_api_error(self, func_name: str, error: Exception) -> Dict[str, Any]:
        """统一处理 API 错误"""
        return {
            "success": False,
            "error": str(error),
            "function": func_name,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_quote(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取实时报价

        Args:
            ticker: 股票代码
            use_cache: 是否使用缓存

        Returns:
            包含报价信息的字典
        """
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("quote", ticker)
            if cached:
                return cached

        try:
            quote = self.client.quote(ticker)
            current_price = quote.get("c") or 0
            # Finnhub 对无效 ticker 返回全零，视为无效数据
            if current_price == 0:
                logger.warning(f"get_quote: ticker={ticker} returned price=0, treating as invalid")
                return {
                    "success": False,
                    "ticker": ticker,
                    "error": f"无法获取 {ticker} 的报价，请确认股票代码正确",
                    "current_price": 0,
                    "timestamp": datetime.now().isoformat()
                }
            result = {
                "success": True,
                "ticker": ticker,
                "current_price": current_price,
                "change": quote.get("d"),
                "percent_change": quote.get("dp"),
                "high_price": quote.get("h"),
                "low_price": quote.get("l"),
                "open_price": quote.get("o"),
                "previous_close": quote.get("pc"),
                "timestamp": datetime.now().isoformat()
            }

            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("quote", ticker, result)
                logger.info(f"get_quote: cached result for ticker={ticker}")

            return result
        except Exception as e:
            logger.error(f"get_quote error for ticker={ticker}: {e}")
            return self._handle_api_error("get_quote", e)
    
    def get_company_profile(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取公司概况

        Args:
            ticker: 股票代码
            use_cache: 是否使用缓存

        Returns:
            包含公司信息的字典
        """
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("company_profile", ticker)
            if cached:
                return cached

        try:
            profile = self.client.company_profile2(symbol=ticker)

            # 空 profile 表示 ticker 无效
            if not profile or not profile.get("name"):
                logger.warning(f"get_company_profile: ticker={ticker} returned empty profile")
                return {
                    "success": False,
                    "ticker": ticker,
                    "error": f"无法获取 {ticker} 的公司信息，请确认股票代码正确"
                }

            # 生成投资者关系网站和财报链接
            website = profile.get("weburl", "")
            ir_website = self._generate_ir_website(ticker, website)
            earnings_url = self._generate_earnings_url(ticker)

            result = {
                "success": True,
                "ticker": ticker,
                "company_name": profile.get("name"),
                "country": profile.get("country"),
                "currency": profile.get("currency"),
                "exchange": profile.get("exchange"),
                "industry": profile.get("finnhubIndustry"),
                "market_cap": profile.get("marketCapitalization"),
                "description": profile.get("description"),
                "website": website,
                "ir_website": ir_website,
                "earnings_url": earnings_url,
                "logo": profile.get("logo"),
                "timestamp": datetime.now().isoformat()
            }

            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("company_profile", ticker, result)
                logger.info(f"get_company_profile: cached result for ticker={ticker}")

            return result
        except Exception as e:
            logger.error(f"get_company_profile error for ticker={ticker}: {e}")
            return self._handle_api_error("get_company_profile", e)
    
    def get_financials(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取基本面数据

        Args:
            ticker: 股票代码
            use_cache: 是否使用缓存

        Returns:
            包含财务数据的字典
        """
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("financials", ticker)
            if cached:
                return cached

        try:
            financials = self.client.company_basic_financials(ticker, "all")
            metric = financials.get("metric", {})

            result = {
                "success": True,
                "ticker": ticker,
                "pe_ratio": metric.get("peBasicExclExtraTTM"),
                "pb_ratio": metric.get("pbQuarterly"),
                "ps_ratio": metric.get("psTTM"),
                "roe": metric.get("roeTTM"),
                "roa": metric.get("roaTTM"),
                "profit_margin": metric.get("netMarginTTM"),
                "dividend_yield": metric.get("dividendYieldTTM"),
                "debt_to_equity": metric.get("debtToEquityQuarterly"),
                "current_ratio": metric.get("currentRatioQuarterly"),
                "quick_ratio": metric.get("quickRatioQuarterly"),
                "revenue_growth": metric.get("revenueGrowth5Y"),
                "earnings_growth": metric.get("epsGrowth5Y"),
                "timestamp": datetime.now().isoformat()
            }

            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("financials", ticker, result)

            return result
        except Exception as e:
            return self._handle_api_error("get_financials", e)
    
    def get_company_news(self, ticker: str, from_date: Optional[str] = None,
                          to_date: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取公司新闻

        Args:
            ticker: 股票代码
            from_date: 开始日期 (YYYY-MM-DD)，默认为7天前
            to_date: 结束日期 (YYYY-MM-DD)，默认为今天
            use_cache: 是否使用缓存

        Returns:
            包含新闻列表的字典
        """
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("company_news", ticker)
            if cached:
                return cached

        try:
            if not from_date:
                from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = datetime.now().strftime("%Y-%m-%d")

            news = self.client.company_news(ticker, _from=from_date, to=to_date)

            news_list = []
            for item in news[:10]:  # 限制返回10条新闻
                news_list.append({
                    "headline": item.get("headline"),
                    "summary": item.get("summary"),
                    "url": item.get("url"),
                    "source": item.get("source"),
                    "datetime": datetime.fromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else None,
                    "related_symbols": item.get("related", [])
                })

            result = {
                "success": True,
                "ticker": ticker,
                "news": news_list,
                "from_date": from_date,
                "to_date": to_date,
                "count": len(news_list),
                "timestamp": datetime.now().isoformat()
            }

            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("company_news", ticker, result)

            return result
        except Exception as e:
            return self._handle_api_error("get_company_news", e)
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算 RSI 指标"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    def _calculate_macd(self, prices: List[float], fast_period: int = 12, 
                       slow_period: int = 26, signal_period: int = 9) -> Dict[str, float]:
        """计算 MACD 指标"""
        if len(prices) < slow_period:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # 计算 EMA
        def calculate_ema(data, period):
            multiplier = 2 / (period + 1)
            ema = [data[0]]
            for price in data[1:]:
                ema.append(price * multiplier + ema[-1] * (1 - multiplier))
            return ema
        
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]
        signal_line = calculate_ema(macd_line, signal_period)
        
        macd = macd_line[-1]
        signal = signal_line[-1]
        histogram = macd - signal
        
        return {
            "macd": round(macd, 4),
            "signal": round(signal, 4),
            "histogram": round(histogram, 4)
        }
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, 
                                  std_dev: float = 2) -> Dict[str, float]:
        """计算布林带"""
        if len(prices) < period:
            return {"upper": 0, "middle": 0, "lower": 0}
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = math.sqrt(variance)
        
        return {
            "upper": round(sma + std_dev * std, 2),
            "middle": round(sma, 2),
            "lower": round(sma - std_dev * std, 2)
        }
    
    def get_technical_indicators(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        获取技术指标（RSI、MACD、布林带）

        Args:
            ticker: 股票代码
            use_cache: 是否使用缓存

        Returns:
            包含技术指标的字典
        """
        if use_cache and self.db:
            from services.finnhub_cache_service import FinnhubCacheService
            cache_service = FinnhubCacheService(self.db)
            cached = cache_service.get_cache("technical_indicators", ticker)
            if cached:
                return cached

        try:
            # 获取最近60天的蜡烛图数据
            end_date = int(datetime.now().timestamp())
            start_date = int((datetime.now() - timedelta(days=60)).timestamp())

            candles = self.client.stock_candles(ticker, "D", start_date, end_date)

            if candles.get("s") != "ok" or not candles.get("c"):
                logger.warning(f"get_technical_indicators: ticker={ticker} candle status={candles.get('s')}")
                return {
                    "success": False,
                    "ticker": ticker,
                    "error": "无法获取K线数据（当前套餐可能不支持）",
                    "rsi": None,
                    "macd": None,
                    "bollinger_bands": None
                }

            close_prices = candles["c"]

            # 计算各项指标
            rsi = self._calculate_rsi(close_prices)
            macd = self._calculate_macd(close_prices)
            bollinger = self._calculate_bollinger_bands(close_prices)

            result = {
                "success": True,
                "ticker": ticker,
                "current_price": close_prices[-1],
                "rsi": rsi,
                "macd": macd,
                "bollinger_bands": bollinger,
                "rsi_signal": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
                "timestamp": datetime.now().isoformat()
            }

            if self.db:
                from services.finnhub_cache_service import FinnhubCacheService
                cache_service = FinnhubCacheService(self.db)
                cache_service.set_cache("technical_indicators", ticker, result)
                logger.info(f"get_technical_indicators: cached result for ticker={ticker}")

            return result
        except Exception as e:
            err_str = str(e)
            if "403" in err_str:
                logger.warning(f"get_technical_indicators: 403 for ticker={ticker}, API plan limitation")
                return {
                    "success": False,
                    "ticker": ticker,
                    "error": "技术指标数据需要付费套餐（Finnhub stock_candles API）",
                    "rsi": None,
                    "macd": None,
                    "bollinger_bands": None
                }
            logger.error(f"get_technical_indicators error for ticker={ticker}: {e}")
            return self._handle_api_error("get_technical_indicators", e)
