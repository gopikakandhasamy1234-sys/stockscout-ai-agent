import json

import yfinance as yf
from langchain_core.tools import tool

FIELDS = [
    "shortName", "bid", "ask", "exchange", "fiftyTwoWeekHigh",
    "fiftyTwoWeekLow", "averageAnalystRating", "dividendYield", "symbol",
]


@tool
def simple_screener(screen_type: str, offset: int = 0) -> str:
    """Returns screened assets (stocks, funds, bonds) for a popular Yahoo Finance screen.

    Args:
        screen_type: One of these screens:
            aggressive_small_caps, day_gainers, day_losers, growth_technology_stocks,
            most_actives, most_shorted_stocks, small_cap_gainers,
            undervalued_growth_stocks, undervalued_large_caps,
            conservative_foreign_funds, high_yield_bond, portfolio_anchors,
            solid_large_growth_funds, solid_midcap_growth_funds, top_mutual_funds
        offset: pagination start point (0 for the first 5 results, 5 for the next 5, ...)

    Returns:
        JSON text with 5 matching assets per page.
    """
    screens = yf.PREDEFINED_SCREENER_QUERIES
    if screen_type not in screens:
        return f"Unknown screen_type '{screen_type}'. Valid options: {', '.join(screens)}"
    try:
        result = yf.screen(screens[screen_type]["query"], offset=offset, size=5)
    except Exception as exc:  # network or Yahoo errors should not crash the agent
        return f"The screener failed: {exc}"

    rows = [{k: v for k, v in quote.items() if k in FIELDS} for quote in result.get("quotes", [])]
    return json.dumps(
        {"screen": screen_type, "offset": offset, "total": result.get("total"), "results": rows}
    )


@tool
def get_price_summary(symbol: str, period: str = "1mo") -> str:
    """Summarises a stock's recent price movement.

    Args:
        symbol: ticker symbol, for example AAPL or TSM
        period: one of 5d, 1mo, 3mo, 6mo, 1y

    Returns:
        JSON text with first close, last close, percent change, high and low for the period.
    """
    try:
        history = yf.Ticker(symbol.upper()).history(period=period)
    except Exception as exc:
        return f"Could not fetch prices for '{symbol}': {exc}"
    if history.empty:
        return f"No price data found for '{symbol}'. Check the ticker symbol."

    first, last = float(history["Close"].iloc[0]), float(history["Close"].iloc[-1])
    return json.dumps(
        {
            "symbol": symbol.upper(),
            "period": period,
            "first_close": round(first, 2),
            "last_close": round(last, 2),
            "percent_change": round((last - first) / first * 100, 2),
            "period_high": round(float(history["High"].max()), 2),
            "period_low": round(float(history["Low"].min()), 2),
        }
    )
