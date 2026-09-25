# Faculty and Infrastructure

## Faculty model

| Role | Count per cohort | Profile |
|---|---|---|
| Programme director | 1 | 15+ years in trading, quant research or risk; owns curriculum quality, the audit and the capstone jury |
| Core faculty (module owners) | 6 | One lead per area: markets, macro and derivatives; Python and data engineering; quant research and backtesting; risk, portfolio and execution; ML/DL and advanced strategies; NLP/LLMs and automation |
| Industry practitioners | 10 guest sessions | Prop traders, AMC fund managers, broker technology and execution heads, exchange and regtech specialists, compliance officers, an economist |
| Practitioner mentors | 1 per 6 learners | Working quants, traders and risk managers; 24 hours of 1:1 mentoring per learner |
| Teaching assistants | 3 (1 per 12–13 learners) | Strong alumni or postgraduates; run clinics, review pull requests, hold office hours |
| Programme manager | 1 | Operations, learner success, scheduling, vendor management |
| Career services lead | 1 (part-time) | Career studio, employer connect, alumni |

**Faculty standards.** Every core faculty member has worked with live markets or production
trading or risk systems. Faculty and mentors declare conflicts of interest, never solicit learners
for advisory, signal or tip services, and follow the rules in [compliance](09-compliance-and-risk-disclosures.md).
Each module has a named owner (see each module guide's instructor notes) who refreshes it every
cohort — especially for regulation, exchange circulars, charges and APIs.

**Faculty development.** A teaching-methods workshop before each cohort; peer observation of one
session per module; learner feedback after every module (target ≥ 4.3 / 5); a shared log of
"what went wrong in class" reviewed at each term's retrospective.

## Learning infrastructure

| Layer | Tools | Notes |
|---|---|---|
| Programming | Python 3.11 or 3.12 (see the [setup guide](12-setup-and-run-guide.md)), VS Code, JupyterLab, the `cfmat` library; scikit-learn, statsmodels, XGBoost, LightGBM, Optuna | Labs are Jupytext percent scripts: run as scripts, open as notebooks |
| Version control and CI | Git, GitHub Classroom; GitHub Actions | Every lab submitted as a pull request; peer review; CI runs lint, tests and labs |
| Databases | SQLite (labs), PostgreSQL + TimescaleDB (tick data), DuckDB + Parquet (research) | Shared read-only research database with licensed data |
| Market data | Licensed historical NSE cash and F&O data (EOD and intraday) for the programme and 6 months after | Redistribution not allowed; see compliance |
| Compute | Cloud lab VMs; GPU hours for M20–M23; Docker images | Per-learner budget with spending alerts |
| Paper trading | Static-IP cloud server per learner for the capstone; `cfmat.trading.PaperBroker`; broker sandboxes where available | Mirrors the static-IP and API-key controls of the retail-algo framework |
| Automation | Self-hosted n8n (Docker) per learner group | Credentials in n8n's store, never in workflow JSON |
| AI | LLM API access (Claude) with per-learner caps; optional vector database | Only public or licensed documents go to LLM APIs |
| LMS | LMS with SSO, proctoring and gradebook | Quizzes, recordings, forums |
| Bootcamp venue | Trading-floor simulation room with multi-monitor desks, simulated exchange and broker terminals | Hired per bootcamp |

## Setting up the lab environment

```bash
git clone <course repository>
cd CFM
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                          # tested versions (Python 3.11 or 3.12)
# or: pip install -e ".[dev,boost]"                      # latest compatible versions
make check                                               # lint, unit tests, manifest check
python curriculum/m00-prework/lab_00a_environment_check.py
```

To open a lab as a notebook: `pip install jupytext`, then in JupyterLab right-click the `.py` file
and choose **Open With → Notebook**. Charts go to `build/lab-output/` (set `CFMAT_OUTPUT_DIR` to
change it).

## Support model

| Channel | Response target |
|---|---|
| Lab clinics (Tue/Thu) | Live |
| Office hours (Wed) | Live |
| Discussion forum | Within 12 hours on weekdays |
| Mentor 1:1 | 24 scheduled sessions |
| Programme office (fees, schedule, certificates) | Within 1 working day |
| Incidents in the lab infrastructure | Acknowledged within 2 hours during programme hours |

## Course codebase quality gates

The course library is itself taught as an example of good practice. Every change must pass:
ruff lint, the unit-test matrix (Python 3.10 and 3.12, plus a pinned 3.11 environment), every lab
as a smoke test, the manifest check (`tools/route_manager.py check`) and the generated-docs check.
See [CONTRIBUTING](../CONTRIBUTING.md).
