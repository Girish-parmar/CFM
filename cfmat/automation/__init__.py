"""Automation and monitoring: the signal service and trade journal used by n8n, and live monitoring (M18).

    journal_store    SQLite trade journal
    signal_service   HTTP endpoints (run ``python -m cfmat.automation.signal_service``)
    monitoring       heartbeats, stale feeds, live-vs-backtest drift, P&L attribution, alert rules

``signal_service`` is not imported here so that ``python -m`` runs it cleanly.
"""
