# Data

Everything here is **fictional**, written for teaching. The companies do not exist and the figures are invented.

| Path | Used by | Contents |
|---|---|---|
| `sample_headlines.csv` | Lab 14, Lab 15, signal service tests | 48 headlines labelled positive / negative / neutral |
| `filings/*.md` | Lab 14 (RAG) | Annual-report excerpts for three fictional companies |

Price data is generated on the fly by `cfmat.data` (geometric Brownian motion, AR(1) returns, factor-model universes and cointegrated pairs), so every lab is reproducible offline. To use your own prices with the signal service, save a CSV with `date, open, high, low, close, volume` columns as `data/<SYMBOL>.csv`. Only use data your licence allows.
