# Security Policy

## Reporting a vulnerability

Please report security problems privately to the repository owner through GitHub's
**Security → Report a vulnerability** (private vulnerability reporting) rather than in a public
issue. Include the affected file, how to reproduce, and the impact. You will get an
acknowledgement within 3 working days.

## Scope and known design limits

- **Signal service** (`cfmat.automation.signal_service`) is a teaching service with **no authentication**. Bind it to `127.0.0.1` or a private network only. It limits request bodies to 1 MB, accepts only JSON objects, and whitelists symbol names used to locate price files.
- **Rule language** (`cfmat.strategies.rules`) parses rules with Python's `ast` module and evaluates only whitelisted syntax; nothing is passed to `eval`. Rules are capped at 500 characters and exponentiation is not allowed.
- **n8n workflows** must keep credentials in n8n's credential store, never in workflow JSON.
- **Secrets**: broker API keys, LLM API keys and credentials belong to the learner. Keep them in environment variables or a secrets manager; `.env` files are git-ignored. Never commit keys; the pre-commit `detect-private-key` hook helps.
- **Data**: licensed market data must never be committed; the `data/` folder is git-ignored except its README.

## Supported versions

Only the latest release on the default branch receives fixes.
