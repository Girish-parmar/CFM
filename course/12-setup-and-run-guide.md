# Setup and Run Guide

How to install Python, set up the course environment, run the labs in order and use the
`cfmat` library in your own work. Steps marked **MUST** are required for everyone; steps marked
**OPTIONAL** are only needed for the modules named next to them.

## At a glance

| # | Step | Required? | Time | Done when |
|---|---|---|---|---|
| 1 | Install Python 3.11 (or 3.12) | **MUST** | 10 min | `python --version` prints 3.11.x or 3.12.x |
| 2 | Install Git and VS Code | **MUST** Git · VS Code recommended | 10 min | `git --version` works |
| 3 | Get the course repository | **MUST** | 2 min | You are in the `CFM` folder |
| 4 | Create and activate a virtual environment | **MUST** | 2 min | Your prompt starts with `(.venv)` |
| 5 | Install the course library | **MUST** | 5–10 min | `pip install` finishes without errors |
| 6 | Run the environment check (Lab 00a) | **MUST** | 1 min | It prints `All required checks passed.` |
| 7 | Run the labs week by week, in the order below | **MUST** | in each week's clinics and self-study | Each lab runs and you have answered its exercises |
| 8 | Optional extras, services and tools | **OPTIONAL** | when a module needs them | See [Optional extras](#optional-extras) |

Everything runs offline after installation. Labs use synthetic or fictional data, so no market
data subscription or broker account is needed.

## What your computer needs

| | Minimum | Recommended |
|---|---|---|
| Operating system | Windows 10, macOS 12, Ubuntu 22.04 | Windows 11, macOS 14, Ubuntu 24.04 |
| Memory | 8 GB | 16 GB (the ML modules M19–M23) |
| Free disk | 3 GB | 8 GB (with the deep-learning extra) |
| Processor | Any 64-bit, 4 cores | 8 cores (parallel labs in M12 and M23 run faster) |
| Internet | Only to install and update | – |

## Step 1 — Install Python (MUST)

**Which version?**

| Python | Status | Use it? |
|---|---|---|
| **3.11** | Tested with pinned versions (the course's reference environment) | **Recommended** |
| 3.12 | Tested with pinned versions | Yes |
| 3.10 | Tested without pins | Yes, if you cannot upgrade; install with the 3.10 command in Step 5 |
| 3.13 and newer | Not tested yet | Not for this cohort |
| 3.9 and older | Not supported | No |

### Windows

1. Download the **Python 3.11** installer (64-bit) from [python.org/downloads/windows](https://www.python.org/downloads/windows/).
2. Run it. On the first screen tick **"Add python.exe to PATH"**, then **Install Now**.
3. Open a new **PowerShell** window and check:

   ```powershell
   py -3.11 --version        # Python 3.11.x
   ```

### macOS

Either the installer from [python.org/downloads/macos](https://www.python.org/downloads/macos/), or Homebrew:

```bash
brew install python@3.11
python3.11 --version      # Python 3.11.x
```

### Linux (Ubuntu)

```bash
# Ubuntu 24.04 ships Python 3.12, which is supported:
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
python3 --version

# Ubuntu 22.04 ships 3.10; to get 3.11:
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv
python3.11 --version
```

In the rest of this guide, `python` means the Python you just installed: use `py -3.11` on
Windows before the virtual environment exists, and `python3.11` (or `python3`) on macOS and Linux.
Once the virtual environment is active, plain `python` is correct everywhere.

## Step 2 — Install Git (MUST) and VS Code (recommended)

- **Git**: [git-scm.com/downloads](https://git-scm.com/downloads) (Windows and macOS), or `sudo apt install git` on Ubuntu. Check with `git --version`.
- **VS Code**: [code.visualstudio.com](https://code.visualstudio.com/), then install the **Python** and **Jupyter** extensions from the Extensions panel.

## Step 3 — Get the course repository (MUST)

The repository is private: the course team gives you access after enrolment.

```bash
git clone https://github.com/Girish-parmar/CFM.git
cd CFM
```

Every command from here on is run **from this `CFM` folder** (the repository root).

## Step 4 — Create and activate a virtual environment (MUST)

A virtual environment keeps the course's packages separate from everything else on your computer.
Create it once; activate it every time you open a new terminal.

| | Create (once) | Activate (every new terminal) |
|---|---|---|
| Windows PowerShell | `py -3.11 -m venv .venv` | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `py -3.11 -m venv .venv` | `.venv\Scripts\activate.bat` |
| macOS / Linux | `python3.11 -m venv .venv` | `source .venv/bin/activate` |

When it is active, your prompt starts with `(.venv)`. Then upgrade pip:

```bash
python -m pip install --upgrade pip
```

If PowerShell refuses to run `Activate.ps1`, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.
To leave the environment, type `deactivate`.

## Step 5 — Install the course library (MUST)

With the environment active, from the repository root:

```bash
pip install -r requirements.txt
```

This installs the `cfmat` library in editable mode together with the tested versions of numpy,
pandas, scipy, scikit-learn, statsmodels and matplotlib, the developer tools (pytest, ruff,
pre-commit, PyYAML) and the boosting extra (XGBoost, LightGBM, Optuna) used in M23.

| Your situation | Command instead |
|---|---|
| Python 3.10 (the pins need 3.11+) | `pip install -e ".[dev,boost]"` |
| Short on disk or bandwidth: core only, add extras later | `pip install -c constraints.txt -e ".[dev]"` |
| macOS, before the boosting extra | `brew install libomp` (XGBoost and LightGBM need it) |

"Editable" (`-e`) means Python uses the code in this folder directly: when you `git pull` a
course update, the library updates with it.

## Step 6 — Check the installation (MUST)

```bash
python curriculum/m00-prework/lab_00a_environment_check.py
```

Every required line must say `OK` and the last line must read `All required checks passed.`
Optional packages you have not installed show `--` and "fine for now". The lab also saves your
first chart to `build/lab-output/lab00a_first_chart.png`. Paste the output into the pre-work form.

Optional, but a good habit before you start: run the unit tests (about a minute) and the manifest check.

```bash
python -m pytest -m "not lab" -q            # all unit tests should pass
python tools/route_manager.py check         # the course manifest is consistent
```

## Step 7 — Run the labs in order (MUST)

Every learner takes every module, so **every released lab is required**, in the order below.
The work (running it cell by cell, reading the output, answering the exercises) happens in the
week's lab clinics and self-study, as the module guide lays out; the runtime column is only how
long the script itself takes on a laptop. The *Optional extras* column names the pip extra that
unlocks an extra section or exercise: without it, the lab still runs and skips that part with a
message.

<!-- BEGIN GENERATED: run-order -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| # | Week | Lab | Module | What it does | Runtime | Optional extras |
|---|---|---|---|---|---|---|
| 1 | −3 to 0 | [00a](../curriculum/m00-prework/lab_00a_environment_check.py) | M00 | Environment check and first chart | ~5 s | – |
| 2 | 1–2 | [01a](../curriculum/m01-financial-markets/lab_01a_markets_instruments.py) | M01 | Notional, margin, fair value, corporate actions, T+1 | ~5 s | – |
| 3 | 5–6 | [03a](../curriculum/m03-python-for-finance/lab_03a_python_for_finance.py) | M03 | Returns, resampling, rolling volatility, drawdowns | ~5 s | `data` |
| 4 | 7–8 | [04a](../curriculum/m04-statistics-time-series/lab_04a_statistics_time_series.py) | M04 | Fat tails, ADF, Ljung–Box, CAPM, cointegration, bootstrap Sharpe | ~10 s | – |
| 5 | 9–10 | [05a](../curriculum/m05-data-engineering-databases/lab_05a_market_database.py) | M05 | SQLite schema, window functions, query plans, data-quality checks | ~5 s | – |
| 6 | 12–13 | [06a](../curriculum/m06-technical-analysis-patterns/lab_06a_indicators_patterns.py) | M06 | Indicator dashboard, HAC event studies, 20 patterns with FDR control | ~15 s | – |
| 7 | 14 | [07a](../curriculum/m07-fundamental-factor-investing/lab_07a_factors_quantamental.py) | M07 | IC, winsorising, sector neutrality, composites, quintile spreads | ~15 s | – |
| 8 | 15–17 | [08a](../curriculum/m08-derivatives-pricing-greeks/lab_08a_options_pricing_greeks.py) | M08 | Option chain and Greeks, IV smile, binomial, payoffs, delta hedging | ~10 s | – |
| 9 | 18–19 | [09b](../curriculum/m09-fno-strategies-advanced-greeks/lab_09b_futures_options_structures.py) | M09 | Futures curve, cash-and-carry, seven option structures in parallel | ~10 s | – |
| 10 | 20–22 | [10a](../curriculum/m10-trading-strategies/lab_10a_trading_strategies.py) | M10 | Trend, momentum, mean reversion, cross-sectional momentum, pairs | ~10 s | – |
| 11 | 20–22 | [10b](../curriculum/m10-trading-strategies/lab_10b_momentum_volatility.py) | M10 | Volatility estimators vs truth, cones and regimes, momentum scores, TSMOM with a vol target | ~5 s | – |
| 12 | 23–24 | [11a](../curriculum/m11-backtesting-research/lab_11a_backtesting_costs_walk_forward.py) | M11 | Indian costs, grid search vs walk-forward, deflated Sharpe, event engine | ~20 s | – |
| 13 | 23–24 | [11b](../curriculum/m11-backtesting-research/lab_11b_analysis_tearsheet.py) | M11 | Tearsheet vs benchmark, drawdown anatomy, rolling and distribution views, CAPM, RS and rotation | ~5 s | – |
| 14 | 25–26 | [12a](../curriculum/m12-strategy-studio/lab_12a_screener_instrument_selection.py) | M12 | Parallel screener, regime labels, ranking, pattern scan, shortlist | ~10 s | – |
| 15 | 25–26 | [12b](../curriculum/m12-strategy-studio/lab_12b_strategy_creator_parallel.py) | M12 | Strategy library and creator, sweeps (serial/thread/process), walk-forward | ~20 s | – |
| 16 | 25–26 | [12c](../curriculum/m12-strategy-studio/lab_12c_fno_signals_and_filters.py) | M12 | Trend template on futures; regime filters for option structures | ~10 s | – |
| 17 | 28–29 | [13a](../curriculum/m13-risk-position-sizing/lab_13a_risk_sizing_stress.py) | M13 | VaR/ES, Kupiec, GARCH VaR, sizing, risk of ruin, stress tests | ~15 s | – |
| 18 | 30–31 | [14a](../curriculum/m14-portfolio-management/lab_14a_portfolio_construction.py) | M14 | Optimisers out of sample, Ledoit–Wolf, frontier, strategy sleeves | ~15 s | – |
| 19 | 32–33 | [15a](../curriculum/m15-microstructure-execution/lab_15a_order_book_execution.py) | M15 | Order book, TWAP/VWAP/POV, Almgren–Chriss, impact, shortfall | ~5 s | – |
| 20 | 34 | [16a](../curriculum/m16-market-data-handling/lab_16a_market_data_handler.py) | M16 | Tick validation with scored detectors, time/volume/dollar bars, instrument master, continuous futures, storage and replay | ~10 s | – |
| 21 | 35–36 | [17a](../curriculum/m17-trading-platform-compliance/lab_17a_oms_rms_paper_trading.py) | M17 | Paper broker, RMS rejects, throttle, kill switch, trade journal | ~5 s | – |
| 22 | 35–36 | [17b](../curriculum/m17-trading-platform-compliance/lab_17b_order_management_journal.py) | M17 | OMS states, stops, IOC/DAY, bracket and OCO, reconciliation; journal review with R and MAE/MFE | ~5 s | – |
| 23 | 37–38 | [18a](../curriculum/m18-monitoring-automation/lab_18a_n8n_signal_service.py) | M18 | Signal service endpoints used by the n8n workflows | ~5 s | – |
| 24 | 37–38 | [18b](../curriculum/m18-monitoring-automation/lab_18b_live_monitoring.py) | M18 | Heartbeats and stale feeds, live-vs-backtest drift, P&L attribution, alert rules to a webhook | ~5 s | – |
| 25 | 39–40 | [19a](../curriculum/m19-machine-learning/lab_19a_machine_learning.py) | M19 | Features, triple barrier, leakage vs purged CV, walk-forward trading | ~30 s | – |
| 26 | 41 | [20a](../curriculum/m20-deep-learning/lab_20a_deep_learning.py) | M20 | Sliding windows, MLP vs logistic on linear and nonlinear signals | ~15 s | `dl` |
| 27 | 42 | [21a](../curriculum/m21-reinforcement-learning/lab_21a_reinforcement_learning.py) | M21 | Q-learning policy, rule baseline, costs in the reward, seed spread | ~30 s | – |
| 28 | 43–44 | [22a](../curriculum/m22-nlp-news-llm-rag/lab_22a_sentiment_rag.py) | M22 | Lexicon and TF-IDF sentiment, RAG with relevance guard, optional Claude | ~5 s | `llm` |
| 29 | 45–46 | [23a](../curriculum/m23-advanced-strategies-hpo/lab_23a_boosting_hpo.py) | M23 | HGB/XGBoost/LightGBM, random search, Optuna, nested walk-forward, PBO | ~60 s | `boost` |
| 30 | 45–46 | [23b](../curriculum/m23-advanced-strategies-hpo/lab_23b_regimes_kalman_garch.py) | M23 | Markov regimes, GARCH volatility targeting, Kalman-filter pairs | ~10 s | – |
| 31 | 45–46 | [23c](../curriculum/m23-advanced-strategies-hpo/lab_23c_meta_labeling_ensembles.py) | M23 | Meta-labelling, bet sizing, multi-strategy allocation | ~10 s | – |
| 32 | 45–46 | [23d](../curriculum/m23-advanced-strategies-hpo/lab_23d_segment_optimisation.py) | M23 | Day/month/expiry/regime/pattern segments, FDR, per-segment walk-forward | ~60 s | – |
| 33 | 48–52 | [24a](../curriculum/m24-capstone-career/lab_24a_capstone_template.py) | M24 | Pre-registration to paper-trading report: a reproducible capstone skeleton | ~5 s | – |

Planned, not yet released: 02a, 09a, 22b.
<!-- END GENERATED: run-order -->

### How to run a lab

From the repository root, with the environment active:

```bash
python curriculum/m10-trading-strategies/lab_10b_momentum_volatility.py
```

Or work through it cell by cell. Labs are plain Python files with `# %%` cell markers (Jupytext
"percent" format):

| Way | How | Best for |
|---|---|---|
| Script | `python curriculum/.../lab_NNx_*.py` | Checking that the whole lab runs; submission |
| VS Code cells | Open the file and click **Run Cell** above each `# %%` (first time: `pip install ipykernel`) | Working through a lab step by step |
| Jupyter notebook | `pip install jupyterlab jupytext`, then `jupyter lab` and right-click the file → **Open With → Notebook** | If you prefer notebooks |

Charts are saved as PNG files in `build/lab-output/` (set `CFMAT_OUTPUT_DIR` to save
elsewhere); the script prints each file's path. Open them from VS Code's file explorer.

### What to run this week

```bash
python tools/route_manager.py week 23                     # the module, theme and session timetable for week 23
python tools/route_manager.py route systematic-trader     # your learning route across all 25 modules
python tools/route_manager.py labs                        # every lab file, in course order
```

The week view links the module guide, whose weekly plan says which lab sections each clinic covers.

## Optional extras

Install an extra only when you reach the module that needs it. With the environment active:

| Extra | Command | Unlocks | Module |
|---|---|---|---|
| `boost` | `pip install -e ".[boost]"` (already in `requirements.txt`) | XGBoost, LightGBM and Optuna sections of Lab 23a | M23 |
| `data` | `pip install -e ".[data]"` | Real prices from Yahoo Finance (`data.download_prices("TCS.NS")`); `USE_REAL_DATA` in Lab 03a; Parquet tick storage in Lab 16a (pyarrow); real-data exercises | M03 onwards |
| `alpaca` | `pip install -e ".[alpaca]"` and set `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` | US stock bars from Alpaca (`data.alpaca_bars`, `cfmat-fetch alpaca`); no NSE | Real-data exercises, M16 |
| `ibkr` | `pip install -e ".[ibkr]"`; TWS or IB Gateway running | Bars from Interactive Brokers, including NSE (`data.ibkr_bars`, `cfmat-fetch ibkr`) | Real-data exercises, M16–M17 |
| `llm` | `pip install -e ".[llm]"` and set `ANTHROPIC_API_KEY` | The Claude answer step in Lab 22a (the retrieval pipeline runs without it) | M22 |
| `dl` | `pip install -e ".[dl]"` (CPU only, much smaller on Windows/Linux: `pip install torch --index-url https://download.pytorch.org/whl/cpu`) | The PyTorch LSTM exercise in Lab 20a | M20 |

**API keys.** Set them as environment variables, never in code or notebooks:

```bash
export ANTHROPIC_API_KEY="..."            # macOS / Linux (current terminal)
$env:ANTHROPIC_API_KEY = "..."            # Windows PowerShell (current terminal)
export ALPACA_API_KEY="..." ALPACA_SECRET_KEY="..."     # Alpaca paper-account keys
```

### Fetching real market data

One command downloads bars, checks them and saves `data/<SYMBOL>.csv` in the standard shape
(`date, open, high, low, close, volume`), which every lab function, `data.load_ohlcv_csv` and the
signal service read directly:

```bash
python -m cfmat.data.fetch yahoo TCS.NS INFY.NS ^NSEI --start 2018-01-01          # free, daily, NSE via Yahoo
python -m cfmat.data.fetch alpaca AAPL MSFT --start 2020-01-01 --timeframe 1Day   # US stocks, Alpaca keys
python -m cfmat.data.fetch ibkr RELIANCE TCS --exchange NSE --currency INR --duration "5 Y"
python -m cfmat.data.fetch ibkr NIFTY50 --sec-type IND --bar-size "5 mins" --duration "5 D" --chunks 4
```

(`cfmat-fetch` is the same command.) Each line prints the rows and date range saved and any
data-quality warnings: prices at or below zero, highs below lows, closes outside the day's range,
duplicate timestamps, or one-bar moves over 25%, which usually mean an unadjusted split. In Python:

```python
from cfmat import data

aapl = data.alpaca_bars("AAPL", start="2020-01-01", timeframe="1Day")        # US, split/dividend-adjusted
reliance = data.ibkr_bars("RELIANCE", exchange="NSE", currency="INR", duration="2 Y")
print(data.ohlcv_problems(reliance) or "looks clean")
```

| Source | Markets | What you need | Watch out for |
|---|---|---|---|
| Yahoo Finance | NSE (`.NS`), BSE (`.BO`), US, indices | Nothing (the `data` extra) | Daily only; free data for learning, not for commercial use |
| Alpaca | US stocks only | Free paper account; API keys in the environment | Free plan: IEX-only real-time; the newest 15 minutes of SIP data are delayed (the fetcher ends 16 minutes ago) |
| Interactive Brokers | NSE (IBKR India account), US, global | TWS or IB Gateway running with API access (paper port 7497 or 4002) and a live market-data subscription for the exchange | About 60 historical requests per 10 minutes (`--chunks` paces itself); confirm IBKR's symbol for each contract in TWS |

The data from all three is licensed for personal use. It stays in `data/`, which git ignores:
do not commit or share it. The course's Indian cost model does not apply to US stocks.

### Optional services and tools

| What | When | How |
|---|---|---|
| Signal service for n8n | M18 | `python -m cfmat.automation.signal_service --port 8000` (or `make serve`); then follow [`n8n/README.md`](../n8n/README.md) to run n8n with Docker or `npx n8n` and import the workflows |
| Your own price files | Any real-data exercise | Save `data/<SYMBOL>.csv` with columns `date, open, high, low, close, volume`; load with `data.load_ohlcv_csv("data/TCS.csv")`. The folder is git-ignored: market data is usually licensed |
| All labs as a smoke test | Before submitting a capstone, or after an update | `python -m pytest -m lab` (about 4 minutes) |
| Quality checks | If you change library code | `make check` (lint, tests, manifest, generated docs); see [CONTRIBUTING](../CONTRIBUTING.md) |

## Using the library in your own code

Everything the labs use is in the `cfmat` package; the [API reference](../docs/reference/README.md)
lists every function. A first script (save it anywhere and run it with the environment active):

```python
from cfmat import data, trading, viz
from cfmat.analytics import momentum, performance, volatility

bars = data.ohlcv(500, seed=1)                  # synthetic OHLCV; or data.load_ohlcv_csv("data/TCS.csv")
returns = bars["close"].pct_change().dropna()

print(performance.tearsheet(returns).round(3))                  # returns, risk, drawdown, tails
print("Yang–Zhang volatility:", round(volatility.yang_zhang(bars, 21).iloc[-1], 3))
print("12-1 momentum:", round(momentum.momentum(bars["close"]).iloc[-1], 3))
print(viz.savefig(viz.price_chart(bars, last=120), "my_first_chart"))   # → build/lab-output/

broker = trading.PaperBroker(cash=1_000_000)                   # paper trading only
oms = trading.OrderManager(broker)
oms.on_price("DEMO", 100.0)
oms.submit_bracket("DEMO", trading.BUY, 50, stop_loss=97.0, take_profit=106.0)
oms.on_price("DEMO", 106.5)                                    # the target fills, the stop is cancelled
print(oms.orders_frame()[["role", "status", "qty", "filled_qty"]])
```

| I want to… | Use |
|---|---|
| Get data | `cfmat.data` (synthetic generators, CSV and Yahoo loaders) |
| Compute indicators, patterns, momentum, volatility | `cfmat.analytics.indicators`, `.patterns`, `.momentum`, `.volatility` |
| Evaluate a strategy | `cfmat.analytics.performance` (tearsheet), `.relative` (alpha, beta), `.metrics` |
| Build and backtest rules | `cfmat.studio` (Strategy Creator), `cfmat.backtesting` |
| Screen instruments | `cfmat.research.screener` |
| Size positions and measure risk | `cfmat.portfolio.risk`, `cfmat.portfolio.construction` |
| Paper-trade with orders and a journal | `cfmat.trading` (`OrderManager`, `PaperBroker`, `TradeJournal`) |
| Chart anything | `cfmat.viz` |

## Your weekly routine

```bash
cd CFM
source .venv/bin/activate                 # Windows: .venv\Scripts\Activate.ps1
git pull                                  # get this week's updates
pip install -r requirements.txt           # only when requirements.txt or constraints.txt changed
python tools/route_manager.py week 23     # this week's module and timetable
python curriculum/.../lab_NNx_*.py        # run the week's lab, then do its exercises
```

Keep your own work (exercise answers, mini-projects, capstone) on your own branch or in your own
repository, not in the course files, so `git pull` never conflicts with it.

## Windows without `make`

`make` targets are shortcuts for these commands, which work everywhere:

| `make …` | Command |
|---|---|
| `make install` | `python -m pip install -r requirements.txt` |
| `make test` | `python -m pytest -m "not lab"` |
| `make labs` | `python -m pytest -m lab` |
| `make course` | `python tools/route_manager.py check` |
| `make lint` | `python -m ruff check .` |
| `make docs` | `python tools/route_manager.py render` then `python tools/gen_api_docs.py` |
| `make serve` | `python -m cfmat.automation.signal_service --port 8000` |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `python` or `py` is not recognised | Python is not on PATH | Re-run the installer and tick "Add python.exe to PATH", then open a new terminal |
| `ModuleNotFoundError: No module named 'cfmat'` | The environment is not active, or Step 5 was skipped | Activate `.venv` (prompt shows `(.venv)`), then `pip install -r requirements.txt` |
| VS Code runs a different Python | Wrong interpreter selected | `Ctrl/Cmd+Shift+P` → **Python: Select Interpreter** → the one in `.venv` |
| `Activate.ps1 cannot be loaded` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip install -r requirements.txt` fails on Python 3.10 | The pinned versions need 3.11+ | Use `pip install -e ".[dev,boost]"`, or install Python 3.11 |
| XGBoost or LightGBM fails to import on macOS | OpenMP runtime missing | `brew install libomp` |
| SSL or proxy errors during `pip install` | Corporate network | Ask IT for the proxy settings, or install from a home network |
| No chart window appears | By design: charts are saved to files | Open the PNG path the lab prints (in `build/lab-output/`) |
| A lab is very slow, or the fan runs flat out | Many threads competing | Close other heavy programs; set `OMP_NUM_THREADS=2` before running |
| `ANTHROPIC_API_KEY not set — skipping the LLM step` | The optional key is not set | Fine: the rest of Lab 22a ran. Set the key only if you want the Claude step |

Still stuck? Post the full command and the complete error message on the course forum (LMS) or
Slack, or bring it to the Wednesday office hours.

## Updating and removing

- **Update:** `git pull`, then `pip install -r requirements.txt` if the requirement files changed.
- **Start fresh:** delete the `.venv` folder and repeat Steps 4–6.
- **Remove everything:** delete the `CFM` folder; nothing is installed outside it except Python and Git.
