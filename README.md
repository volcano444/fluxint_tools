# Fluxx API

Configurable terminal API toolkit for Termux. Features a neon-blue CLI menu, configurable HTTP API endpoints, optional API-key/Bearer/session-header authentication, pretty-printed JSON output, and optional JSON file saving.

> API integrations are intentionally unconfigured. Add only API endpoints you are authorized to use. This project does not bypass logins, paywalls, rate limits, or platform protections.

## Features

- Python CLI with Rich terminal styling.
- Ten configurable menu entries.
- GET and POST JSON API requests.
- API auth modes: `none`, `api_key`, `bearer`, `session`.
- JSON pretty printing with line numbers.
- Save results under `output/` (ignored by Git).
- Response timeout and response-size limits.
- GitHub Actions compile/test workflow.

## Install on Termux

```bash
pkg update && pkg upgrade
pkg install python git
git clone https://github.com/USERNAME/fluxx-api.git
cd fluxx-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

If `venv` creation is unavailable on your Termux version, install packages with `pip install --user -r requirements.txt` or follow current Termux Python guidance.

## Configure an API

1. Open `config/endpoints.json`.
2. Find the menu entry you want.
3. Set `enabled` to `true`.
4. Set `url` to the endpoint URL from the provider's documentation.
5. Configure `method`, `params` for GET or `json` for POST.
6. Set the `auth` field to `none`, `api_key`, `bearer`, or `session`.
7. Put secrets in `.env`, never directly in JSON config or Python source.
8. Run `python main.py`.

Example GET endpoint:

```json
"weather": {
  "label": "Deteksi Cuaca",
  "enabled": true,
  "method": "GET",
  "url": "https://api.example.com/weather",
  "auth": "api_key",
  "auth_header": "X-API-Key",
  "params": {
    "q": "{query}"
  }
}
```

Replace the example URL and parameter names with those documented by your provider. In `.env`, set `FLUXX_API_KEY=your_key_here`. The `.env` file is excluded by `.gitignore`.

For a POST endpoint, use `"method": "POST"` and a `"json"` object instead of `"params"`:

```json
"json": {
  "search": "{query}"
}
```

Supported placeholders: `{query}`. For downloader entries, the input is usually a URL. For weather or lyrics, it is usually a city or search phrase. Match the API provider's actual schema.

## Session key clarification

If an API provider specifically documents a session-key header, use `"auth": "session"` and store the value in `FLUXX_SESSION_KEY`. This is not a GitHub login session cookie.

For GitHub, do **not** copy browser session cookies or put a token in source code. Prefer SSH keys or GitHub's supported authentication flow.

## Menu notes

- URL Mirroring: connect an authorized site snapshot/archiving API. The tool does not clone arbitrary sites by itself.
- Deteksi Cuaca: connect a weather API.
- News Gempa (BMKG): connect an official BMKG feed or authorized API.
- NIK Detail: use only lawful, authorized data services and consented test data. NIK is sensitive personal information; never submit another person's NIK without a lawful basis and permission.
- Telegram Spy: intended for public channel metadata or resources you own/administer, not private-account surveillance.
- TikTok Spy: intended for permitted public metadata APIs, not account intrusion or private-data collection.
- TikTok Downloader / IG Downloader: use only for content you own or are permitted to download, and respect platform terms and copyright.
- Play Tera: configure according to the actual service/API you mean.
- Find Lyrics Song: use a licensed API and comply with its display restrictions.

## JSON output

Each API response is wrapped with `tool`, `http_status`, `ok`, and `data`, then displayed as indented JSON. Choose `y` to save a copy to `output/`. Generated output is ignored by Git by default.

## Push to GitHub (recommended: SSH)

Create an empty repository on GitHub named `fluxx-api`, then in Termux:

```bash
git init
git add .
git commit -m "Initial Fluxx API toolkit"
git branch -M main
git remote add origin git@github.com:USERNAME/fluxx-api.git
git push -u origin main
```

Set up an SSH key using GitHub's official documentation. Never commit private keys, `.env`, session cookies, or API tokens. Replace `USERNAME` with your GitHub username.

If using HTTPS instead, authenticate with GitHub's supported credential flow; do not paste tokens into source files or commit history.

## Tests

```bash
pip install pytest
python -m compileall -q .
pytest -q
```

## Project structure

```text
fluxx-api/
├── .github/workflows/python-check.yml
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
├── config/
│   └── endpoints.json
├── fluxx_api/
│   ├── __init__.py
│   ├── cli.py
│   ├── client.py
│   ├── config.py
│   └── formatter.py
└── tests/
    └── test_formatter.py
```

## Security notes

- Keep `.env` private; `.gitignore` is not a substitute for checking `git status`.
- Do not paste credentials into screenshots, chat, or public issues.
- Only connect to APIs whose usage and data handling you understand.
- Review provider rate limits, privacy requirements, and terms before enabling endpoints.
