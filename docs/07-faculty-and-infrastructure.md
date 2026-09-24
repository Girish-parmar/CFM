# Faculty and Infrastructure

## Faculty model

| Role | Count per cohort | Profile |
|---|---|---|
| Program Director | 1 | 15+ years in trading, quant research or risk; PhD, CFA or FRM preferred; owns curriculum quality and the capstone jury |
| Core faculty | 5–6 | One lead per area: markets and derivatives; Python and data engineering; quant research and backtesting; risk and execution; ML/DL; NLP/LLMs and automation |
| Industry practitioners | 8–10 guest sessions | Prop traders, AMC fund managers, broker technology heads, exchange and regtech specialists, compliance officers |
| Practitioner mentors | 1 per 5 learners | Working quants, traders and risk managers; 12 hours of 1:1 mentoring per learner |
| Teaching assistants | 1 per 15 learners | Strong alumni or postgraduates; run lab clinics, review pull requests, hold office hours |

**Faculty standards**

- Every core faculty member has worked with live markets or production trading or risk systems.
- Faculty and mentors declare conflicts of interest, do not solicit learners for paid advisory, signal or tip services, and follow the communication rules in [09-compliance-and-disclaimers.md](09-compliance-and-disclaimers.md).
- Each module has a named owner who updates it every cohort, particularly for regulatory changes, exchange circulars and API changes.

**Faculty development**: a teaching-methods workshop before each cohort, peer observation of one session per module, and learner feedback after every module (target average ≥ 4.3/5).

## Learning infrastructure

| Layer | Tools | Notes |
|---|---|---|
| Programming | Python 3.11+, JupyterLab, VS Code, `cfmat` course library | Labs are Jupytext "percent" scripts: they run as scripts and open as notebooks |
| Version control | Git, GitHub (classroom organisation) | Every lab submitted as a pull request; peer review |
| Databases | SQLite (labs), PostgreSQL + TimescaleDB (tick data), DuckDB + Parquet (research) | Shared read-only research database with licensed data |
| Market data | Licensed historical NSE cash and F&O data (EOD and intraday) for the program term; free sources such as yfinance for practice | Redistribution is not allowed; see compliance |
| Compute | Cloud lab VMs; GPU hours for Module 13; containerised environments with Docker | Per-learner budget with spending alerts |
| Paper trading | Static-IP cloud server per learner for the capstone; `cfmat.broker.PaperBroker`; broker sandbox or paper accounts where available | Mirrors the static-IP and API-key controls of the retail algo framework |
| Automation | Self-hosted n8n (Docker) per learner group | Credentials stored in n8n's credential store, never in workflow JSON |
| AI | LLM API access (for example Claude) with per-learner spending caps; vector database (pgvector or Chroma) | Only public or licensed documents go to LLM APIs |
| LMS | Any LMS with SSO, proctoring integration and gradebook | Quizzes, recordings, discussion forums |
| Bootcamp venue | Trading-floor simulation room: multi-monitor desks, simulated exchange and broker terminals, projector wall for risk dashboards | Hired per bootcamp |

## Setting up the lab environment

```bash
git clone <course repository>
cd CFM
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # add ,data,llm for yfinance and the Claude client
pytest                              # the whole suite should pass
python labs/lab01_markets_instruments.py
```

To open a lab as a notebook: `pip install jupytext`, then in JupyterLab right-click the `.py` file and choose **Open With → Notebook**.

## Support model

| Channel | Response target |
|---|---|
| Lab clinics (Tue/Thu) | Live |
| Discussion forum | Within 12 hours on weekdays |
| TA office hours | 3 slots per week |
| Mentor 1:1 | 6 scheduled sessions |
| Program office (fees, schedule, certificates) | Within 1 working day |
