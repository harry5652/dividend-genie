"""
Fetches dividend data for a given stock symbol using yfinance.
"""
import logging
import yfinance as yf

logger = logging.getLogger(__name__)


def get_dividend_info(symbol: str) -> dict:
    """
    Return a dict with dividend details for the given ticker symbol.
    Raises ValueError if the symbol is not found or has no dividend data.
    """
    logger.info("Fetching dividend info for symbol: %s", symbol)

    ticker = yf.Ticker(symbol)
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        logger.warning("Symbol not found or no market data: %s", symbol)
        raise ValueError(f"Could not find data for symbol '{symbol}'.")

    dividend_rate = info.get("dividendRate") or 0
    dividend_yield = info.get("dividendYield") or 0
    ex_date = info.get("exDividendDate")
    payout_ratio = info.get("payoutRatio") or 0
    company_name = info.get("shortName") or symbol
    currency = info.get("currency") or "USD"
    price = info.get("regularMarketPrice") or info.get("currentPrice") or 0

    logger.info(
        "Result for %s: rate=%.2f yield=%.2f%% ex_date=%s",
        symbol, dividend_rate, dividend_yield * 100, ex_date,
    )

    return {
        "symbol": symbol,
        "company": company_name,
        "currency": currency,
        "price": price,
        "dividend_rate": dividend_rate,
        "dividend_yield": dividend_yield,
        "ex_dividend_date": ex_date,
        "payout_ratio": payout_ratio,
    }


def format_dividend_message(data: dict) -> str:
    """Format the dividend info dict into a readable Telegram message."""
    yield_pct = f"{data['dividend_yield'] * 100:.2f}%" if data["dividend_yield"] else "N/A"
    payout = f"{data['payout_ratio'] * 100:.1f}%" if data["payout_ratio"] else "N/A"
    ex_date = str(data["ex_dividend_date"]) if data["ex_dividend_date"] else "N/A"
    rate = f"{data['currency']} {data['dividend_rate']:.2f}" if data["dividend_rate"] else "N/A"
    price = f"{data['currency']} {data['price']:.2f}" if data["price"] else "N/A"

    return (
        f"📊 *{data['company']} ({data['symbol']})*\n\n"
        f"💰 Dividend Rate:  {rate} / year\n"
        f"📈 Dividend Yield: {yield_pct}\n"
        f"📅 Ex-Dividend Date: {ex_date}\n"
        f"💼 Payout Ratio: {payout}\n"
        f"🏷 Current Price: {price}"
    )
