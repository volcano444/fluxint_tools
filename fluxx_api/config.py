import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "endpoints.json"
ENV_PATH = ROOT / ".env"


def load_settings():
    load_dotenv(ENV_PATH)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Config tidak ditemukan: {CONFIG_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON config tidak valid: {exc}") from exc

    return {
        "endpoints": data,
        "timeout": max(1, min(int(os.getenv("FLUXX_TIMEOUT", "20")), 90)),
        "max_response_bytes": max(
            1024, min(int(os.getenv("FLUXX_MAX_RESPONSE_BYTES", "2000000")), 10_000_000)
        ),
        "api_key": os.getenv("FLUXX_API_KEY", "").strip(),
        "api_token": os.getenv("FLUXX_API_TOKEN", "").strip(),
        "session_key": os.getenv("FLUXX_SESSION_KEY", "").strip(),
        "npsn_api_key": os.getenv("FLUXX_NPSN_API_KEY", "").strip(),
        "contact_api_key": os.getenv("FLUXX_CONTACT_API_KEY", "").strip(),
    }
