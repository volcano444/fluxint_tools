import os
from pathlib import Path

from dotenv import load_dotenv

from .github_config import fetch_remote_config


ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def load_settings():
    load_dotenv(ENV_PATH)

    timeout = max(
        1,
        min(int(os.getenv("FLUXX_TIMEOUT", "20")), 90),
    )

    max_response_bytes = max(
        1024,
        min(
            int(os.getenv("FLUXX_MAX_RESPONSE_BYTES", "2000000")),
            10_000_000,
        ),
    )

    github_token = os.getenv(
        "FLUXX_GITHUB_TOKEN", ""
    ).strip()

    remote = fetch_remote_config(
        github_token,
        timeout=15,
    )

    settings = {
        "endpoints": remote["endpoints"],
        "timeout": timeout,
        "max_response_bytes": max_response_bytes,
        "api_key": "",
        "api_token": "",
        "session_key": "",
    }

    settings.update(remote["api_keys"])

    # GetContact hanya menggunakan kredensial lokal.
    settings["gtc_token"] = os.getenv(
        "FLUXX_GTC_TOKEN", ""
    ).strip()

    return settings
