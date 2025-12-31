# Financial Analysis Agent System

A multi-agent AI system that provides comprehensive stock analysis and investment recommendations using CrewAI framework.

## Overview

This system uses 5 specialized AI agents working collaboratively to analyze stocks and provide actionable investment recommendations:

1. **Data Analyst** - Fetches and analyzes real-time stock data, news, and trends
2. **Trading Strategy Developer** - Recommends optimal trading strategies
3. **Trade Advisor** - Provides specific entry/exit prices and timing
4. **Risk Advisor** - Assesses risks and provides mitigation strategies
5. **Financial Advisor** - Consolidates all findings into clear recommendations

## Features

### Comprehensive Multi-Timeframe Analysis
- **1 Day** - Intraday momentum
- **5 Days** - Short-term trend
- **1 Month** - Recent performance
- **6 Months** - Medium-term trend
- **YTD** - Year-to-date performance
- **1 Year** - Annual performance
- **5 Years** - Long-term growth

### Real-Time Data Integration
- Live stock prices via yfinance
- 52-week high/low ranges
- Market cap, P/E ratio, volume metrics
- Company sector and industry information
- Automated news fetching via Serper/Google search

### Intelligent Decision Making
- Sequential workflow ensures proper context passing
- Each agent builds on previous agent's analysis
- Critical evaluation prevents rubber-stamping
- Risk-based decision logic (YES/NO recommendations)

## Files

### `FA.py`
Main orchestration file containing:
- 5 AI agent definitions with specialized roles
- 5 task definitions with detailed instructions
- CrewAI sequential workflow configuration
- Input parameters for stock analysis

### `stock_data_tool.py`
Custom CrewAI tool for fetching stock data:
- Integrates with yfinance API
- Handles multiple ticker formats (removes exchange prefixes)
- Fetches 7 different timeframe analyses
- Calculates trend indicators
- Returns formatted stock analysis

### `utils.py`
Utility functions for API key management:
- `get_openai_api_key()` - OpenAI API access
- `get_serper_api_key()` - Serper search API access

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
```

## Usage

### Basic Usage

Edit the input parameters in `FA.py`:

```python
financial_trading_inputs = {
    'stock_selection': 'AAPL',           # Stock ticker symbol
    'initial_capital': '950 CAD',        # Investment amount
    'risk_tolerance': 'Medium',          # Low/Medium/High
    'trading_strategy_preference': 'Buy & Hold',  # or 'Day Trading'
    'news_impact_consideration': True
}
```

Run the analysis:
```bash
python FA.py
```

### Supported Stock Formats

The system automatically handles various ticker formats:
- ✅ `AAPL` (clean ticker)
- ✅ `OTCMKTS: AUMC` (with exchange prefix)
- ✅ `NYSE: AAPL` (with exchange prefix)

## Output Format

### For YES Recommendations:
```
**INVESTMENT RECOMMENDATION FOR [TICKER]**

**Decision**: YES
**Current Price**: $X.XX USD
**Amount to Invest**: $XXX CAD (~$XXX USD)
**Number of Shares**: X shares
**Entry Price**: $X.XX
**Target Price**: $X.XX (X% gain)
**Stop-Loss**: $X.XX (X% loss)
**When to Enter**: [Immediate/Wait for dip/Wait for confirmation]
**Time Horizon**: 3-6 months
**Trading Style**: Buy & Hold
**Key Reason**: [Data-driven explanation with specific metrics]
**Risk Level**: MEDIUM
```

### For NO Recommendations:
```
**INVESTMENT RECOMMENDATION FOR [TICKER]**

**Decision**: NO
**Current Price**: $X.XX USD
**Risk Level**: HIGH
**Reasons for Not Recommending**:
1. [Specific concern with data]
2. [Specific concern with data]
3. [Specific concern with data]

**Alternative Suggestion**: [What to do instead]
```

## Agent Workflow

```
1. Data Analyst
   ├─ Fetches stock data (price, trends, metrics)
   ├─ Searches for news if yfinance has none
   └─ Provides investment outlook
   
2. Trading Strategy Developer
   ├─ Reviews Data Analyst findings
   ├─ Recommends strategy aligned with user preference
   └─ Considers risk tolerance
   
3. Trade Advisor
   ├─ Reviews strategy recommendation
   ├─ Calculates specific entry/exit prices
   └─ Provides timing recommendation
   
4. Risk Advisor
   ├─ Reviews all previous analysis
   ├─ Identifies top 3 risks
   ├─ Rates overall risk level
   └─ Suggests mitigation strategy
   
5. Financial Advisor
   ├─ Consolidates all findings
   ├─ Makes critical YES/NO decision
   ├─ Provides formatted recommendation
   └─ Ensures data accuracy and consistency
```

## Configuration

### Adjusting Agent Behavior

**Temperature**: Set in `FA.py` line 11
```python
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
```

**Process Type**: Sequential (recommended) vs Hierarchical
```python
process=Process.sequential  # Line ~243
```

### Modifying Timeframes

Edit `stock_data_tool.py` to adjust analysis periods:
```python
hist_1d = stock.history(period="1d", interval="1m")
hist_5d = stock.history(period="5d")
hist_1mo = stock.history(period="1mo")
# ... etc
```

## Key Improvements Made

### ✅ Removed Scraping Tool
- Eliminated 13+ failed scraping attempts
- Faster execution
- Cleaner error logs

### ✅ Sequential Processing
- Each agent executes their own task
- Proper context passing between agents
- Data Analyst uses stock_data_tool directly

### ✅ Multi-Timeframe Analysis
- 7 timeframes (1D, 5D, 1M, 6M, YTD, 1Y, 5Y)
- Professional financial advisor perspective
- Better trend identification

### ✅ Mandatory News Search
- Step-by-step process ensures news is fetched
- Uses Serper search when yfinance has no news
- News sentiment analysis included

### ✅ Critical Financial Advisor
- Not a "yes-man" - evaluates contradictions
- Checks if current price matches entry price
- Flags high-risk scenarios
- Different formats for YES vs NO decisions

### ✅ Data-Driven Reasoning
- Must cite actual numbers in recommendations
- No generic statements allowed
- Specific metrics required in output

## Token Optimization Tips

1. **Use specific stocks** - Well-known stocks (AAPL, NVDA) have more data, reducing search attempts
2. **Adjust verbosity** - Set `verbose=False` in agents to reduce output
3. **Limit news search** - Modify Data Analyst task to search fewer news sources
4. **Use GPT-3.5-turbo** - Already configured, faster and cheaper than GPT-4
5. **Cache results** - Consider caching stock data for repeated analyses

## Troubleshooting

### No Price Data
- Check ticker symbol is correct
- Try without exchange prefix (use `AUMC` not `OTCMKTS: AUMC`)
- Some OTC/penny stocks have limited data

### No News Found
- OTC stocks often lack news in yfinance
- System automatically searches via Serper
- Ensure SERPER_API_KEY is set correctly

### Agent Not Following Instructions
- Check task descriptions in `FA.py`
- Ensure `expected_output` is specific
- Consider increasing task description detail

### High Token Usage
- Reduce `verbose=True` to `verbose=False`
- Use more concise task descriptions
- Limit expected_output to shorter responses
- Consider using GPT-3.5-turbo-16k for longer contexts

## API Keys Required

1. **OpenAI API** - For GPT models (agents use this)
   - Get at: https://platform.openai.com/api-keys
   
2. **Serper API** - For Google search (news fetching)
   - Get at: https://serper.dev/
   - Free tier: 2,500 searches/month

## Cost Considerations

**Typical run costs** (using GPT-3.5-turbo):
- Simple analysis: ~$0.10-0.20
- With news search: ~$0.15-0.30
- Complex decisions: ~$0.20-0.40

**Token usage breakdown**:
- Data Analyst: 1,000-2,000 tokens
- Strategy Developer: 800-1,500 tokens
- Trade Advisor: 800-1,500 tokens
- Risk Advisor: 800-1,500 tokens
- Financial Advisor: 1,000-2,000 tokens

## License

This is a personal project for educational purposes.

## Contributing

Suggestions for improvements:
1. Add technical indicators (RSI, MACD, Bollinger Bands)
2. Support for options analysis
3. Portfolio optimization across multiple stocks
4. Backtesting capabilities
5. Integration with brokerage APIs for execution

## Disclaimer

**This is for educational purposes only. Not financial advice.**

- Always do your own research
- Past performance doesn't guarantee future results
- Consider consulting a licensed financial advisor
- AI can make mistakes - verify all data independently
- Use at your own risk

---

**Version**: 2.0  
**Last Updated**: December 30, 2025  
**Framework**: CrewAI  
**Model**: GPT-3.5-turbo
