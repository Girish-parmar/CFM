# Compliance and Risk Disclosures

This page lists the regulatory points a trading-education provider in India must manage. It is a checklist for the program team, **not legal advice**. Regulations and circulars change often. Before launch and before every cohort, have a securities lawyer or compliance professional check this page against the current SEBI circulars, exchange circulars and tax rules.

## 1. Education, not advice

- The program teaches methods. It does **not** give investment advice, research recommendations, trading tips, signals or portfolio management to learners or the public.
- Giving investment advice for consideration requires registration under the SEBI (Investment Advisers) Regulations, 2013; publishing research reports or recommendations requires registration under the SEBI (Research Analysts) Regulations, 2014. The institute, faculty and mentors must not do either through the program unless the relevant entity is registered and the activity is kept separate from teaching.
- SEBI has restricted regulated entities (brokers, advisers and others) from associating with unregistered persons who give advice or recommendations or make claims of returns. Persons **exclusively engaged in education** are exempt only if they meet the conditions. SEBI's January 2025 clarification added, among other things, that such persons must not use market price data of the preceding three months when talking about named securities, or in any way that indicates a future price, advice or recommendation. The program applies this as follows:
  - Case studies and live examples that name a security use data at least three months old.
  - Labs use synthetic data or historical data, and never present results as a view on what a security will do.
  - No "stock of the week", no live calls, no screenshots of the instructor's own trades, no Telegram or WhatsApp tip groups.
  - Screener results, strategy signals and alerts built in the course (M12 Strategy Studio, M18 automation) stay inside the classroom and learners' own research. They must not be published or shared as lists of securities to buy or sell.
- Any partnership or referral arrangement with a SEBI-registered broker or other regulated entity must be reviewed against the rules on association with unregistered persons before it is signed.

## 2. SEBI's retail algorithmic trading framework

SEBI's circular of 4 February 2025, *Safer participation of retail investors in algorithmic trading*, with the exchanges' implementation standards, applies in phases from late 2025. Confirm the current timeline and thresholds on the NSE and BSE websites. Key points taught in M17 and reflected in the capstone:

- Brokers act as principals; algo providers act as their agents and must be empanelled with the exchanges.
- Algo orders carry an exchange-provided unique identifier, which gives an audit trail.
- API access goes through vendor-client-specific API keys and static IP whitelisting; open APIs are not allowed.
- Algos above an exchange-specified orders-per-second threshold must be registered with the exchange; tech-savvy clients who build their own algos above that threshold must register them through their broker.
- "White-box" algos disclose their logic. For "black-box" algos, the provider must be registered as a Research Analyst and meet its reporting requirements.
- Brokers must keep controls such as kill switches and pre-trade risk checks.

**What this means for the program**

- Capstone strategies run in **paper trading only** (`cfmat.trading.PaperBroker`, or a broker's paper or sandbox environment where available). The static-IP server, RMS limits and monitoring are there so learners practise the real controls.
- The institute does not provide, sell or rent algos to learners or the public. Doing that would need empanelment through a broker and, for black-box algos, Research Analyst registration.
- Learners who later trade their own money through a broker API are responsible for following their broker's onboarding, registration and risk requirements.

## 3. Risk disclosure (shown on the website, brochure and enrolment form)

> Trading in securities and derivatives involves substantial risk of loss. SEBI's study of equity F&O traders (published September 2024) found that about 93% of individual traders made losses between FY22 and FY24. Past performance, including backtested and paper-trading results shown in this program, does not guarantee future results. The program is educational. It does not provide investment advice or recommendations, and it does not guarantee trading profits, income or placement.

Link the latest SEBI study on F&O trader outcomes in all marketing material.

## 4. Advertising and marketing rules

Consumer protection law (the Consumer Protection Act, 2019, the 2022 guidelines on misleading advertisements and the 2023 guidelines on dark patterns) applies to course marketing. The program team must **not**:

- claim or imply guaranteed returns, "passive income", "financial freedom" or a win rate;
- show P&L screenshots, lifestyle imagery or learner trading profits;
- promise placement, salary levels or 100% placement;
- use the SEBI, NSE, BSE or NISM logos, or imply endorsement by a regulator or exchange;
- use fake urgency (countdown timers that reset, false "last 2 seats");
- publish testimonials that mention returns, or that are paid for without disclosure.

Placement data, if published, must be audited and show the base and period (see [admissions and careers](08-admissions-and-careers.md)). Fee communication must show the all-inclusive amount and its GST split exactly as in the [fee plan](03-fee-plan.md).

## 5. Data licensing

- Real-time and historical exchange data are licensed products. Use a licensed vendor for course data, check that the licence covers classroom use, and do not redistribute raw data to learners beyond what the licence allows.
- The sample data in this repository (`cfmat/data/samples/`) is fictional; company names in the headlines and filings are invented for teaching. Price data is generated synthetically by `cfmat.data`. Learners' own price files go in `data/`, which is git-ignored so licensed data is never committed.
- Free sources (for example yfinance) are for personal learning; their terms of use apply.

## 6. Learner data and privacy

- Handle learner personal data in line with the Digital Personal Data Protection Act, 2023: collect only what is needed, get consent, secure it, and delete it on request or when no longer needed.
- Broker API keys, LLM API keys and n8n credentials belong to the learner. Never collect them. Teach secrets management (environment variables and credential stores), and never commit keys to Git.
- Proctoring recordings are kept only as long as the assessment policy needs them.

## 7. Tax and invoicing

- GST at 18% applies to the program fee as a commercial training service. Confirm with a chartered accountant, especially if the certificate is issued jointly with a university.
- Issue GST invoices for every instalment. For employer-sponsored learners, invoice the employer with its GSTIN.
- If EMI partners are used, disclose any interest or processing fee clearly before enrolment.

## 8. Credential wording

- Call it a "Certificate in Financial Market and Algorithmic Trading" issued by the institute. Do not describe it as a degree, diploma or SEBI/NISM certification unless a recognised partner awards it.
- NISM certifications are earned by passing NISM's own exams; the program includes vouchers and preparation only.

## 9. Professional conduct taught in the program

M24 covers the SEBI (Prohibition of Insider Trading) Regulations, 2015, the SEBI (Prohibition of Fraudulent and Unfair Trade Practices relating to Securities Market) Regulations, 2003 (including spoofing, layering, front-running and circular trading), and the confidentiality duties of anyone working with order flow or client data.

## 10. AI and LLM use in the programme

- Only public or licensed documents are sent to LLM APIs; never learner personal data, client data or confidential employer material.
- LLM outputs in labs (M22) are grounded in retrieved sources, cite them, and refuse when the sources are silent. They are research aids, not advice.
- AI agents in automations (M18) draft and summarise; a human decides. No agent may place orders.
- Per-learner API spending caps and usage logs are kept for cost control and audit.

## 11. Review cadence

| What | When | Owner |
|---|---|---|
| This page against current SEBI and exchange circulars | Before every cohort | Programme director + compliance adviser |
| Charge sheet, STT and exchange fees (`RATES_AS_OF` in `cfmat/microstructure/costs.py`) | Before every cohort and after every Union Budget | Markets lead |
| Marketing material against section 4 | Before publication | Programme manager + compliance adviser |
| Data licences | Annually | Programme manager |

## Standard disclaimer (for the website, brochure, LMS and every lab)

> This program and its materials are for education only. Nothing in them is investment advice, a research recommendation, or an offer or solicitation to buy or sell any security. Examples use synthetic, fictional or historical data. Trading involves substantial risk of loss. Consult a SEBI-registered investment adviser before making investment decisions.
