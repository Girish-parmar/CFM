# %% [markdown]
# # Lab 24a — Capstone Template: Pre-registration to Paper-trading Report (M24)
#
# One script, one command, every capstone table:
#
#     python curriculum/m24-capstone-career/lab_24a_capstone_template.py
#
# 1. Pre-registration: the plan, written before testing, and checked.
# 2. Data with quality checks, split into research and an untouched hold-out.
# 3. The strategy as a Strategy Creator spec.
# 4. Walk-forward research with Indian costs, and the deflated Sharpe ratio charged for
#    the pre-registered number of trials.
# 5. One look at the hold-out.
# 6. Paper trading through the OMS and the broker's risk checks, with a journal and monitoring.
# 7. Tests: no look-ahead, risk limits, costs.
# 8. The report tables, and a capstone folder to copy (README, PREREGISTRATION, tests).
#
# Copy this file into your capstone repository as `src/pipeline.py` and edit `CONFIG`.
# It runs on synthetic data until you point `data_csv` at your own file.

# %%
import json
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd

from cfmat import data, studio, trading
from cfmat.analytics import metrics
from cfmat.analytics import performance as perf
from cfmat.automation import monitoring as mon
from cfmat.infra.paths import output_dir
from cfmat.microstructure.costs import IndianCostModel

pd.set_option("display.width", 150)

CONFIG = {
    "question": "Does a trend-following breakout, filtered by ADX, earn a positive risk-adjusted return "
                "after Indian costs on a liquid NSE stock?",
    "hypothesis": "The out-of-sample Sharpe ratio after costs is above zero, and the deflated Sharpe ratio "
                  "for the pre-registered number of trials exceeds 95%.",
    "instrument": "DEMOSTOCK (synthetic until data_csv is set)",
    "data_csv": None,                        # e.g. "data/TCS.NS.csv" from: python -m cfmat.data.fetch yahoo TCS.NS
    "research": ("2019-01-01", "2023-12-31"),
    "holdout": ("2024-01-01", "2024-12-31"),
    "template": "trend_up_breakout",
    "grid": {"entry": [20, 40, 55], "exit": [10, 20], "trend": [100, 200]},
    "trials_budget": 12,                     # every configuration you will ever try, counted before testing
    "walk_forward": {"train": 500, "test": 250},
    "segment": "equity_delivery",
    "slippage_bps": 5.0,
    "capital": 1_000_000.0,
    "primary_metric": "Walk-forward out-of-sample Sharpe after costs",
    "success": "OOS Sharpe > 0 and deflated Sharpe > 95%; hold-out Sharpe reported once, not optimised",
    "risk": {"max_position_value_pct": 120, "max_daily_loss_pct": 3.0, "max_orders_per_second": 5},
    "seed": 24,
}
OUT = output_dir() / "capstone_template"
REPORT: dict[str, pd.DataFrame] = {}

# %% [markdown]
# ## 1. Pre-registration
# Written before any test and committed to Git (the commit date is your evidence). The check
# below refuses to run the research if a field is missing, the hold-out overlaps the research
# period, or the grid holds more configurations than the trial budget.

# %%
PREREG_FIELDS = ["Question", "Hypothesis", "Instrument", "Research period", "Hold-out period", "Strategy",
                 "Parameter grid", "Trials budget", "Primary metric", "Success criterion", "Costs", "Risk limits"]


def preregistration_text(cfg: dict) -> str:
    """The PREREGISTRATION.md for this configuration."""
    risk = cfg["risk"]
    return "\n".join([
        "# Pre-registration", "",
        f"- Question: {cfg['question']}",
        f"- Hypothesis: {cfg['hypothesis']}",
        f"- Instrument: {cfg['instrument']}",
        f"- Research period: {cfg['research'][0]} to {cfg['research'][1]}",
        f"- Hold-out period: {cfg['holdout'][0]} to {cfg['holdout'][1]} (one look, after research is frozen)",
        f"- Strategy: Strategy Creator template `{cfg['template']}`",
        f"- Parameter grid: {json.dumps(cfg['grid'])}",
        f"- Trials budget: {cfg['trials_budget']}",
        f"- Primary metric: {cfg['primary_metric']}",
        f"- Success criterion: {cfg['success']}",
        f"- Costs: Indian {cfg['segment']} charges plus {cfg['slippage_bps']} bp slippage per side",
        f"- Risk limits: position ≤ {risk['max_position_value_pct']}% of capital, daily loss ≤ "
        f"{risk['max_daily_loss_pct']}%, ≤ {risk['max_orders_per_second']} orders per second",
    ]) + "\n"


def check_preregistration(text: str, cfg: dict) -> list[str]:
    """Problems that must be fixed before any test is run (an empty list means go)."""
    problems = [f"missing field: {f}" for f in PREREG_FIELDS
                if not any(line.startswith(f"- {f}:") and line.split(":", 1)[1].strip() for line in text.splitlines())]
    if pd.Timestamp(cfg["holdout"][0]) <= pd.Timestamp(cfg["research"][1]):
        problems.append("the hold-out starts before the research period ends")
    n_grid = len(studio.expand_grid(cfg["grid"]))
    if n_grid > cfg["trials_budget"]:
        problems.append(f"the grid has {n_grid} configurations but the trial budget is {cfg['trials_budget']}")
    return problems


prereg = preregistration_text(CONFIG)
problems = check_preregistration(prereg, CONFIG)
print(prereg)
print("Pre-registration check:", problems or "OK")
assert not problems, problems

# %% [markdown]
# ## 2. Data, quality checks and the split
# Synthetic daily bars unless `data_csv` points at a file (the same shape `cfmat-fetch` saves).
# The hold-out is cut off here and not touched again until section 5.

# %%
if CONFIG["data_csv"] and Path(CONFIG["data_csv"]).exists():
    bars = data.standardize_ohlcv(data.load_ohlcv_csv(CONFIG["data_csv"]))
else:
    n_days = len(pd.bdate_range(CONFIG["research"][0], CONFIG["holdout"][1]))
    bars = data.ohlcv(n_days, s0=1200, mu=0.12, sigma=0.24, seed=CONFIG["seed"], start=CONFIG["research"][0])
issues = data.ohlcv_problems(bars)
research = bars.loc[CONFIG["research"][0]:CONFIG["research"][1]]
holdout_end = bars.index[bars.index <= CONFIG["holdout"][1]][-1]
REPORT["data"] = pd.DataFrame({
    "rows": [len(research), len(bars.loc[CONFIG["holdout"][0]:holdout_end])],
    "from": [research.index[0].date(), bars.loc[CONFIG["holdout"][0]:].index[0].date()],
    "to": [research.index[-1].date(), holdout_end.date()],
}, index=["research", "hold-out"])
print(REPORT["data"].to_string())
print("Data quality:", issues or "no problems found")

# %% [markdown]
# ## 3. The strategy and its cost
# The rule engine charges costs per side; the Indian cost model gives the round trip for a
# typical order, so we pass half of it.

# %%
spec = studio.TEMPLATES[CONFIG["template"]]
price = float(research["close"].iloc[-1])
qty = int(CONFIG["capital"] // price)
round_trip = IndianCostModel().round_trip_bps(qty, price, CONFIG["segment"])
cost_bps = round_trip / 2
print(f"Template: {spec.name}\n  entry: {spec.long_entry}\n  exit : {spec.long_exit}")
print(f"Indian {CONFIG['segment']} charges: {round_trip:.1f} bp round trip → {cost_bps:.1f} bp per side, "
      f"plus {CONFIG['slippage_bps']} bp slippage")

# %% [markdown]
# ## 4. Walk-forward research and the deflated Sharpe ratio
# Each window re-optimises on the past and trades the next year. The in-sample best is
# reported only to show the gap; the pre-registered metric is the out-of-sample Sharpe, and
# the DSR charges it for every configuration tried.

# %%
wf = CONFIG["walk_forward"]
oos, chosen = studio.walk_forward(research, spec, CONFIG["grid"], train=wf["train"], test=wf["test"],
                                  workers=1, backend="serial", cost_bps=cost_bps, slippage_bps=CONFIG["slippage_bps"])
full_sweep = studio.sweep(research, spec, CONFIG["grid"], workers=1, backend="serial", cost_bps=cost_bps,
                          slippage_bps=CONFIG["slippage_bps"])
n_trials = CONFIG["trials_budget"]
trial_sr_var = float((full_sweep["sharpe"] / np.sqrt(252)).var())
dsr = metrics.deflated_sharpe_ratio(oos, n_trials, trial_sr_var)
REPORT["walk_forward"] = chosen
REPORT["research"] = pd.DataFrame({
    "in-sample best (full period)": {"sharpe": full_sweep["sharpe"].iloc[0], "cagr": full_sweep["cagr"].iloc[0]},
    "walk-forward out-of-sample": {"sharpe": metrics.sharpe_ratio(oos), "cagr": metrics.cagr(oos)},
}).T
REPORT["research"]["deflated_sharpe"] = [np.nan, dsr]
print(chosen.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
print("\n", REPORT["research"].round(3).to_string())

# %% [markdown]
# ## 5. One look at the hold-out
# Freeze the parameters the last walk-forward window chose and run them once on the
# hold-out. Whatever it shows is reported as it is; re-tuning after this look turns the
# hold-out into more in-sample data.

# %%
final_params = {k: chosen.iloc[-1][k] for k in CONFIG["grid"]}
final_params = {k: type(CONFIG["grid"][k][0])(v) for k, v in final_params.items()}
frozen = spec.resolve(**final_params)
through_holdout = bars.loc[:holdout_end]
held = studio.backtest(through_holdout, frozen, cost_bps=cost_bps, slippage_bps=CONFIG["slippage_bps"])
holdout_returns = held.returns.loc[CONFIG["holdout"][0]:]
benchmark = through_holdout["close"].pct_change().loc[CONFIG["holdout"][0]:]
REPORT["holdout"] = perf.tearsheet(holdout_returns, benchmark).loc[
    ["total_return", "sharpe", "max_drawdown", "volatility", "alpha", "beta"]]
print("Frozen parameters:", final_params)
print(REPORT["holdout"].round(3).to_string())

oos_sharpe = metrics.sharpe_ratio(oos)
VERDICT = {"OOS Sharpe > 0": oos_sharpe > 0, "deflated Sharpe > 95%": dsr > 0.95}
met = all(VERDICT.values())
print(f"\nPre-registered success criterion: {VERDICT} → {'MET' if met else 'NOT MET'}")
print("Report the result as it is: a clearly argued negative result is a pass in the capstone rubric;"
      " a positive result reached by moving the goalposts is not.")

# %% [markdown]
# ## 6. Paper trading: OMS, risk checks, journal and monitoring
# Replay the hold-out bar by bar. Each morning the OMS moves the book, through the broker's
# RMS, to the position decided by the previous close: new entries and signal exits happen at
# the open. The backtest also exits on intraday trailing stops; this daily paper loop has no
# intraday watch, so it takes those exits at the next open. The drift report measures the gap.
#
# A trap to avoid: moving to the backtest's *end-of-day* position at the open would trade on
# a stop that has not happened yet — look-ahead inside the paper loop itself.

# %%


def open_targets(result, days: pd.DatetimeIndex) -> pd.Series:
    """Position to hold from each open, using only what was known at the previous close."""
    entries = {t.entry_time: (1 if t.side == "long" else -1) for t in result.trades.itertuples()}
    open_exits = {t.exit_time for t in result.trades.itertuples() if t.reason in ("signal", "time", "reverse")}
    carried = result.position.shift(1).fillna(0)
    return pd.Series([entries[d] if d in entries else (0 if d in open_exits else int(carried.loc[d])) for d in days],
                     index=days)


risk = CONFIG["risk"]
open_px = float(through_holdout.loc[CONFIG["holdout"][0]:, "open"].iloc[0])
limits = trading.RiskLimits(max_order_qty=int(risk["max_position_value_pct"] / 100 * CONFIG["capital"] // open_px),
                            max_order_value=risk["max_position_value_pct"] / 100 * CONFIG["capital"] * 1.05,
                            max_position_qty=int(risk["max_position_value_pct"] / 100 * CONFIG["capital"] // open_px),
                            max_daily_loss=risk["max_daily_loss_pct"] / 100 * CONFIG["capital"],
                            max_orders_per_second=risk["max_orders_per_second"], price_band_pct=0.2)
broker = trading.PaperBroker(cash=CONFIG["capital"], risk=trading.RiskManager(limits),
                             slippage_bps=CONFIG["slippage_bps"], cost_model=IndianCostModel(),
                             segment=CONFIG["segment"])
oms = trading.OrderManager(broker, id_prefix="CAP")
journal = trading.TradeJournal()
broker.add_fill_listener(journal.record)
alerts = mon.AlertManager([mon.AlertRule("daily loss", "day_pnl_pct", "<", -risk["max_daily_loss_pct"], "critical")])
target = open_targets(held, through_holdout.loc[CONFIG["holdout"][0]:].index)
equity = []
for day, row in through_holdout.loc[CONFIG["holdout"][0]:].iterrows():
    broker.start_new_day()
    at_open = day + pd.Timedelta("09:15:00")
    oms.on_price("DEMOSTOCK", float(row["open"]), at_open)
    want = int(target.loc[day]) * int(CONFIG["capital"] // float(row["open"]))
    have = oms.positions.get("DEMOSTOCK", 0)
    if want != have:
        order = oms.submit("DEMOSTOCK", trading.BUY if want > have else trading.SELL, abs(want - have), timestamp=at_open)
        if order.status == "REJECTED":
            print(f"{day:%Y-%m-%d} order rejected: {order.reject_reason}")
    oms.on_price("DEMOSTOCK", float(row["close"]), day + pd.Timedelta("15:29:00"))
    alerts.evaluate({"day_pnl_pct": 100 * broker.day_pnl() / CONFIG["capital"]}, day + pd.Timedelta("15:30:00"))
    equity.append(broker.equity())
paper_returns = pd.Series(equity, index=target.index).pct_change().fillna(equity[0] / CONFIG["capital"] - 1)
drift = mon.drift_report(paper_returns, holdout_returns, alpha=0.01)
trips = journal.round_trips(include_open=True)
REPORT["paper"] = pd.DataFrame({
    "paper": {"total_return": (1 + paper_returns).prod() - 1, "sharpe": metrics.sharpe_ratio(paper_returns),
              "trades": len(trips), "charges": broker.total_charges},
    "backtest": {"total_return": (1 + holdout_returns).prod() - 1, "sharpe": metrics.sharpe_ratio(holdout_returns),
                 "trades": len(held.trades[held.trades["entry_time"] >= CONFIG["holdout"][0]]), "charges": np.nan},
})
print(REPORT["paper"].round(4).to_string())
print(f"Drift report: tracking {drift['tracking_bps_per_day']:.2f} bp/day (t = {drift['tracking_tstat']:.2f}), "
      f"drift flagged: {drift['drift']}; alerts raised: {len(alerts.history)}; "
      f"reconciliation breaks: {len(oms.reconcile())}")

# %% [markdown]
# ## 7. Tests: no look-ahead, risk limits, costs
# The same three checks run as `pytest` in the capstone folder (section 8).

# %%


def check_no_lookahead(bars: pd.DataFrame, spec, cuts: int = 5, seed: int = 0) -> bool:
    """Signals computed with data up to day t equal the full-history signals up to day t."""
    full = studio.signals(bars, spec)
    rng = np.random.default_rng(seed)
    for cut in rng.integers(300, len(bars) - 1, cuts):
        part = studio.signals(bars.iloc[:cut], spec)
        if not part.equals(full.iloc[:cut]):
            return False
    return True


def check_risk_limits(broker: trading.PaperBroker, limits: trading.RiskLimits) -> bool:
    """No filled order or position broke a limit, and an oversized order is refused."""
    filled_ok = all(o.qty <= limits.max_order_qty for o in broker.orders if o.status == "FILLED")
    position_ok = abs(broker.position("DEMOSTOCK")) <= limits.max_position_qty
    probe = broker.place_order(trading.Order("DEMOSTOCK", trading.BUY, limits.max_order_qty + 1))
    return filled_ok and position_ok and probe.status == "REJECTED"


def check_costs(bars: pd.DataFrame, spec, cost_bps: float, slippage_bps: float) -> bool:
    """Costs are charged: the same strategy earns less with them than without."""
    with_costs = studio.backtest(bars, spec, cost_bps=cost_bps, slippage_bps=slippage_bps).returns.sum()
    without = studio.backtest(bars, spec, cost_bps=0.0, slippage_bps=0.0).returns.sum()
    return cost_bps > 0 and with_costs < without


CHECKS = {
    "no_lookahead": check_no_lookahead(research, frozen),
    "risk_limits": check_risk_limits(broker, limits),
    "costs": check_costs(research, frozen, cost_bps, CONFIG["slippage_bps"]),
}
REPORT["checks"] = pd.DataFrame({"passed": CHECKS})
print(REPORT["checks"].to_string())
assert all(CHECKS.values()), CHECKS

# %% [markdown]
# ## 8. The report tables and a capstone folder to copy
# Every table above is written to `report/`; the folder also gets the pre-registration, a
# README saying how to reproduce the results, the RMS limits and a `pytest` file with the
# three checks. `RESULTS` is what the tests read.

# %%
RESULTS = {"report": REPORT, "checks": CHECKS, "dsr": dsr, "params": final_params, "verdict": VERDICT}
for sub in ("report", "tests", "paper_trading", "src", "data"):
    (OUT / sub).mkdir(parents=True, exist_ok=True)
for name, table in REPORT.items():
    table.to_csv(OUT / "report" / f"{name}.csv")
summary = "\n\n".join(f"## {name}\n\n```\n{table.to_string(float_format=lambda v: f'{v:.4g}')}\n```"
                      for name, table in REPORT.items())
summary += f"\n\n## Verdict\n\n{VERDICT} → {'MET' if met else 'NOT MET'}\n"
(OUT / "report" / "REPORT.md").write_text(f"# Capstone report\n\n{CONFIG['question']}\n\n{summary}\n", encoding="utf-8")
(OUT / "PREREGISTRATION.md").write_text(prereg, encoding="utf-8")
(OUT / "paper_trading" / "limits.json").write_text(json.dumps(limits.__dict__, default=list, indent=2), encoding="utf-8")
(OUT / "data" / "README.md").write_text("Scripts only. Licensed raw data is never committed.\n", encoding="utf-8")
(OUT / "README.md").write_text(textwrap.dedent(f"""\
    # Capstone: {CONFIG['instrument']}

    {CONFIG['question']}

    Reproduce every table: `python src/pipeline.py` (writes `report/`). Test: `pytest tests`.
    Pre-registration: `PREREGISTRATION.md`, committed before any test.
    """), encoding="utf-8")
(OUT / "tests" / "test_capstone.py").write_text(textwrap.dedent('''\
    """Capstone checks: run the whole pipeline once and test what it produced."""
    import runpy
    from pathlib import Path

    RESULTS = runpy.run_path(str(Path(__file__).resolve().parents[1] / "src" / "pipeline.py"))["RESULTS"]


    def test_no_lookahead():
        assert RESULTS["checks"]["no_lookahead"]


    def test_risk_limits():
        assert RESULTS["checks"]["risk_limits"]


    def test_costs():
        assert RESULTS["checks"]["costs"]
    '''), encoding="utf-8")
if "__file__" in globals():
    (OUT / "src" / "pipeline.py").write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
print("Capstone folder:", OUT)
for path in sorted(OUT.rglob("*")):
    if path.is_file():
        print("  ", path.relative_to(OUT))

# %% [markdown]
# ## What to change for your capstone
# 1. `CONFIG`: your question, instrument, dates, template or your own `StrategySpec`, grid and
#    trial budget — then commit `PREREGISTRATION.md` before running anything else.
# 2. `data_csv`: your data file; section 2 prints its quality problems — fix or explain each.
# 3. Keep section 5 to one run. If you change anything after looking, say so in the report
#    and count the extra trials.
# 4. Add a test for each claim your report makes.
