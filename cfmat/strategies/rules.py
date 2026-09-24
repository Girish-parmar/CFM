"""The rule language of the Strategy Creator (Module 12).

Rules such as ``"close > sma(200)"`` or ``"rsi(2) < 10 and bullish_engulfing"``
are parsed with Python's ``ast`` module; only whitelisted syntax (numbers,
price fields, registered functions and patterns, comparisons, arithmetic and
and/or/not) is evaluated. Nothing is passed to ``eval``.
"""

from __future__ import annotations

import ast
from collections.abc import Callable

import numpy as np
import pandas as pd

from ..analytics import indicators as ind
from ..analytics import patterns as pat

PRICE_FIELDS = ("open", "high", "low", "close", "volume")
FUNCTIONS: dict[str, Callable] = {}
MAX_RULE_LENGTH = 500


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
_ARITH = {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply, ast.Div: np.divide}


class Evaluator:
    """Evaluate rule strings against one set of bars, caching every sub-expression."""

    def __init__(self, bars: pd.DataFrame) -> None:
        self.bars = bars
        self._cache: dict[str, object] = {}

    def __call__(self, expr: str):
        if len(expr) > MAX_RULE_LENGTH:
            raise ValueError(f"rule longer than {MAX_RULE_LENGTH} characters; split it into several rules")
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
