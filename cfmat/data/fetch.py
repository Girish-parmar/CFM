"""Fetch historical bars into ``data/<SYMBOL>.csv`` from Yahoo Finance, Alpaca or Interactive Brokers (M16).

    python -m cfmat.data.fetch yahoo TCS.NS INFY.NS ^NSEI --start 2018-01-01
    python -m cfmat.data.fetch alpaca AAPL MSFT --start 2020-01-01 --timeframe 1Day
    python -m cfmat.data.fetch ibkr RELIANCE TCS --exchange NSE --currency INR --duration "5 Y"

Each file is checked (``loaders.ohlcv_problems``) and saved in the standard
shape, so ``data.load_ohlcv_csv`` and the signal service read it directly.
Files go to ``data/`` (git-ignored; set ``CFMAT_DATA_DIR`` or ``--out`` to
change it). Installed as the ``cfmat-fetch`` command too.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from ..infra.paths import user_data_dir
from .loaders import download_prices, ohlcv_problems
from .providers import alpaca_bars, ibkr_bars

SOURCES = ("yahoo", "alpaca", "ibkr")


def file_name(symbol: str) -> str:
    """The CSV name for a symbol: upper case, only the characters the signal service accepts (``^NSEI`` → ``NSEI``)."""
    name = re.sub(r"[^A-Z0-9_.&-]", "", symbol.upper())
    if not name or len(name) > 32:
        raise ValueError(f"cannot make a file name from symbol {symbol!r}")
    return name


def save_bars(bars: pd.DataFrame, symbol: str, folder: str | Path | None = None) -> Path:
    """Write bars to ``<folder>/<SYMBOL>.csv`` (default ``data/``) with a ``date`` column; returns the path."""
    folder = Path(folder) if folder is not None else user_data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{file_name(symbol)}.csv"
    bars.to_csv(path, index_label="date")
    return path


def fetch(source: str, symbol: str, **options) -> pd.DataFrame:
    """Bars for one symbol from ``yahoo``, ``alpaca`` or ``ibkr``; ``options`` go to that source's function."""
    if source == "yahoo":
        return download_prices(symbol, start=options.get("start", "2018-01-01"), end=options.get("end"))
    if source == "alpaca":
        return alpaca_bars(symbol, **options)
    if source == "ibkr":
        return ibkr_bars(symbol, **options)
    raise ValueError(f"source must be one of {SOURCES}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cfmat-fetch", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="source", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("symbols", nargs="+", help="one or more symbols")
    common.add_argument("--out", help="folder for the CSV files (default: data/ or CFMAT_DATA_DIR)")
    yahoo = sub.add_parser("yahoo", parents=[common], help="daily adjusted bars from Yahoo Finance (NSE: TCS.NS)")
    yahoo.add_argument("--start", default="2018-01-01")
    yahoo.add_argument("--end")
    alpaca = sub.add_parser("alpaca", parents=[common], help="US stock bars from Alpaca (keys from the environment)")
    alpaca.add_argument("--start", default="2018-01-01")
    alpaca.add_argument("--end")
    alpaca.add_argument("--timeframe", default="1Day", help="1Day, 1Hour, 15Min, 1Week ...")
    alpaca.add_argument("--adjustment", default="all", choices=["raw", "split", "dividend", "all"])
    alpaca.add_argument("--feed", default="sip", choices=["sip", "iex"])
    ibkr = sub.add_parser("ibkr", parents=[common], help="bars from Interactive Brokers via TWS or IB Gateway")
    ibkr.add_argument("--exchange", default="NSE")
    ibkr.add_argument("--currency", default="INR")
    ibkr.add_argument("--sec-type", default="STK", help="STK for stocks, IND for indices")
    ibkr.add_argument("--duration", default="5 Y", help='IBKR duration per request: "5 Y", "6 M", "10 D"')
    ibkr.add_argument("--bar-size", default="1 day", help='"1 day", "1 hour", "5 mins" ...')
    ibkr.add_argument("--what", default="TRADES", help="TRADES, ADJUSTED_LAST, MIDPOINT ...")
    ibkr.add_argument("--end", help="bars before this time (exchange time); default now")
    ibkr.add_argument("--chunks", type=int, default=1, help="requests walking back in time, paced for IBKR limits")
    ibkr.add_argument("--tz", default="Asia/Kolkata", help="exchange time zone for intraday bars")
    ibkr.add_argument("--port", type=int, default=7497, help="7497 TWS paper, 4002 Gateway paper")
    ibkr.add_argument("--host", default="127.0.0.1")
    ibkr.add_argument("--client-id", type=int, default=17)
    return parser


def _options(args: argparse.Namespace) -> dict:
    if args.source == "yahoo":
        return {"start": args.start, "end": args.end}
    if args.source == "alpaca":
        return {"start": args.start, "end": args.end, "timeframe": args.timeframe, "adjustment": args.adjustment,
                "feed": args.feed}
    return {"exchange": args.exchange, "currency": args.currency, "sec_type": args.sec_type,
            "duration": args.duration, "bar_size": args.bar_size, "what_to_show": args.what, "end": args.end,
            "chunks": args.chunks, "tz": args.tz, "host": args.host, "port": args.port, "client_id": args.client_id}


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point; returns 0 when every symbol was saved."""
    args = _parser().parse_args(argv)
    options, failed = _options(args), 0
    for symbol in args.symbols:
        try:
            bars = fetch(args.source, symbol, **options)
        except (ImportError, RuntimeError, ValueError, ConnectionError, OSError) as exc:
            print(f"FAIL {symbol}: {exc}", file=sys.stderr)
            failed += 1
            continue
        path = save_bars(bars, symbol, args.out)
        print(f"OK   {symbol}: {len(bars)} bars, {bars.index[0]:%Y-%m-%d %H:%M} to {bars.index[-1]:%Y-%m-%d %H:%M} "
              f"-> {path}")
        for problem in ohlcv_problems(bars):
            print(f"     check: {problem}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
