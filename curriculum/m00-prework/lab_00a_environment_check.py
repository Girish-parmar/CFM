# %% [markdown]
# # Lab 00a — Environment Check and Your First Market Chart (M00)
#
# Run this before Week 1. It checks that Python, the scientific stack and the course
# library are installed, then builds a first chart from synthetic prices. The full
# installation steps are in course/12-setup-and-run-guide.md.
#
#     pip install -e ".[dev]"          # from the repository root
#     python curriculum/m00-prework/lab_00a_environment_check.py
#
# Every line should print OK. Paste the output into the pre-work form.

# %%
import importlib
import importlib.util
import platform
import sys

REQUIRED = {"numpy": "1.26", "pandas": "2.2", "scipy": "1.11", "sklearn": "1.4", "statsmodels": "0.14",
            "matplotlib": "3.8"}
OPTIONAL = {"xgboost": "M23 boosting", "lightgbm": "M23 boosting", "optuna": "M23 tuning",
            "yfinance": "real prices", "anthropic": "M22 LLM step", "torch": "M20 LSTM exercise"}


def version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split(".")[:2] if p.isdigit())


print(f"Python {platform.python_version()} on {platform.system()} {platform.machine()}")
ok = sys.version_info >= (3, 10)
print(f"{'OK ' if ok else 'FAIL'} Python 3.10 or newer")
problems = 0 if ok else 1
for name, minimum in REQUIRED.items():
    try:
        module = importlib.import_module(name)
        good = version_tuple(module.__version__) >= version_tuple(minimum)
        print(f"{'OK ' if good else 'OLD'} {name} {module.__version__} (need {minimum}+)")
        problems += 0 if good else 1
    except ImportError:
        print(f"FAIL {name} is not installed")
        problems += 1
for name, used_for in OPTIONAL.items():
    found = importlib.util.find_spec(name) is not None
    print(f"{'OK ' if found else '-- '} optional {name:<10} ({used_for}){'' if found else ': not installed, fine for now'}")

# %% [markdown]
# ## The course library

# %%
import cfmat
from cfmat import data
from cfmat.analytics import metrics
from cfmat.infra.paths import SAMPLE_DATA_DIR, output_dir
from cfmat.infra.plotting import plt, savefig

print(f"OK  cfmat {cfmat.__version__} from {cfmat.__file__}")
print(f"{'OK ' if (SAMPLE_DATA_DIR / 'sample_headlines.csv').exists() else 'FAIL'} sample data in {SAMPLE_DATA_DIR}")
print(f"OK  charts will be saved in {output_dir()}")

# %% [markdown]
# ## Your first chart: price and drawdown

# %%
close = data.gbm_prices(756, mu=0.10, sigma=0.20, seed=1)
returns = metrics.simple_returns(close)
equity = metrics.equity_curve(returns)
summary = metrics.performance_summary(returns)
print(f"CAGR {summary['cagr']:.1%}, volatility {summary['volatility']:.1%}, Sharpe {summary['sharpe']:.2f}, "
      f"max drawdown {summary['max_drawdown']:.1%}")
print("This series was generated with a +10% a year drift. Three years of 20% volatility can still lose money:")
print("remember that the next time a 3-year backtest looks convincing.")

fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
close.plot(ax=axes[0], title="Synthetic price (geometric Brownian motion)")
metrics.drawdown_series(equity).plot(ax=axes[1], title="Drawdown", color="tab:red")
print("Chart saved to", savefig(fig, "lab00a_first_chart"))
print("\nAll required checks passed." if problems == 0 else f"\n{problems} problem(s): fix them before Week 1.")
