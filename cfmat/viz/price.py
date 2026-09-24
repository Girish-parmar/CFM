"""Price charts: candles or a line with overlays, trade markers, pattern markers, volume and indicator panels.

Bars are drawn at positions 0..n-1 so weekends and holidays leave no gaps;
the x-axis is labelled with dates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._common import ACCENT, DOWN, NEUTRAL, UP, bar_positions, date_ticks, figure


def candlestick(ax, ohlc: pd.DataFrame, width: float = 0.6) -> np.ndarray:
    """Draw candles on ``ax`` at positions 0..n-1; returns the positions."""
    x = np.arange(len(ohlc))
    o, h, lo, c = (ohlc[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    colours = np.where(c >= o, UP, DOWN)
    ax.vlines(x, lo, h, colors=colours, linewidth=0.8)
    body = np.maximum(np.abs(c - o), (h - lo) * 0.01 + 1e-12)       # dojis stay visible
    ax.bar(x, body, bottom=np.minimum(o, c), width=width, color=colours, edgecolor=colours, linewidth=0.5)
    return x


def _plot_overlay(ax, index: pd.Index, name: str, data, colour) -> None:
    frame = data.to_frame(name) if isinstance(data, pd.Series) else data
    for i, col in enumerate(frame.columns):
        values = frame[col].reindex(index).to_numpy(dtype=float)
        label = f"{name} {col}" if isinstance(data, pd.DataFrame) else name
        ax.plot(np.arange(len(index)), values, lw=1.0, color=colour if i == 0 else ACCENT[(i + 2) % len(ACCENT)],
                label=label, alpha=0.9)


def _plot_trades(ax, index: pd.Index, trades: pd.DataFrame) -> None:
    if trades is None or trades.empty:
        return
    t = trades.copy()
    side = t.get("direction", t.get("side", pd.Series("LONG", index=t.index))).astype(str).str.upper()
    long = side.isin(["LONG", "BUY"]).to_numpy()
    entry_x = bar_positions(index, t["entry_time"])
    ax.scatter(entry_x[long], t["entry_price"].to_numpy()[long], marker="^", s=45, color=UP, zorder=5,
               label="long entry")
    ax.scatter(entry_x[~long], t["entry_price"].to_numpy()[~long], marker="v", s=45, color=DOWN, zorder=5,
               label="short entry")
    closed = t["exit_time"].notna().to_numpy()
    if closed.any():
        exit_x = bar_positions(index, t.loc[closed, "exit_time"])
        ax.scatter(exit_x, t.loc[closed, "exit_price"], marker="x", s=35, color=NEUTRAL, zorder=5, label="exit")
        pnl = t.get("net_pnl", t.get("return", pd.Series(0.0, index=t.index)))[closed].to_numpy()
        for x0, y0, x1, y1, p in zip(entry_x[closed], t.loc[closed, "entry_price"], exit_x,
                                     t.loc[closed, "exit_price"], pnl, strict=True):
            ax.plot([x0, x1], [y0, y1], ls=":", lw=1.0, color=UP if p > 0 else DOWN)


def _plot_markers(ax, ohlc: pd.DataFrame, markers: dict[str, pd.Series]) -> None:
    pad = float((ohlc["high"] - ohlc["low"]).median()) * 0.8
    x = np.arange(len(ohlc))
    for i, (name, flags) in enumerate(markers.items()):
        s = flags.reindex(ohlc.index).fillna(0).astype(float).to_numpy()
        colour = ACCENT[i % len(ACCENT)]
        up, down = s > 0, s < 0
        if up.any():
            ax.scatter(x[up], ohlc["low"].to_numpy()[up] - pad, marker="^", s=25, color=colour, label=name, zorder=4)
        if down.any():
            ax.scatter(x[down], ohlc["high"].to_numpy()[down] + pad, marker="v", s=25, color=colour,
                       label=None if up.any() else name, zorder=4)


def price_chart(
    ohlc: pd.DataFrame,
    overlays: dict[str, pd.Series | pd.DataFrame] | None = None,
    trades: pd.DataFrame | None = None,
    markers: dict[str, pd.Series] | None = None,
    panels: dict[str, pd.Series | pd.DataFrame] | None = None,
    volume: bool = True,
    kind: str = "auto",
    last: int | None = None,
    title: str = "",
):
    """Price with everything a chart review needs; returns the figure.

    ``overlays``   lines on the price axis, e.g. ``{"SMA 50": sma50, "Bollinger": bands}``
    ``trades``     entry/exit markers from ``TradeJournal.round_trips`` or a backtest trade list
                   (``entry_time``, ``entry_price``, ``exit_time``, ``exit_price``, ``direction`` or ``side``)
    ``markers``    pattern flags: a bool or +1 Series marks below the low, −1 above the high
    ``panels``     indicators drawn in their own panel below, e.g. ``{"RSI 14": rsi}``
    ``kind``       ``candle``, ``line`` or ``auto`` (candles up to 250 bars)
    ``last``       show only the last N bars
    """
    bars = ohlc.iloc[-last:] if last else ohlc
    panels = panels or {}
    show_volume = volume and "volume" in bars
    heights = [4] + ([1] if show_volume else []) + [1.4] * len(panels)
    fig, axes = figure(len(heights), 1, figsize=(11, 3 + 1.6 * (len(heights) - 1) + 2), sharex=True,
                       gridspec_kw={"height_ratios": heights}, squeeze=False)
    axes = axes[:, 0]
    ax = axes[0]
    if kind == "candle" or (kind == "auto" and len(bars) <= 250):
        candlestick(ax, bars)
    else:
        ax.plot(np.arange(len(bars)), bars["close"].to_numpy(dtype=float), lw=1.0, color=NEUTRAL, label="close")
    for i, (name, data) in enumerate((overlays or {}).items()):
        _plot_overlay(ax, bars.index, name, data, ACCENT[i % len(ACCENT)])
    if trades is not None and len(trades):
        start, end = bars.index[0], bars.index[-1] + (bars.index[-1] - bars.index[-2] if len(bars) > 1
                                                      else pd.Timedelta(0))
        _plot_trades(ax, bars.index, trades[(trades["entry_time"] >= start) & (trades["entry_time"] <= end)])
    if markers:
        _plot_markers(ax, bars, markers)
    ax.set_title(title)
    _, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend(loc="upper left", fontsize=8, ncol=min(4, len(labels)))
    row = 1
    if show_volume:
        colours = np.where(bars["close"].to_numpy() >= bars["open"].to_numpy(), UP, DOWN) if "open" in bars else NEUTRAL
        axes[row].bar(np.arange(len(bars)), bars["volume"].to_numpy(dtype=float), color=colours, width=0.8, alpha=0.6)
        axes[row].set_ylabel("volume", fontsize=8)
        row += 1
    for name, data in panels.items():
        _plot_overlay(axes[row], bars.index, name, data, ACCENT[0])
        axes[row].set_ylabel(name, fontsize=8)
        if isinstance(data, pd.DataFrame):
            axes[row].legend(loc="upper left", fontsize=7)
        row += 1
    date_ticks(axes[-1], bars.index)
    return fig
