"""
Fetches dividend data for a given stock symbol using yfinance.
Supports NSE (.NS), BSE (.BO), and global exchanges.
"""
import logging
from datetime import datetime, timezone
import yfinance as yf

logger = logging.getLogger(__name__)

# Suffix → exchange label
EXCHANGE_SUFFIXES = {
    ".NS": "NSE",
    ".BO": "BSE",
}

# Candidate suffixes tried in order when user gives a bare symbol (e.g. "ITC")
INDIAN_SUFFIXES = [".NS", ".BO"]


def _fetch(symbol: str) -> dict | None:
    """
    Try to fetch a valid ticker for `symbol`.
    Returns the info dict on success, None if no market data found.
    """
    logger.debug("Trying ticker: %s", symbol)
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    price = info.get("regularMarketPrice") or info.get("currentPrice")
    if price:
        return info
    return None


def get_dividend_info(symbol: str) -> dict:
    """
    Return a dict with dividend details for the given ticker symbol.

    Resolution order:
      1. Symbol as-is (handles AAPL, ITC.NS, ITC.BO, etc.)
      2. Symbol + .NS  (NSE)
      3. Symbol + .BO  (BSE)

    Raises ValueError if no data is found on any exchange.
    """
    symbol = symbol.upper().strip()
    logger.info("Resolving symbol: %s", symbol)

    # Build candidate list
    candidates: list[str] = [symbol]
    if not any(symbol.endswith(s) for s in EXCHANGE_SUFFIXES):
        # Bare symbol — try Indian exchanges before giving up
        candidates += [symbol + s for s in INDIAN_SUFFIXES]

    info = None
    resolved = symbol
    for candidate in candidates:
        info = _fetch(candidate)
        if info:
            resolved = candidate
            logger.info("Resolved %s → %s", symbol, resolved)
            break

    if not info:
        raise ValueError(
            f"No data found for '{symbol}'. "
            "Try adding the exchange suffix: ITC.NS (NSE) or ITC.BO (BSE)."
        )

    # Determine exchange label
    suffix = next((s for s in EXCHANGE_SUFFIXES if resolved.endswith(s)), None)
    exchange_label = EXCHANGE_SUFFIXES.get(suffix) if suffix else (
        info.get("exchange") or "Global"
    )

    dividend_rate = info.get("dividendRate") or 0
    payout_ratio  = info.get("payoutRatio") or 0
    company_name  = info.get("shortName") or resolved
    currency      = info.get("currency") or "INR"
    price         = info.get("regularMarketPrice") or info.get("currentPrice") or 0
    sector        = info.get("sector") or "N/A"

    # Convert Unix timestamp → readable date string
    ex_date_raw = info.get("exDividendDate")
    if ex_date_raw:
        try:
            ex_date = datetime.fromtimestamp(int(ex_date_raw), tz=timezone.utc).strftime("%d %b %Y")
        except Exception:
            ex_date = str(ex_date_raw)
    else:
        ex_date = None

    # Calculate yield from rate/price to avoid yfinance returning
    # inconsistent formats (decimal vs whole-number %) for Indian stocks
    if dividend_rate and price:
        dividend_yield = (dividend_rate / price) * 100  # always a true percentage
    else:
        raw_yield = info.get("dividendYield") or 0
        # yfinance may return 0.0552 (decimal) or 5.52 (already %) — normalise
        dividend_yield = raw_yield if raw_yield > 1 else raw_yield * 100

    logger.info(
        "%s | rate=%.2f yield=%.2f%% ex_date=%s exchange=%s",
        resolved, dividend_rate, dividend_yield, ex_date, exchange_label,
    )

    return {
        "symbol":           resolved,
        "company":          company_name,
        "exchange":         exchange_label,
        "currency":         currency,
        "price":            price,
        "sector":           sector,
        "dividend_rate":    dividend_rate,
        "dividend_yield":   dividend_yield,   # always a true % value now
        "ex_dividend_date": ex_date,          # always a string or None
        "payout_ratio":     payout_ratio,
    }


def format_dividend_message(data: dict) -> str:
    """Format the dividend info dict into a readable Telegram message."""
    yield_pct = f"{data['dividend_yield']:.2f}%" if data["dividend_yield"] else "N/A"
    payout    = f"{data['payout_ratio'] * 100:.1f}%" if data["payout_ratio"]  else "N/A"
    ex_date   = str(data["ex_dividend_date"])        if data["ex_dividend_date"] else "N/A"
    rate      = (
        f"{data['currency']} {data['dividend_rate']:.2f} / year"
        if data["dividend_rate"] else "N/A"
    )
    price = (
        f"{data['currency']} {data['price']:.2f}"
        if data["price"] else "N/A"
    )

    return (
        f"📊 *{data['company']} ({data['symbol']})*\n"
        f"🏛 Exchange: {data['exchange']}  |  🏭 {data['sector']}\n\n"
        f"💰 Dividend Rate:    {rate}\n"
        f"📈 Dividend Yield:   {yield_pct}\n"
        f"📅 Ex-Dividend Date: {ex_date}\n"
        f"💼 Payout Ratio:     {payout}\n"
        f"🏷 Current Price:    {price}"
    )
