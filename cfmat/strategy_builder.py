"""Strategy Creator: build, backtest and optimise rule-based strategies (Module 17).

Write a strategy as plain rules over indicators, prices and patterns:

    spec = StrategySpec(
        name="RSI-2 pullback",
        long_entry=["close > sma(200)", "rsi(2) < {oversold}"],
        long_exit=["close > sma(5)"],
        stop_atr=3, max_bars=10, params={"oversold": 10},
    )
    result = backtest(bars, spec)

Rules in a list are combined with AND; a single rule may use ``and`` / ``or`` /
``not``. ``{placeholders}`` are filled from ``params`` (or a parameter grid).
Rules are parsed with Python's ``ast`` module and only whitelisted syntax is
executed; nothing is passed to ``eval``.

Execution model: rules are evaluated at each bar's close; orders fill at the
next bar's open (with slippage); protective stops and targets fill intrabar at
the stop/target price, or at the open if price gaps through them. When a stop
and a target are both touched in the same bar, the stop is assumed first.
"""

from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass, field, fields, replace
from itertools import product
from typing import Callable

import numpy as np
import pandas as pd

from . import indicators as ind
from . import patterns as pat
from .metrics import equity_curve, max_drawdown, performance_summary, sharpe_ratio
from .parallel import parallel_map, shared

# ---------------------------------------------------------------------------
# Expression language
# ---------------------------------------------------------------------------

PRICE_FIELDS = ("open", "high", "low", "close", "volume")
FUNCTIONS: dict[str, Callable] = {}


def register(name: str):
    """Add a function to the rule language: ``fn(bars, *args) -> Series``."""
    def wrap(fn):
        FUNCTIONS[name] = fn
        return fn
    return wrap


def _src(bars, args, default="close"):
    """Split args into (source series, numeric args); source defaults to a price field."""
    if args and isinstance(args[0], pd.Series):
        return args[0], args[1:]
    return bars[default], args


def _num(args, i, default):
    return args[i] if len(args) > i else default


@register("sma")
def _sma(bars, *a):
    s, a = _src(bars, a)
    return ind.sma(s, int(_num(a, 0, 20)))


@register("ema")
def _ema(bars, *a):
    s, a = _src(bars, a)
    return ind.ema(s, int(_num(a, 0, 20)))


@register("rsi")
def _rsi(bars, *a):
    s, a = _src(bars, a)
    return ind.rsi(s, int(_num(a, 0, 14)))


@register("zscore")
def _zscore(bars, *a):
    s, a = _src(bars, a)
    return ind.rolling_zscore(s, int(_num(a, 0, 20)))


@register("roc")
def _roc(bars, *a):
    s, a = _src(bars, a)
    return ind.rate_of_change(s, int(_num(a, 0, 10)))


@register("highest")
def _highest(bars, *a):
    s, a = _src(bars, a, default="high")
    return s.rolling(int(_num(a, 0, 20))).max()


@register("lowest")
def _lowest(bars, *a):
    s, a = _src(bars, a, default="low")
    return s.rolling(int(_num(a, 0, 20))).min()


@register("atr")
def _atr(bars, *a):
    return ind.atr(bars, int(_num(a, 0, 14)))


@register("adx")
def _adx(bars, *a):
    return ind.adx(bars, int(_num(a, 0, 14)))["adx"]


@register("plus_di")
def _pdi(bars, *a):
    return ind.adx(bars, int(_num(a, 0, 14)))["plus_di"]


@register("minus_di")
def _mdi(bars, *a):
    return ind.adx(bars, int(_num(a, 0, 14)))["minus_di"]


def _macd(bars, a, col):
    return ind.macd(bars["close"], int(_num(a, 0, 12)), int(_num(a, 1, 26)), int(_num(a, 2, 9)))[col]


FUNCTIONS["macd"] = lambda bars, *a: _macd(bars, a, "macd")
FUNCTIONS["macd_signal"] = lambda bars, *a: _macd(bars, a, "signal")
FUNCTIONS["macd_hist"] = lambda bars, *a: _macd(bars, a, "histogram")


def _bb(bars, a, col):
    return ind.bollinger_bands(bars["close"], int(_num(a, 0, 20)), float(_num(a, 1, 2.0)))[col]


FUNCTIONS["bb_upper"] = lambda bars, *a: _bb(bars, a, "upper")
FUNCTIONS["bb_lower"] = lambda bars, *a: _bb(bars, a, "lower")
FUNCTIONS["bb_mid"] = lambda bars, *a: _bb(bars, a, "middle")
FUNCTIONS["bb_width"] = lambda bars, *a: ind.bollinger_bandwidth(bars["close"], int(_num(a, 0, 20)), float(_num(a, 1, 2.0)))
FUNCTIONS["supertrend"] = lambda bars, *a: ind.supertrend(bars, int(_num(a, 0, 10)), float(_num(a, 1, 3.0)))["supertrend"]
FUNCTIONS["supertrend_dir"] = lambda bars, *a: ind.supertrend(bars, int(_num(a, 0, 10)), float(_num(a, 1, 3.0)))["direction"]
FUNCTIONS["stoch_k"] = lambda bars, *a: ind.stochastic(bars, int(_num(a, 0, 14)), int(_num(a, 1, 3)))["k"]
FUNCTIONS["stoch_d"] = lambda bars, *a: ind.stochastic(bars, int(_num(a, 0, 14)), int(_num(a, 1, 3)))["d"]
FUNCTIONS["er"] = lambda bars, *a: ind.efficiency_ratio(bars["close"], int(_num(a, 0, 20)))
FUNCTIONS["vol"] = lambda bars, *a: 100 * ind.rolling_volatility(bars["close"], int(_num(a, 0, 20)))
FUNCTIONS["volume_sma"] = lambda bars, *a: bars["volume"].rolling(int(_num(a, 0, 20))).mean()


def _to_series(bars, x):
    return x if isinstance(x, pd.Series) else pd.Series(x, index=bars.index)


FUNCTIONS["prev"] = lambda bars, x, k=1: _to_series(bars, x).shift(int(k))
FUNCTIONS["change"] = lambda bars, x, k=1: _to_series(bars, x).pct_change(int(k)) * 100
FUNCTIONS["abs"] = lambda bars, x: _to_series(bars, x).abs()
FUNCTIONS["max"] = lambda bars, a, b: np.maximum(_to_series(bars, a), _to_series(bars, b))
FUNCTIONS["min"] = lambda bars, a, b: np.minimum(_to_series(bars, a), _to_series(bars, b))


@register("cross_above")
def _cross_above(bars, a, b):
    a, b = _to_series(bars, a), _to_series(bars, b)
    return (a > b) & (a.shift(1) <= b.shift(1))


@register("cross_below")
def _cross_below(bars, a, b):
    a, b = _to_series(bars, a), _to_series(bars, b)
    return (a < b) & (a.shift(1) >= b.shift(1))


@register("recent")
def _recent(bars, cond, k=5):
    """True if ``cond`` was true on any of the last ``k`` bars (including today)."""
    return _to_series(bars, cond).fillna(False).astype(float).rolling(int(k), min_periods=1).max() > 0


_COMPARE = {ast.Gt: "__gt__", ast.GtE: "__ge__", ast.Lt: "__lt__", ast.LtE: "__le__", ast.Eq: "__eq__", ast.NotEq: "__ne__"}
_ARITH = {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply, ast.Div: np.divide, ast.Pow: np.power}


class Evaluator:
    """Evaluate rule strings against one set of bars, caching every sub-expression."""

    def __init__(self, bars: pd.DataFrame) -> None:
        self.bars = bars
        self._cache: dict[str, object] = {}

    def __call__(self, expr: str):
        try:
            tree = ast.parse(expr.strip(), mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"cannot parse rule {expr!r}: {exc.msg}") from exc
        return self._eval(tree.body)

    def boolean(self, expr: str) -> pd.Series:
        value = self(expr)
        if not isinstance(value, pd.Series):
            return pd.Series(bool(value), index=self.bars.index)
        return value.fillna(False).astype(bool)

    def _eval(self, node):
        key = ast.dump(node)
        if key not in self._cache:
            self._cache[key] = self._compute(node)
        return self._cache[key]

    def _compute(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, bool)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in PRICE_FIELDS:
                return self.bars[node.id]
            if node.id in pat.ALL_PATTERNS:
                return pat.ALL_PATTERNS[node.id](self.bars)
            raise ValueError(f"unknown name {node.id!r}")
        if isinstance(node, ast.BoolOp):
            values = [self._as_bool(self._eval(v)) for v in node.values]
            out = values[0]
            for v in values[1:]:
                out = (out & v) if isinstance(node.op, ast.And) else (out | v)
            return out
        if isinstance(node, ast.UnaryOp):
            v = self._eval(node.operand)
            if isinstance(node.op, ast.Not):
                return ~self._as_bool(v)
            if isinstance(node.op, ast.USub):
                return -v
            if isinstance(node.op, ast.UAdd):
                return v
        if isinstance(node, ast.BinOp) and type(node.op) in _ARITH:
            return _ARITH[type(node.op)](self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.Compare) and all(type(op) in _COMPARE for op in node.ops):
            left = self._eval(node.left)
            result = None
            for op, comp in zip(node.ops, node.comparators):
                right = self._eval(comp)
                l_ser, r_ser = _to_series(self.bars, left), _to_series(self.bars, right)
                part = getattr(l_ser, _COMPARE[type(op)])(r_ser)
                result = part if result is None else (result & part)
                left = right
            return result
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            args = [self._eval(a) for a in node.args]
            name = node.func.id
            if name in FUNCTIONS:
                return FUNCTIONS[name](self.bars, *args)
            if name in pat.ALL_PATTERNS:
                return pat.ALL_PATTERNS[name](self.bars, *args)
            raise ValueError(f"unknown function {name!r}; available: {sorted(FUNCTIONS) + sorted(pat.ALL_PATTERNS)}")
        raise ValueError(f"unsupported syntax in rule: {ast.unparse(node)!r}")

    def _as_bool(self, v) -> pd.Series:
        return _to_series(self.bars, v).fillna(False).astype(bool)


def available_functions() -> list[str]:
    return sorted(FUNCTIONS) + sorted(pat.ALL_PATTERNS) + list(PRICE_FIELDS)


# ---------------------------------------------------------------------------
# Strategy specification
# ---------------------------------------------------------------------------

@dataclass
class StrategySpec:
    name: str
    long_entry: list[str] = field(default_factory=list)
    long_exit: list[str] = field(default_factory=list)
    short_entry: list[str] = field(default_factory=list)
    short_exit: list[str] = field(default_factory=list)
    stop_atr: float | str | None = None      # protective stop, in ATRs from entry
    target_atr: float | str | None = None    # profit target, in ATRs from entry
    trail_atr: float | str | None = None     # trailing stop, in ATRs from the close
    max_bars: int | str | None = None        # time exit after this many bars
    atr_period: int = 14
    params: dict = field(default_factory=dict)
    category: str = "custom"
    description: str = ""

    def resolve(self, **overrides) -> "StrategySpec":
        """Fill ``{placeholders}`` from ``params`` updated with ``overrides``."""
        p = {**self.params, **overrides}

        def fmt_rules(rules):
            return [r.format(**p) for r in rules]

        def fmt_num(v, cast):
            if isinstance(v, str):
                return cast(float(v.format(**p)))
            return v

        try:
            return replace(
                self, params=p,
                long_entry=fmt_rules(self.long_entry), long_exit=fmt_rules(self.long_exit),
                short_entry=fmt_rules(self.short_entry), short_exit=fmt_rules(self.short_exit),
                stop_atr=fmt_num(self.stop_atr, float), target_atr=fmt_num(self.target_atr, float),
                trail_atr=fmt_num(self.trail_atr, float), max_bars=fmt_num(self.max_bars, int),
            )
        except KeyError as exc:
            raise ValueError(f"strategy {self.name!r} needs a value for parameter {exc}") from exc

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: str | None = None) -> str:
        text = json.dumps(self.to_dict(), indent=2)
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        return text

    @classmethod
    def from_dict(cls, d: dict) -> "StrategySpec":
        known = {f.name for f in fields(cls)}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"unknown strategy fields: {sorted(unknown)}")
        return cls(**d)

    @classmethod
    def from_json(cls, text_or_path: str) -> "StrategySpec":
        text = text_or_path
        if not text_or_path.lstrip().startswith("{"):
            with open(text_or_path, encoding="utf-8") as fh:
                text = fh.read()
        return cls.from_dict(json.loads(text))


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    spec: StrategySpec
    returns: pd.Series
    position: pd.Series
    trades: pd.DataFrame

    @property
    def equity(self) -> pd.Series:
        return equity_curve(self.returns)

    def stats(self) -> pd.Series:
        from .report import backtest_stats
        return backtest_stats(self)


def signals(bars: pd.DataFrame, spec: StrategySpec) -> pd.DataFrame:
    """Evaluate the four rule lists (AND within each list) at every close."""
    ev = Evaluator(bars)

    def all_of(rules):
        if not rules:
            return pd.Series(False, index=bars.index)
        out = ev.boolean(rules[0])
        for r in rules[1:]:
            out &= ev.boolean(r)
        return out

    return pd.DataFrame({"long_entry": all_of(spec.long_entry), "long_exit": all_of(spec.long_exit),
                         "short_entry": all_of(spec.short_entry), "short_exit": all_of(spec.short_exit)})


def backtest(
    bars: pd.DataFrame,
    spec: StrategySpec,
    cost_bps: float = 5.0,
    slippage_bps: float = 2.0,
    size: float = 1.0,
    allow_reverse: bool = True,
) -> BacktestResult:
    """Run ``spec`` bar by bar. Returns daily returns (fraction of capital, with
    ``size`` × capital notional per position), positions and a trade list."""
    spec = spec.resolve()
    sig = signals(bars, spec)
    le, lx = sig["long_entry"].to_numpy(), sig["long_exit"].to_numpy()
    se, sx = sig["short_entry"].to_numpy(), sig["short_exit"].to_numpy()
    o, h, l, c = (bars[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    a = ind.atr(bars, spec.atr_period).to_numpy()
    idx = bars.index
    n = len(bars)
    cost, slip = cost_bps / 1e4, slippage_bps / 1e4
    stop_dist = spec.stop_atr if spec.stop_atr is not None else spec.trail_atr

    ret = np.zeros(n)
    held = np.zeros(n)
    trades = []
    pos, entry_px, entry_i, stop, target = 0, 0.0, 0, None, None
    pending = None

    def close_trade(i, px, reason):
        trades.append({"side": "long" if pos == 1 else "short", "entry_time": idx[entry_i], "entry_price": entry_px,
                       "exit_time": idx[i], "exit_price": px, "bars": i - entry_i + 1,
                       "return": pos * (px / entry_px - 1) - 2 * cost, "reason": reason})

    for i in range(n):
        ref = c[i - 1] if i > 0 else o[i]
        day = 0.0
        if pending is not None:
            kind, arg = pending
            pending = None
            if pos != 0:                                   # exit (or first leg of a reversal) at the open
                px = o[i] * (1 - slip * pos)
                day += pos * (px / ref - 1) - cost
                close_trade(i, px, arg if kind == "exit" else "reverse")
                pos = 0
            if kind in ("enter", "reverse"):
                side = arg if kind == "enter" else -held[i - 1]
                px = o[i] * (1 + slip * side)
                pos, entry_px, entry_i, ref = int(side), px, i, px
                day -= cost
                atr_then = a[i - 1] if i > 0 else np.nan
                stop = px - side * stop_dist * atr_then if stop_dist is not None and not np.isnan(atr_then) else None
                target = (px + side * spec.target_atr * atr_then
                          if spec.target_atr is not None and not np.isnan(atr_then) else None)
        if pos != 0:
            hit_stop = stop is not None and ((pos == 1 and l[i] <= stop) or (pos == -1 and h[i] >= stop))
            hit_target = target is not None and ((pos == 1 and h[i] >= target) or (pos == -1 and l[i] <= target))
            if hit_stop or hit_target:
                if hit_stop:
                    level, reason = stop, "stop"
                    px = min(o[i], level) if pos == 1 else max(o[i], level)
                else:
                    level, reason = target, "target"
                    px = max(o[i], level) if pos == 1 else min(o[i], level)
                if i == entry_i:                           # entered at this open: can't fill beyond it
                    px = level
                px *= 1 - slip * pos
                day += pos * (px / ref - 1) - cost
                close_trade(i, px, reason)
                pos, stop, target = 0, None, None
        if pos != 0:
            day += pos * (c[i] / ref - 1)
            if spec.trail_atr is not None and not np.isnan(a[i]):
                trail = c[i] - pos * spec.trail_atr * a[i]
                stop = trail if stop is None else (max(stop, trail) if pos == 1 else min(stop, trail))
        ret[i] = day * size
        held[i] = pos
        if i == n - 1:
            break
        if pos == 1:
            if allow_reverse and se[i]:
                pending = ("reverse", None)
            elif lx[i]:
                pending = ("exit", "signal")
            elif spec.max_bars and i - entry_i + 1 >= spec.max_bars:
                pending = ("exit", "time")
        elif pos == -1:
            if allow_reverse and le[i]:
                pending = ("reverse", None)
            elif sx[i]:
                pending = ("exit", "signal")
            elif spec.max_bars and i - entry_i + 1 >= spec.max_bars:
                pending = ("exit", "time")
        elif le[i] != se[i]:
            pending = ("enter", 1 if le[i] else -1)
    if pos != 0:
        close_trade(n - 1, c[-1], "end of data")
    trade_cols = ["side", "entry_time", "entry_price", "exit_time", "exit_price", "bars", "return", "reason"]
    return BacktestResult(spec, pd.Series(ret, index=idx, name="strategy_return"),
                          pd.Series(held, index=idx, name="position"), pd.DataFrame(trades, columns=trade_cols))


# ---------------------------------------------------------------------------
# Optimisation (parallel)
# ---------------------------------------------------------------------------

def expand_grid(grid: dict[str, list]) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, values)) for values in product(*(grid[k] for k in keys))]


def _score(result: BacktestResult, rows: slice | None) -> dict:
    r = result.returns if rows is None else result.returns.iloc[rows]
    t = result.trades
    if rows is not None and len(t):
        start, end = result.returns.index[rows][[0, -1]]
        t = t[(t["exit_time"] >= start) & (t["exit_time"] <= end)]
    return {"sharpe": sharpe_ratio(r), "cagr": performance_summary(r)["cagr"],
            "max_dd": max_drawdown(equity_curve(r)), "trades": len(t),
            "win_rate": float((t["return"] > 0).mean()) if len(t) else 0.0}


def _sweep_task(params: dict) -> dict:
    bars, spec, kwargs, rows = shared("bars"), shared("spec"), shared("kwargs"), shared("rows")
    try:
        result = backtest(bars, spec.resolve(**params), **kwargs)
        return {**params, **_score(result, rows)}
    except ValueError as exc:
        return {**params, "sharpe": np.nan, "error": str(exc)}


def sweep(
    bars: pd.DataFrame,
    spec: StrategySpec,
    grid: dict[str, list] | list[dict],
    workers: int = 1,
    backend: str = "process",
    rows: slice | None = None,
    **backtest_kwargs,
) -> pd.DataFrame:
    """Backtest every parameter combination; results sorted by Sharpe.

    ``rows`` restricts scoring to a slice of bars (e.g. a training window);
    pass bars that end at the window so no later data is ever touched.
    """
    combos = expand_grid(grid) if isinstance(grid, dict) else list(grid)
    out = parallel_map(_sweep_task, combos, workers=workers, backend=backend,
                       shared={"bars": bars, "spec": spec, "kwargs": backtest_kwargs, "rows": rows})
    return pd.DataFrame(out).sort_values("sharpe", ascending=False, ignore_index=True)


def coarse_to_fine(
    bars: pd.DataFrame,
    spec: StrategySpec,
    grid: dict[str, list],
    top_k: int = 3,
    workers: int = 1,
    backend: str = "process",
    rows: slice | None = None,
    **backtest_kwargs,
) -> tuple[pd.DataFrame, int]:
    """Smarter search: test every other value of each parameter first, then only
    the neighbours of the ``top_k`` coarse winners. Returns (results, evaluations)."""
    coarse_grid = {k: v[::2] if len(v) > 2 else v for k, v in grid.items()}
    first = sweep(bars, spec, coarse_grid, workers, backend, rows, **backtest_kwargs)
    tried = {tuple(sorted(r.items())) for r in expand_grid(coarse_grid)}
    neighbours = []
    for _, row in first.dropna(subset=["sharpe"]).head(top_k).iterrows():
        axes = {}
        for k, values in grid.items():
            i = values.index(row[k])
            axes[k] = values[max(0, i - 1): i + 2]
        for combo in expand_grid(axes):
            key = tuple(sorted(combo.items()))
            if key not in tried:
                tried.add(key)
                neighbours.append(combo)
    second = sweep(bars, spec, neighbours, workers, backend, rows, **backtest_kwargs) if neighbours else first.iloc[:0]
    results = pd.concat([first, second], ignore_index=True).sort_values("sharpe", ascending=False, ignore_index=True)
    return results, len(results)


def _like(values: list, v):
    """Cast a value read back from a results table to the type used in the grid."""
    if all(isinstance(x, (int, np.integer)) and not isinstance(x, bool) for x in values):
        return int(v)
    if all(isinstance(x, (float, int)) for x in values):
        return float(v)
    return v


def walk_forward(
    bars: pd.DataFrame,
    spec: StrategySpec,
    grid: dict[str, list],
    train: int = 750,
    test: int = 250,
    workers: int = 1,
    backend: str = "process",
    **backtest_kwargs,
) -> tuple[pd.Series, pd.DataFrame]:
    """Re-optimise on each training window, trade the next test window."""
    oos, chosen = [], []
    for start in range(0, len(bars) - train - test + 1, test):
        train_end, test_end = start + train, start + train + test
        table = sweep(bars.iloc[:train_end], spec, grid, workers, backend, slice(start, train_end), **backtest_kwargs)
        best = {k: _like(grid[k], table.iloc[0][k]) for k in grid}
        result = backtest(bars.iloc[:test_end], spec.resolve(**best), **backtest_kwargs)
        oos.append(result.returns.iloc[train_end:test_end])
        chosen.append({"test_start": bars.index[train_end], **best, "train_sharpe": table.iloc[0]["sharpe"]})
    if not oos:
        raise ValueError("not enough bars for the requested train/test windows")
    return pd.concat(oos), pd.DataFrame(chosen)


def _matrix_task(task: tuple[str, str]) -> dict:
    symbol, name = task
    result = backtest(shared("universe")[symbol], shared("specs")[name], **shared("kwargs"))
    return {"symbol": symbol, "strategy": name, **_score(result, None)}


def strategy_matrix(
    universe: dict[str, pd.DataFrame],
    specs: dict[str, StrategySpec],
    workers: int = 1,
    backend: str = "process",
    **backtest_kwargs,
) -> pd.DataFrame:
    """Backtest every strategy on every instrument (long format: one row per pair)."""
    tasks = [(s, n) for s in universe for n in specs]
    rows = parallel_map(_matrix_task, tasks, workers=workers, backend=backend,
                        shared={"universe": universe, "specs": specs, "kwargs": backtest_kwargs})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Strategy library
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, StrategySpec] = {
    "trend_up_breakout": StrategySpec(
        name="Trend up: Donchian breakout (long only)", category="trend_up",
        long_entry=["close > prev(highest(high, {entry}), 1)", "adx(14) > {adx_min}", "close > sma({trend})"],
        long_exit=["close < prev(lowest(low, {exit}), 1)"],
        trail_atr="{trail}", params={"entry": 20, "exit": 10, "adx_min": 20, "trend": 100, "trail": 3.0},
        description="Buy a 20-day high in an established uptrend; exit on a 10-day low or a 3-ATR trailing stop."),
    "trend_down_breakdown": StrategySpec(
        name="Trend down: Donchian breakdown (short only)", category="trend_down",
        short_entry=["close < prev(lowest(low, {entry}), 1)", "adx(14) > {adx_min}", "close < sma({trend})"],
        short_exit=["close > prev(highest(high, {exit}), 1)"],
        trail_atr="{trail}", params={"entry": 20, "exit": 10, "adx_min": 20, "trend": 100, "trail": 3.0},
        description="Short a 20-day low in an established downtrend (futures or F&O stocks); mirror of the breakout."),
    "trend_supertrend": StrategySpec(
        name="Trend both ways: Supertrend", category="trend_both",
        long_entry=["supertrend_dir({period}, {mult}) == 1", "adx(14) > {adx_min}"],
        long_exit=["supertrend_dir({period}, {mult}) == -1"],
        short_entry=["supertrend_dir({period}, {mult}) == -1", "adx(14) > {adx_min}"],
        short_exit=["supertrend_dir({period}, {mult}) == 1"],
        params={"period": 10, "mult": 3.0, "adx_min": 20},
        description="Long above the Supertrend line, short below it, only when ADX confirms a trend."),
    "trend_ema_cross": StrategySpec(
        name="Trend both ways: EMA crossover", category="trend_both",
        long_entry=["ema({fast}) > ema({slow})", "recent(cross_above(ema({fast}), ema({slow})), 3)"],
        long_exit=["cross_below(ema({fast}), ema({slow}))"],
        short_entry=["ema({fast}) < ema({slow})", "recent(cross_below(ema({fast}), ema({slow})), 3)"],
        short_exit=["cross_above(ema({fast}), ema({slow}))"],
        stop_atr=3.0, params={"fast": 20, "slow": 50}),
    "range_bollinger_rsi": StrategySpec(
        name="Range-bound: Bollinger + RSI reversion", category="range",
        long_entry=["adx(14) < {adx_max}", "close < bb_lower({n}, {k})", "rsi(14) < {rsi_low}"],
        long_exit=["close > bb_mid({n})"],
        short_entry=["adx(14) < {adx_max}", "close > bb_upper({n}, {k})", "rsi(14) > 100 - {rsi_low}"],
        short_exit=["close < bb_mid({n})"],
        stop_atr=2.0, max_bars=15, params={"n": 20, "k": 2.0, "adx_max": 20, "rsi_low": 35},
        description="Fade band extremes only when ADX says there is no trend."),
    "range_box": StrategySpec(
        name="Range-bound: buy support, sell resistance", category="range",
        long_entry=["er(20) < 0.3", "low <= lowest(low, {n}) * 1.005", "rsi(5) < 30"],
        long_exit=["high >= highest(high, {n}) * 0.99 or rsi(5) > 70"],
        short_entry=["er(20) < 0.3", "high >= highest(high, {n}) * 0.995", "rsi(5) > 70"],
        short_exit=["low <= lowest(low, {n}) * 1.01 or rsi(5) < 30"],
        stop_atr=1.5, max_bars=10, params={"n": 30}),
    "either_way_squeeze": StrategySpec(
        name="Either way: squeeze breakout", category="either_way",
        long_entry=["recent(squeeze({n}, {lookback}), {window})", "close > prev(highest(high, {n}), 1)"],
        short_entry=["recent(squeeze({n}, {lookback}), {window})", "close < prev(lowest(low, {n}), 1)"],
        stop_atr="{stop}", target_atr="{target}", max_bars=30,
        params={"n": 20, "lookback": 120, "window": 10, "stop": 1.5, "target": 4.0},
        description="After volatility compresses, trade the breakout in whichever direction it comes."),
    "either_way_atr_breakout": StrategySpec(
        name="Either way: ATR volatility breakout", category="either_way",
        long_entry=["close > prev(close, 1) + {k} * prev(atr(14), 1)"],
        short_entry=["close < prev(close, 1) - {k} * prev(atr(14), 1)"],
        trail_atr="{trail}", max_bars=20, params={"k": 1.5, "trail": 2.5}),
    "pattern_reversal": StrategySpec(
        name="Pattern: bullish candles at oversold levels", category="pattern",
        long_entry=["bullish_engulfing or hammer or morning_star or piercing_line", "rsi(14) < {rsi_max}", "close > sma(200)"],
        long_exit=["rsi(14) > 60"],
        stop_atr=1.5, max_bars=10, params={"rsi_max": 45}),
    "rsi2_pullback": StrategySpec(
        name="Pullback: RSI-2 in an uptrend", category="pattern",
        long_entry=["close > sma(200)", "rsi(2) < {oversold}"],
        long_exit=["close > sma(5)"],
        stop_atr=3.0, max_bars=10, params={"oversold": 10}),
}


def templates(category: str | None = None) -> dict[str, StrategySpec]:
    return {k: v for k, v in TEMPLATES.items() if category is None or v.category == category}
