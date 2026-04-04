"""
Finnhub 数据服务模块
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import finnhub
from finnhub import Client as FinnhubClient
import math


class FinnhubService:
    """Finnhub API 服务类"""
    
    def __init__(self, api_key: str):
        self.client = FinnhubClient(api_key=api_key)
    
    def _handle_api_error(self, func_name: str, error: Exception) -> Dict[str, Any]:
        """统一处理 API 错误"""
        return {
            "success": False,
            "error": str(error),
            "function": func_name,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """
        获取实时报价
        
        Args:
            ticker: 股票代码
            
        Returns:
            包含报价信息的字典
        """
        try:
            quote = self.client.quote(ticker)
            return {
                "success": True,
                "ticker": ticker,
                "current_price": quote.get("c"),
                "change": quote.get("d"),
                "percent_change": quote.get("dp"),
                "high_price": quote.get("h"),
                "low_price": quote.get("l"),
                "open_price": quote.get("o"),
                "previous_close": quote.get("pc"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return self._handle_api_error("get_quote", e)
    
    def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """
        获取公司概况
        
        Args:
            ticker: 股票代码
            
        Returns:
            包含公司信息的字典
        """
        try:
            profile = self.client.company_profile2(symbol=ticker)
            return {
                "success": True,
                "ticker": ticker,
                "company_name": profile.get("name"),
                "country": profile.get("country"),
                "currency": profile.get("currency"),
                "exchange": profile.get("exchange"),
                "industry": profile.get("finnhubIndustry"),
                "market_cap": profile.get("marketCapitalization"),
                "description": profile.get("description"),
                "website": profile.get("weburl"),
                "logo": profile.get("logo"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return self._handle_api_error("get_company_profile", e)
    
    def get_financials(self, ticker: str) -> Dict[str, Any]:
        """
        获取基本面数据
        
        Args:
            ticker: 股票代码
            
        Returns:
            包含财务数据的字典
        """
        try:
            financials = self.client.company_basic_financials(ticker, "all")
            metric = financials.get("metric", {})
            
            return {
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
        except Exception as e:
            return self._handle_api_error("get_financials", e)
    
    def get_company_news(self, ticker: str, from_date: Optional[str] = None, 
                        to_date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取公司新闻
        
        Args:
            ticker: 股票代码
            from_date: 开始日期 (YYYY-MM-DD)，默认为7天前
            to_date: 结束日期 (YYYY-MM-DD)，默认为今天
            
        Returns:
            包含新闻列表的字典
        """
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
            
            return {
                "success": True,
                "ticker": ticker,
                "news": news_list,
                "from_date": from_date,
                "to_date": to_date,
                "count": len(news_list),
                "timestamp": datetime.now().isoformat()
            }
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
    
    def get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """
        获取技术指标（RSI、MACD、布林带）
        
        Args:
            ticker: 股票代码
            
        Returns:
            包含技术指标的字典
        """
        try:
            # 获取最近50天的蜡烛图数据
            end_date = int(datetime.now().timestamp())
            start_date = int((datetime.now() - timedelta(days=60)).timestamp())
            
            candles = self.client.stock_candles(
                ticker, 
                "D", 
                start_date, 
                end_date
            )
            
            if candles.get("s") != "ok" or not candles.get("c"):
                return {
                    "success": False,
                    "error": "Unable to fetch candle data",
                    "ticker": ticker
                }
            
            close_prices = candles["c"]
            
            # 计算各项指标
            rsi = self._calculate_rsi(close_prices)
            macd = self._calculate_macd(close_prices)
            bollinger = self._calculate_bollinger_bands(close_prices)
            
            return {
                "success": True,
                "ticker": ticker,
                "current_price": close_prices[-1],
                "rsi": rsi,
                "macd": macd,
                "bollinger_bands": bollinger,
                "rsi_signal": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return self._handle_api_error("get_technical_indicators", e)
