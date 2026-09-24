# Labs

One lab per technical module (three for the advanced Module 16). Each lab is a Python script in Jupytext "percent" format: run it as a script, or open it as a notebook in JupyterLab/VS Code (`pip install jupytext`, then *Open With → Notebook*). Charts are saved to `labs/output/`.

| Lab | Module | Topics | Runtime* |
|---|---|---|---|
| [lab01_markets_instruments.py](lab01_markets_instruments.py) | M01 | Notional, margin, leverage, futures fair value, corporate actions, T+1 | < 5 s |
| [lab02_python_for_finance.py](lab02_python_for_finance.py) | M02 | Returns, resampling, monthly table, rolling volatility, drawdowns | < 5 s |
| [lab03_quant_statistics.py](lab03_quant_statistics.py) | M03 | Fat tails, ADF, Ljung–Box, CAPM, cointegration, bootstrap Sharpe | ~10 s |
| [lab04_market_database.py](lab04_market_database.py) | M04 | SQLite schema, window functions, query plans, data-quality checks | < 5 s |
| [lab05_technical_fundamental.py](lab05_technical_fundamental.py) | M05 | Indicators, event study, multi-factor screen | < 5 s |
| [lab06_options_derivatives.py](lab06_options_derivatives.py) | M06 | Option chain and Greeks, IV smile, binomial, payoffs, delta hedging | ~10 s |
| [lab07_trading_strategies.py](lab07_trading_strategies.py) | M07 | Trend, momentum, mean reversion, cross-sectional momentum, pairs | ~5 s |
| [lab08_backtesting_research.py](lab08_backtesting_research.py) | M08 | Indian costs, grid search vs walk-forward, Deflated Sharpe, event engine | ~15 s |
| [lab09_risk_portfolio.py](lab09_risk_portfolio.py) | M09 | VaR/ES and VaR backtest, sizing, portfolio optimisers, stress tests | ~10 s |
| [lab10_execution_microstructure.py](lab10_execution_microstructure.py) | M10 | Order book, TWAP/VWAP/POV, Almgren–Chriss, impact, shortfall | < 5 s |
| [lab11_paper_trading_rms.py](lab11_paper_trading_rms.py) | M11 | Paper broker, RMS rejects, throttle, kill switch, trade journal | < 5 s |
| [lab12_machine_learning.py](lab12_machine_learning.py) | M12 | Features, triple barrier, leakage vs purged CV, walk-forward trading | ~30 s |
| [lab13_deep_learning_rl.py](lab13_deep_learning_rl.py) | M13 | Sliding windows, MLP vs logistic, Q-learning agent | < 5 s |
| [lab14_nlp_llm_rag.py](lab14_nlp_llm_rag.py) | M14 | Lexicon sentiment, TF-IDF classifier, RAG with relevance guard, optional Claude | < 5 s |
| [lab15_n8n_automation.py](lab15_n8n_automation.py) | M15 | Signal service endpoints used by the n8n workflows | < 5 s |
| [lab16_boosting_hyperparameter_tuning.py](lab16_boosting_hyperparameter_tuning.py) | M16 | HGB/XGBoost/LightGBM, random search, Optuna, nested walk-forward, Deflated Sharpe, PBO | ~60 s |
| [lab17_regimes_kalman_garch.py](lab17_regimes_kalman_garch.py) | M16 | Markov regimes (filtered vs smoothed), GARCH vol targeting, Kalman-filter pairs | < 5 s |
| [lab18_meta_labeling_ensembles.py](lab18_meta_labeling_ensembles.py) | M16 | Meta-labelling, bet sizing, multi-strategy allocation (inverse-vol, risk parity, HRP) | < 5 s |

*On a typical laptop.

## Running

```bash
pip install -e ".[dev,boost]"
python labs/lab07_trading_strategies.py
pytest tests/test_labs.py        # runs every lab as a smoke test
```

Every lab runs offline on synthetic or fictional data. Lab 16 uses XGBoost, LightGBM and Optuna when installed (`pip install xgboost lightgbm optuna`, or `xgboost-cpu` for a small CPU-only build) and skips those sections otherwise. Lab 2 can switch to real data (`USE_REAL_DATA = True`, needs `pip install yfinance`). Lab 14's LLM step runs only when `ANTHROPIC_API_KEY` is set (`pip install anthropic`); it uses `claude-opus-5` unless `CFMAT_CLAUDE_MODEL` names another model.

Each lab ends with exercises. Submit your work as a pull request to your cohort repository.
