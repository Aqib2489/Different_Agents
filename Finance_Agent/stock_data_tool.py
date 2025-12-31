"""Custom tool to fetch real-time stock data using yfinance"""

from crewai.tools import BaseTool
from pydantic import Field
import yfinance as yf
from datetime import datetime, timedelta


class StockDataTool(BaseTool):
    name: str = "Get Stock Data"
    description: str = (
        "Fetches real-time stock data including current price, volume, "
        "financials, and recent news for a given stock ticker. "
        "Input should be a stock ticker symbol (e.g., 'NVDA', 'AAPL')."
    )

    def _run(self, ticker: str) -> str:
        """Fetch comprehensive stock data for the given ticker"""
        try:
            # Clean ticker symbol - remove exchange prefix if present
            # Examples: "OTCMKTS: AUMC" -> "AUMC", "NYSE: AAPL" -> "AAPL"
            original_ticker = ticker
            if ':' in ticker:
                ticker = ticker.split(':')[-1].strip()
                print(f"Note: Converting '{original_ticker}' to '{ticker}' for yfinance")
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price and basic info - handle multiple sources
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            # If still no price, try getting from history
            if not current_price or current_price == 'N/A':
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Validate current_price is numeric
            try:
                current_price = float(current_price)
                price_str = f"${current_price:.2f} USD"
            except (ValueError, TypeError):
                current_price = None
                price_str = "N/A (Price data unavailable)"
            
            # Get historical data for comprehensive trend analysis
            # Financial advisors analyze multiple timeframes
            hist_1d = stock.history(period="1d", interval="1m")
            hist_5d = stock.history(period="5d")
            hist_1mo = stock.history(period="1mo")
            hist_6mo = stock.history(period="6mo")
            hist_ytd = stock.history(period="ytd")
            hist_1y = stock.history(period="1y")
            hist_5y = stock.history(period="5y")
            
            # Helper function to calculate price change
            def calc_change(hist_data, current_price):
                if current_price and len(hist_data) > 0:
                    old_price = hist_data['Close'].iloc[0]
                    change = ((current_price - old_price) / old_price * 100)
                    return f"{change:+.2f}%", change
                return "N/A", 0
            
            # Calculate price changes for all timeframes
            day_change_str, day_change = calc_change(hist_1d, current_price)
            week_change_str, week_change = calc_change(hist_5d, current_price)
            month_change_str, month_change = calc_change(hist_1mo, current_price)
            six_month_change_str, six_month_change = calc_change(hist_6mo, current_price)
            ytd_change_str, ytd_change = calc_change(hist_ytd, current_price)
            year_change_str, year_change = calc_change(hist_1y, current_price)
            five_year_change_str, five_year_change = calc_change(hist_5y, current_price)
            
            # Determine overall trend based on multiple timeframes
            positive_trends = sum([
                1 if change > 0 else 0 
                for change in [day_change, week_change, month_change, six_month_change, year_change]
                if change != 0
            ])
            total_trends = sum([
                1 for change in [day_change, week_change, month_change, six_month_change, year_change]
                if change != 0
            ])
            
            if total_trends > 0:
                trend_ratio = positive_trends / total_trends
                if trend_ratio >= 0.6:
                    trend = "BULLISH"
                elif trend_ratio <= 0.4:
                    trend = "BEARISH"
                else:
                    trend = "NEUTRAL"
            else:
                trend = "NEUTRAL"
            
            # Format 52-week high/low
            high_52 = info.get('fiftyTwoWeekHigh')
            low_52 = info.get('fiftyTwoWeekLow')
            high_52_str = f"${high_52:.2f}" if high_52 and isinstance(high_52, (int, float)) else "N/A"
            low_52_str = f"${low_52:.2f}" if low_52 and isinstance(low_52, (int, float)) else "N/A"
            
            # Format market cap
            market_cap = info.get('marketCap', 0)
            if market_cap and isinstance(market_cap, (int, float)) and market_cap > 0:
                market_cap_str = f"${market_cap:,.0f}"
            else:
                market_cap_str = "N/A"
            
            # Format P/E ratio
            pe_ratio = info.get('trailingPE')
            pe_ratio_str = f"{pe_ratio:.2f}" if pe_ratio and isinstance(pe_ratio, (int, float)) else "N/A"
            
            # Format volume
            volume = info.get('volume')
            avg_volume = info.get('averageVolume')
            volume_str = f"{volume:,}" if volume and isinstance(volume, (int, float)) else "N/A"
            avg_volume_str = f"{avg_volume:,}" if avg_volume and isinstance(avg_volume, (int, float)) else "N/A"
            
            # Get news
            news = stock.news[:3] if hasattr(stock, 'news') and stock.news else []
            if news:
                news_summary = "\n".join([f"- {item.get('title', 'N/A')}" for item in news])
            else:
                news_summary = "No recent news available from yfinance.\nNote: For OTC stocks, use Search tool to find recent news articles."
            
            # Format the output with comprehensive timeframe analysis
            output = f"""
STOCK DATA FOR {ticker.upper()}
{'='*60}

CURRENT PRICE: {price_str}

PRICE TRENDS (Multiple Timeframes):
- 1 Day Change:    {day_change_str}
- 5 Day Change:    {week_change_str}
- 1 Month Change:  {month_change_str}
- 6 Month Change:  {six_month_change_str}
- YTD Change:      {ytd_change_str}
- 1 Year Change:   {year_change_str}
- 5 Year Change:   {five_year_change_str}

52-WEEK RANGE:
- 52 Week High: {high_52_str}
- 52 Week Low: {low_52_str}

KEY METRICS:
- Market Cap: {market_cap_str}
- P/E Ratio: {pe_ratio_str}
- Volume: {volume_str}
- Average Volume: {avg_volume_str}

COMPANY INFO:
- Sector: {info.get('sector', 'N/A')}
- Industry: {info.get('industry', 'N/A')}

RECENT NEWS (Last 7 days):
{news_summary}

TREND: {trend}
"""
            return output.strip()
            
        except Exception as e:
            return f"Error fetching data for {ticker}: {str(e)}\n\nNote: This stock may have limited data available. For OTC/penny stocks, try using the ticker symbol without exchange prefix (e.g., 'AUMC' instead of 'OTCMKTS:AUMC')."
