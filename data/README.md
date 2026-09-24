# Your own data (not committed)

Put your own price files here, one CSV per symbol named `<SYMBOL>.csv` with the
columns `date, open, high, low, close, volume`. The signal service
(`python -m cfmat.automation.signal_service`) reads them in place of synthetic prices.

- Everything in this folder except this README is ignored by git (see `.gitignore`).
  Market data is usually licensed: do not commit or share it.
- Set `CFMAT_DATA_DIR` to use a different folder.
- The fictional sample data used by the labs ships inside the package:
  `cfmat/data/samples/`.
