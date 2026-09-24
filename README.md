# Certificate in Financial Market and Algorithmic Trading (CFMAT)

A 10-month, practitioner-led program that takes learners from how markets work to building, testing, risk-managing and automating trading strategies with Python, SQL databases, machine learning, deep learning, NLP/RAG and n8n.

| | |
|---|---|
| **Program fee** | ₹4,25,000 + 18% GST = **₹5,01,500** (pay-in-full, instalment, EMI and scholarship options) |
| **Duration** | 40 weeks + 4 weeks of pre-work · January and July intakes |
| **Format** | Hybrid: live weekend classes, weekday lab clinics, two 3-day in-person bootcamps |
| **Guided learning** | 460 hours (310 module + 20 review/exam + 48 bootcamp + 70 capstone + 12 mentoring) |
| **Cohort** | 30 target, 40 maximum; 1 TA per 15 learners; 1 mentor per 5 learners |
| **Outcome** | Certificate (Distinction / Merit / Pass) with verifiable credential ID, a GitHub portfolio, and a pre-registered capstone with 4 weeks of live paper trading |

> **Education only.** Nothing in this repository is investment advice or a recommendation. All data is synthetic or fictional. Trading involves substantial risk of loss. See [docs/09-compliance-and-disclaimers.md](docs/09-compliance-and-disclaimers.md).

## Program documents

| Document | Contents |
|---|---|
| [01 Program overview](docs/01-program-overview.md) | Purpose, audience, learning outcomes, structure, value |
| [02 Curriculum](docs/02-curriculum.md) | All 16 modules with hours, summaries and texts |
| [03 Fee structure and value](docs/03-fee-structure-and-value.md) | ₹5 lakh pricing, payment plans, scholarships, refunds, what is included, unit economics |
| [04 Assessment and certification](docs/04-assessment-and-certification.md) | Weights, capstone rubric, grade bands, integrity and AI-use policy |
| [05 Capstone projects](docs/05-capstone-projects.md) | Timeline, 10 project options, technical requirements, jury |
| [06 Academic calendar](docs/06-academic-calendar.md) | Week-by-week plan for all 40 weeks |
| [07 Faculty and infrastructure](docs/07-faculty-and-infrastructure.md) | Faculty model, lab stack, data, compute, support |
| [08 Admissions and careers](docs/08-admissions-and-careers.md) | Eligibility, selection, sample test, interview rubric, career services |
| [09 Compliance and disclaimers](docs/09-compliance-and-disclaimers.md) | SEBI education and algo rules, risk disclosure, marketing, data, privacy, GST |

## Modules

| Term | Modules |
|---|---|
| 1 · Market Foundations (W1–9) | [01 Markets and Regulation](modules/module-01-financial-markets/README.md) · [02 Python](modules/module-02-python-for-finance/README.md) · [03 Quant Methods](modules/module-03-quant-methods/README.md) · [04 Databases](modules/module-04-databases-data-engineering/README.md) · Bootcamp 1 |
| 2 · Trading and Strategy Design (W10–19) | [05 Technical/Fundamental](modules/module-05-technical-fundamental/README.md) · [06 Derivatives and Options](modules/module-06-derivatives-options/README.md) · [07 Strategies](modules/module-07-trading-strategies/README.md) · [08 Backtesting](modules/module-08-backtesting/README.md) |
| 3 · Risk, Portfolio and Execution (W20–26) | [09 Risk and Portfolio](modules/module-09-risk-portfolio/README.md) · [10 Microstructure and Execution](modules/module-10-microstructure-execution/README.md) · [11 Infrastructure and Compliance](modules/module-11-infrastructure-compliance/README.md) · Bootcamp 2 |
| 4 · AI and Automation (W27–33) | [12 Machine Learning](modules/module-12-machine-learning/README.md) · [13 Deep and Reinforcement Learning](modules/module-13-deep-rl/README.md) · [14 NLP, LLMs and RAG](modules/module-14-nlp-llm-rag/README.md) · [15 n8n Automation](modules/module-15-n8n-automation/README.md) |
| 5 · Capstone and Career (W34–40) | [16 Capstone, Paper Trading, Ethics and Career](modules/module-16-capstone-career/README.md) |

## Course codebase

```
cfmat/          course library (tested): data, metrics, indicators, options, strategies,
                backtest (+ Indian cost model), engine, risk, portfolio, execution,
                broker (OMS/RMS/paper broker), ml, rl, nlp (sentiment + RAG), signal_server
labs/           15 hands-on labs, one per technical module (run as scripts or notebooks)
n8n/            3 importable n8n workflows (signal alerts, news digest, trade-journal webhook)
data/           fictional headlines and annual-report excerpts for the NLP/RAG lab
tests/          unit tests for the library + smoke tests that run every lab
```

### Quick start

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                               # optional extras: data (yfinance), llm (anthropic)
pytest -q                                             # library tests + all 15 labs
python labs/lab08_backtesting_research.py
python -m cfmat.signal_server --port 8000             # service used by the n8n workflows
```

Requires Python 3.10+. Everything runs offline on synthetic data. The optional LLM step in Lab 14 uses the Claude API when `ANTHROPIC_API_KEY` is set.
