import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ID_PATH = ROOT / ".installation_id"


def installation_id():
    """Buat ID acak lokal yang tetap sama untuk instalasi ini."""
    try:
        if ID_PATH.exists():
            value = ID_PATH.read_text(encoding="utf-8").strip()
            if value:
                return value

        value = str(uuid.uuid4())
        ID_PATH.write_text(value, encoding="utf-8")
        try:
            ID_PATH.chmod(0o600)
        except OSError:
            pass
        return value
    except OSError:
        return "unavailable"


def redact(value, key=""):
    """Hilangkan nilai sensitif sebelum laporan dikirim."""
    sensitive = (
        "password", "token", "secret",
        "authorization", "api_key", "session_key",
        "phone", "email", "credential",
    )

    if any(word in key.lower() for word in sensitive):
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            str(k): redact(v, str(k))
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [redact(item) for item in value[:20]]

    if isinstance(value, str):
        return value[:300]

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    return str(value)[:300]


def get_device_name():
    """Deteksi model perangkat Android dengan fallback yang aman."""
    import os
    import platform
    import subprocess

    def read_android_property(prop):
        try:
            result = subprocess.run(
                ["getprop", prop],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            value = result.stdout.strip()

            if value and value.lower() not in {
                "unknown", "null", "none"
            }:
                return value[:80]

        except (OSError, subprocess.SubprocessError):
            pass

        return None

    # Prioritaskan model perangkat Android.
    manufacturer = read_android_property("ro.product.manufacturer")
    model = read_android_property("ro.product.model")

    if model:
        if manufacturer and manufacturer.lower() not in model.lower():
            return f"{manufacturer} {model}"[:80]
        return model[:80]

    # Fallback untuk lingkungan non-Android.
    name = (
        os.environ.get("HOSTNAME")
        or platform.node()
        or platform.machine()
        or "Unknown Device"
    )

    return str(name)[:80]


def send_report(menu, status, target="", result=None):
    """Kirim laporan jika fitur diaktifkan secara sadar."""
    if os.getenv("FLUXX_TELEGRAM_REPORTS", "false").lower() != "true":
        return False

    token = os.getenv("FLUXX_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("FLUXX_TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        return False

    safe_result = redact(result) if result is not None else None
    result_text = json.dumps(
        safe_result,
        ensure_ascii=False,
        indent=2,
    ) if safe_result is not None else "(tidak tersedia)"

    # Batasi panjang hasil agar pesan tetap aman dikirim.
    if len(result_text) > 1800:
        result_text = result_text[:1700] + "\n...[hasil dipotong]"

    timestamp = datetime.now().astimezone().strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )

    device_name = get_device_name()

    # Tidak mengirim target mentah karena dapat berisi data pribadi.
    message = (
        "╭───〔 Fluxx API 〕\n"
        f"│ ID     : {installation_id()}\n"
        f"│ Device : {device_name}\n"
        f"│ Menu   : {str(menu)[:80]}\n"
        f"│ Target : {str(target)[:100] if target else '[tidak tersedia]'}\n"
        f"│ Status : {str(status)[:100]}\n"
        f"│ Waktu  : {timestamp}\n"
        "│ Result :\n"
        f"{result_text}\n"
        "╰─────────────────────────────────"
    )


    try:
        from pathlib import Path

        # Gambar laporan di folder assets pada root proyek.
        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "fluxx-doc.png"
        )

        if not image_path.is_file():
            return False

        # Caption foto Telegram maksimal 1024 karakter.
        if len(message) <= 1024:
            caption = message
        else:
            caption = (
                message[:900]
                + "\n...[laporan lengkap dikirim menyusul]"
            )

        # Kirim foto beserta caption laporan.
        with image_path.open("rb") as photo:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                },
                files={"photo": photo},
                timeout=15,
            )

        response.raise_for_status()
        payload = response.json()

        if payload.get("ok") is not True:
            return False

        # Jika caption terlalu panjang, kirim laporan lengkap.
        if len(message) > 1024:
            for start in range(0, len(message), 3900):
                chunk = message[start:start + 3900]

                text_response = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                    },
                    timeout=15,
                )

                text_response.raise_for_status()

                if text_response.json().get("ok") is not True:
                    return False

        return True

    except (requests.RequestException, OSError, ValueError):
        # Kegagalan Telegram tidak menghentikan CLI.
        return False
