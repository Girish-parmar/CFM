# Your own data (not committed)

Put your own price files here, one CSV per symbol named `<SYMBOL>.csv` with the
columns `date, open, high, low, close, volume`. The signal service
(`python -m cfmat.automation.signal_service`) reads them in place of synthetic prices.

The fetch command writes files in exactly this shape and checks them:

```bash
python -m cfmat.data.fetch yahoo TCS.NS --start 2018-01-01
python -m cfmat.data.fetch alpaca AAPL --start 2020-01-01          # needs ALPACA_API_KEY / ALPACA_SECRET_KEY
python -m cfmat.data.fetch ibkr RELIANCE --exchange NSE --currency INR   # needs TWS or IB Gateway running
```

See the [setup and run guide](../course/12-setup-and-run-guide.md#fetching-real-market-data).

- Everything in this folder except this README is ignored by git (see `.gitignore`).
  Market data is usually licensed: do not commit or share it.
- Set `CFMAT_DATA_DIR` to use a different folder.
- The fictional sample data used by the labs ships inside the package:
  `cfmat/data/samples/`.
