"""
Core dividend service.
Combines yfinance (price / yield), NSE (ex-date / record-date / amount),
and Screener.in links into a single enriched result.
"""
import logging
from datetime import datetime, timezone, date as date_type

import yfinance as yf

from app.services.nse_service import get_nse_dividend_detail
from app.services.screener_service import (
    get_screener_url,
    get_stockedge_url,
    get_screener_dividend_history,
)

logger = logging.getLogger(__name__)

EXCHANGE_SUFFIXES = {".NS": "NSE", ".BO": "BSE"}
INDIAN_SUFFIXES   = [".NS", ".BO"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _yf_fetch(symbol: str) -> dict | None:
    logger.debug("yfinance fetch: %s", symbol)
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception as e:
        logger.warning("yfinance error for %s: %s", symbol, e)
        return None
    if info.get("regularMarketPrice") or info.get("currentPrice"):
        return info
    return None


def _fmt_date(d: date_type) -> str:
    return d.strftime("%d %b %Y")


# ── main API ─────────────────────────────────────────────────────────────────

def get_dividend_info(symbol: str, shares: int | None = None) -> dict:
    """
    Resolve symbol → fetch yfinance + NSE + Screener and return enriched dict.
    Raises ValueError if the stock cannot be found on any source.
    """
    symbol = symbol.upper().strip()
    logger.info("get_dividend_info: symbol=%s shares=%s", symbol, shares)

    # 1. Resolve ticker via yfinance
    candidates = [symbol]
    if not any(symbol.endswith(s) for s in EXCHANGE_SUFFIXES):
        candidates += [symbol + s for s in INDIAN_SUFFIXES]

    yf_info   = None
    resolved  = symbol
    for candidate in candidates:
        yf_info = _yf_fetch(candidate)
        if yf_info:
            resolved = candidate
            break

    if not yf_info:
        raise ValueError(
            f"No data found for '{symbol}'. "
            "Try adding the exchange suffix: ITC.NS (NSE) or ITC.BO (BSE)."
        )

    suffix         = next((s for s in EXCHANGE_SUFFIXES if resolved.endswith(s)), None)
    exchange_label = EXCHANGE_SUFFIXES.get(suffix) or yf_info.get("exchange") or "Global"
    is_indian      = suffix in (".NS", ".BO") or exchange_label in ("NSE", "BSE")

    company_name = yf_info.get("shortName") or resolved
    currency     = yf_info.get("currency") or ("INR" if is_indian else "USD")
    price        = yf_info.get("regularMarketPrice") or yf_info.get("currentPrice") or 0
    sector       = yf_info.get("sector") or "N/A"
    payout_ratio = yf_info.get("payoutRatio") or 0

    # yfinance dividend rate (annual)
    yf_rate = yf_info.get("dividendRate") or 0

    # Ex-date from yfinance (unix timestamp → string)
    yf_ex_date = None
    raw_ts = yf_info.get("exDividendDate")
    if raw_ts:
        try:
            yf_ex_date = datetime.fromtimestamp(int(raw_ts), tz=timezone.utc).strftime("%d %b %Y")
        except Exception:
            yf_ex_date = str(raw_ts)

    # 2. Enrich from NSE for Indian stocks
    nse = None
    if is_indian:
        nse = get_nse_dividend_detail(resolved)

    # Prefer NSE data; fall back to yfinance
    if nse:
        ex_date = _fmt_date(nse["ex_date"]) if isinstance(nse.get("ex_date"), date_type) else yf_ex_date
        record_date = _fmt_date(nse["record_date"]) if isinstance(nse.get("record_date"), date_type) else None
        dividend_amount = nse.get("amount") or yf_rate
    else:
        ex_date         = yf_ex_date
        record_date     = None
        dividend_amount = yf_rate

    # 3. Dividend yield — calculate from amount/price to avoid yfinance inconsistency
    if dividend_amount and price:
        dividend_yield = (dividend_amount / price) * 100
    else:
        raw_yield = yf_info.get("dividendYield") or 0
        dividend_yield = raw_yield if raw_yield > 1 else raw_yield * 100

    # 4. Screener dividend history (optional enrichment)
    screener_history = get_screener_dividend_history(resolved) if is_indian else []

    # 5. Estimated payout
    estimated_payout = round(dividend_amount * shares, 2) if (dividend_amount and shares) else None

    logger.info(
        "%s | amount=%s yield=%.2f%% ex=%s record=%s exchange=%s",
        resolved, dividend_amount, dividend_yield, ex_date, record_date, exchange_label,
    )

    return {
        "symbol":           resolved,
        "company":          company_name,
        "exchange":         exchange_label,
        "currency":         currency,
        "price":            price,
        "sector":           sector,
        "dividend_amount":  dividend_amount,
        "dividend_yield":   dividend_yield,
        "ex_dividend_date": ex_date,
        "record_date":      record_date,
        "payout_ratio":     payout_ratio,
        "screener_history": screener_history,
        "estimated_payout": estimated_payout,
        "shares":           shares,
        "screener_url":     get_screener_url(resolved),
        "stockedge_url":    get_stockedge_url(resolved),
    }


def format_dividend_message(data: dict) -> str:
    curr    = "₹" if data["currency"] == "INR" else f"{data['currency']} "
    amount  = f"{curr}{data['dividend_amount']:.2f}/share" if data["dividend_amount"] else "N/A"
    yield_s = f"{data['dividend_yield']:.2f}%" if data["dividend_yield"] else "N/A"
    ex_date = data["ex_dividend_date"] or "N/A"
    rec     = data["record_date"] or "N/A"
    payout  = f"{data['payout_ratio'] * 100:.1f}%" if data["payout_ratio"] else "N/A"
    price_s = f"{curr}{data['price']:.2f}" if data["price"] else "N/A"

    lines = [
        f"📊 *{data['company']}* (`{data['symbol']}`)",
        f"🏛 {data['exchange']}  |  🏭 {data['sector']}",
        "",
        f"💰 Dividend Amount:   {amount}",
        f"📈 Dividend Yield:    {yield_s}",
        f"📅 Ex-Dividend Date:  {ex_date}",
        f"📋 Record Date:       {rec}",
        f"💼 Payout Ratio:      {payout}",
        f"🏷 Current Price:     {price_s}",
    ]

    # Estimated payout block
    if data.get("estimated_payout") is not None:
        lines += [
            "",
            f"📦 *If you own {data['shares']:,} shares:*",
            f"   Expected Dividend = {curr}{data['estimated_payout']:,.2f}",
        ]

    # Screener history (last 3 dividends)
    if data.get("screener_history"):
        lines.append("\n📜 *Recent Dividend History* (Screener.in):")
        for row in data["screener_history"][:3]:
            lines.append(f"   • {row['date']}: {curr}{row['amount']}")

    lines += [
        "",
        f"[🔍 Screener]({data['screener_url']})  |  [📊 StockEdge]({data['stockedge_url']})",
    ]

    return "\n".join(lines)
