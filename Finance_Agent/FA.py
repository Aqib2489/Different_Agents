# Warning control
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew

import os
from utils import get_openai_api_key, get_serper_api_key

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
os.environ["SERPER_API_KEY"] = get_serper_api_key()

from crewai_tools import SerperDevTool
from stock_data_tool import StockDataTool

search_tool = SerperDevTool()
stock_data_tool = StockDataTool()  # New reliable stock data tool

data_analyst_agent = Agent(
    role="Data Analyst",
    goal="Monitor and analyze market data in real-time "
         "to identify trends and predict market movements.",
    backstory="Specializing in financial markets, this agent "
              "uses statistical modeling and machine learning "
              "to provide crucial insights. With a knack for data, "
              "the Data Analyst Agent is the cornerstone for "
              "informing trading decisions.",
    verbose=True,
    allow_delegation=True,
    tools = [stock_data_tool, search_tool]  # Use reliable stock data tool
)


trading_strategy_agent = Agent(
    role="Trading Strategy Developer",
    goal="Develop and test various trading strategies based "
         "on insights from the Data Analyst Agent.",
    backstory="Equipped with a deep understanding of financial "
              "markets and quantitative analysis, this agent "
              "devises and refines trading strategies. It evaluates "
              "the performance of different approaches to determine "
              "the most profitable and risk-averse options.",
    verbose=True,
    allow_delegation=True,
    tools = [search_tool]
)

execution_agent = Agent(
    role="Trade Advisor",
    goal="Suggest optimal trade execution strategies "
         "based on approved trading strategies.",
    backstory="This agent specializes in analyzing the timing, price, "
              "and logistical details of potential trades. By evaluating "
              "these factors, it provides well-founded suggestions for "
              "when and how trades should be executed to maximize "
              "efficiency and adherence to strategy.",
    verbose=True,
    allow_delegation=True,
    tools = [search_tool]
)

risk_management_agent = Agent(
    role="Risk Advisor",
    goal="Evaluate and provide insights on the risks "
         "associated with potential trading activities.",
    backstory="Armed with a deep understanding of risk assessment models "
              "and market dynamics, this agent scrutinizes the potential "
              "risks of proposed trades. It offers a detailed analysis of "
              "risk exposure and suggests safeguards to ensure that "
              "trading activities align with the firm's risk tolerance.",
    verbose=True,
    allow_delegation=True,
    tools = [search_tool]
)

financial_advisor_agent = Agent(
    role="Financial Advisor",
    goal="Provide clear, actionable investment recommendations "
         "based on comprehensive analysis from all team members.",
    backstory="As a seasoned financial advisor with 20 years of experience, "
              "you excel at synthesizing complex financial data into clear, "
              "actionable recommendations. You critically evaluate all inputs "
              "and identify contradictions or concerns before making recommendations. "
              "You provide specific advice on investment amounts, entry/exit points, "
              "and timing based on thorough analysis from your team of experts. "
              "You are NOT a yes-man - if the data shows red flags or contradictions, "
              "you point them out and adjust recommendations accordingly.",
    verbose=True,
    allow_delegation=True,
    tools = [search_tool]
)

# Task for Data Analyst Agent: Analyze Market Data
data_analysis_task = Task(
    description=(
        "STEP 1: Use the 'Get Stock Data' tool to fetch data for {stock_selection}.\n\n"
        "STEP 2: Check the 'RECENT NEWS' section in the output:\n"
        "- IF it shows 'No recent news available from yfinance', you MUST proceed to STEP 3\n"
        "- IF it shows actual news, you can skip STEP 3\n\n"
        "STEP 3: MANDATORY NEWS SEARCH (if no news from yfinance):\n"
        "- Use 'Search the internet with Serper' tool\n"
        "- Search query: '{stock_selection} stock news recent' OR '{stock_selection} company news'\n"
        "- Review at least the top 3 news results\n"
        "- Determine sentiment: Positive (growth, partnership, earnings beat) / Negative (losses, lawsuits, decline) / Neutral\n\n"
        "STEP 4: Summarize your analysis in 5-7 sentences covering:\n"
        "1. Current price: $X.XX and overall trend (BULLISH/BEARISH/NEUTRAL)\n"
        "2. Multi-timeframe analysis (1D, 5D, 1M, 6M, YTD, 1Y performance)\n"
        "3. Key metrics: P/E ratio, Market Cap, Volume\n"
        "4. News sentiment and impact (MUST include if found via search)\n"
        "5. Investment recommendation: Good buying opportunity or wait?\n\n"
        "CRITICAL: Do NOT skip the news search step if yfinance shows no news!"
    ),
    expected_output=(
        "A complete analysis FOR {stock_selection} with: Current price, multi-timeframe trends, key metrics, "
        "news sentiment (with at least 1-2 specific news points if found), and investment outlook. "
        "Maximum 7 sentences. MUST include news analysis."
    ),
    agent=data_analyst_agent,
)

# Task for Trading Strategy Agent: Develop Trading Strategies
strategy_development_task = Task(
    description=(
        "Based on Data Analyst's findings, recommend the best strategy for {stock_selection} based on {trading_strategy_preference}.\n\n"
        "CRITICAL: You are developing strategy for {stock_selection} ONLY. Do NOT analyze any other stock.\n\n"
        "Consider:\n"
        "1. Current price trend (bullish/bearish) for {stock_selection}\n"
        "2. Risk tolerance: {risk_tolerance}\n"
        "3. Client's preference: {trading_strategy_preference}\n\n"
        "IF 'Day Trading' or short-term: Recommend Momentum, Breakout, or Range trading.\n"
        "IF 'Buy & Hold' or long-term: Recommend value investing, growth investing, or dollar-cost averaging.\n\n"
        "Tailor your recommendation to match their stated preference."
    ),
    expected_output=(
        "ONE recommended trading strategy for {stock_selection} ONLY, aligned with client's preference, with clear reasoning. Maximum 5 sentences."
    ),
    agent=trading_strategy_agent,
)

# Task for Trade Advisor Agent: Plan Trade Execution
execution_planning_task = Task(
    description=(
        "Based on current price, recommended strategy, and {trading_strategy_preference}, provide SPECIFIC execution plan for {stock_selection}:\n\n"
        "CRITICAL: This execution plan is for {stock_selection} ONLY. Do NOT provide plans for any other stock.\n\n"
        "1. **Entry Point**: Exact price or price range to buy {stock_selection}\n"
        "2. **Exit Point**: Target price to sell {stock_selection} for profit\n"
        "3. **Stop-Loss**: Price to exit if {stock_selection} trade goes wrong\n"
        "4. **Timing**: When to enter (now, wait for dip, wait for breakout)\n\n"
        "Base all prices on the ACTUAL CURRENT PRICE of {stock_selection} from Data Analyst.\n\n"
        "IF Day Trading: Target 2-5% gains with 2-3% stop-loss.\n"
        "IF Buy & Hold: Target 15-30% gains over weeks/months with 10-15% stop-loss."
    ),
    expected_output=(
        "Specific entry price, exit price, stop-loss price, and timing recommendation for {stock_selection} ONLY, appropriate for the trading style. Maximum 5 sentences."
    ),
    agent=execution_agent,
)

# Task for Risk Advisor Agent: Assess Trading Risks
risk_assessment_task = Task(
    description=(
        "Based ONLY on the Data Analyst's findings and Trade Advisor's plan, assess the TOP 3 RISKS for {stock_selection}:\n\n"
        "CRITICAL: Analyze risks using the ACTUAL DATA provided by your team, NOT generic web searches.\n\n"
        "Consider:\n"
        "1. Market risk: Based on actual price volatility and trend from Data Analyst\n"
        "2. Stock-specific risk: Based on P/E ratio, market cap, news from Data Analyst\n"
        "3. Execution risk: OTC stock liquidity concerns\n\n"
        "Rate overall risk as: LOW, MEDIUM, or HIGH based on the specific data you received.\n"
        "Suggest ONE mitigation strategy (e.g., position sizing, stop-loss, diversification)."
    ),
    expected_output=(
        "Top 3 SPECIFIC risks for {stock_selection} based on team's data analysis, overall risk rating (LOW/MEDIUM/HIGH), and one concrete mitigation strategy. Maximum 5 sentences."
    ),
    agent=risk_management_agent,
)

# Task for Financial Advisor: Provide Final Investment Recommendation
investment_recommendation_task = Task(
    description=(
        "Consolidate all findings into ONE CLEAR recommendation for {stock_selection} ONLY. Client has {initial_capital} CAD and prefers {trading_strategy_preference}.\n\n"
        "ABSOLUTELY CRITICAL: You MUST provide recommendation for {stock_selection} ticker symbol. DO NOT provide recommendation for any other stock.\n\n"
        "CRITICAL ANALYSIS REQUIRED:\n"
        "1. Evaluate if this is a good investment based on ALL team inputs\n"
        "2. If Risk Level is HIGH AND recent trend is strongly negative, recommend NO\n"
        "3. If current price is ABOVE entry price OR recent trend is DOWN, recommend 'Wait'\n"
        "4. If fundamentals are weak (no P/E, low volume, negative news), recommend NO\n\n"
        "**DECISION LOGIC:**\n"
        "- Decision = YES: Stock shows good fundamentals, acceptable risk, positive outlook\n"
        "- Decision = NO: High risk, poor fundamentals, strongly negative trend, or major red flags\n\n"
        "**FORMAT BASED ON DECISION:**\n\n"
        "============================================================\n"
        "IF DECISION = YES, use this format:\n"
        "============================================================\n"
        "**INVESTMENT RECOMMENDATION FOR {stock_selection}**\n\n"
        "**Decision**: YES\n"
        "**Current Price**: $X.XX USD\n"
        "**Amount to Invest**: $XXX CAD (~$XXX USD)\n"
        "**Number of Shares**: X shares of {stock_selection}\n"
        "**Entry Price**: $X.XX\n"
        "**Target Price**: $X.XX (X% gain)\n"
        "**Stop-Loss**: $X.XX (X% loss)\n"
        "**When to Enter**: [Immediate / Wait for dip to $X.XX / Wait for confirmation above $X.XX]\n"
        "**Time Horizon**: [3-6 months / 6-12 months]\n"
        "**Trading Style**: {trading_strategy_preference}\n"
        "**Key Reason**: [Cite ACTUAL data: '1-month +X%, P/E ratio Y, positive news Z']\n"
        "**Risk Level**: [LOW/MEDIUM/HIGH]\n\n"
        "============================================================\n"
        "IF DECISION = NO, use this SHORTER format:\n"
        "============================================================\n"
        "**INVESTMENT RECOMMENDATION FOR {stock_selection}**\n\n"
        "**Decision**: NO\n"
        "**Current Price**: $X.XX USD\n"
        "**Risk Level**: [Exact rating from Risk Advisor]\n"
        "**Reasons for Not Recommending**:\n"
        "1. [First major concern - be specific with data]\n"
        "2. [Second major concern - be specific with data]\n"
        "3. [Third major concern - be specific with data]\n\n"
        "**Alternative Suggestion**: [What conditions would need to change for this to be investable? Or suggest waiting, or looking at other stocks]\n\n"
        "============================================================\n\n"
        "CRITICAL: \n"
        "- If Decision = NO, DO NOT include investment amounts, share counts, entry/exit prices\n"
        "- If Decision = YES, fill ALL fields with actual numbers from team reports\n"
        "- Key Reason must cite ACTUAL numbers from Data Analyst\n"
        "- Convert CAD to USD using 0.72 exchange rate (only if Decision = YES)"
    ),
    expected_output=(
        "A complete recommendation for {stock_selection}. If YES: full investment details. If NO: price, risk level, 3 specific reasons, and alternative suggestion. NO placeholders."
    ),
    agent=financial_advisor_agent,
)


from crewai import Crew, Process
from langchain_openai import ChatOpenAI

# Define the crew with agents and tasks
financial_trading_crew = Crew(
    agents=[data_analyst_agent, 
            trading_strategy_agent, 
            execution_agent, 
            risk_management_agent,
            financial_advisor_agent],
    
    tasks=[data_analysis_task, 
           strategy_development_task, 
           execution_planning_task, 
           risk_assessment_task,
           investment_recommendation_task],
    
    process=Process.sequential,
    verbose=True
)


# Example data for kicking off the process
financial_trading_inputs = {
    'stock_selection': 'PLTR' ,  # Use clean ticker without exchange prefix
    'initial_capital': '950 CAD',
    'risk_tolerance': 'Medium',
    'trading_strategy_preference': 'Buy & Hold',
    'news_impact_consideration': True
}

### this execution will take some time to run
result = financial_trading_crew.kickoff(inputs=financial_trading_inputs)

print("\n" + "="*80)
print("FINAL RESULT")
print("="*80)
print(result.raw)