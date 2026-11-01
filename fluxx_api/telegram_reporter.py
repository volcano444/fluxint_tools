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
        "credential",
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

    manufacturer = read_android_property("ro.product.manufacturer")
    model = read_android_property("ro.product.model")

    if model:
        if manufacturer and manufacturer.lower() not in model.lower():
            return f"{manufacturer} {model}"[:80]
        return model[:80]

    name = (
        os.environ.get("HOSTNAME")
        or platform.node()
        or platform.machine()
        or "Unknown Device"
    )

    return str(name)[:80]


def get_public_ip(version):
    """Ambil IP publik real-time dari layanan luar. version: 4 atau 6."""
    url = "https://api6.ipify.org" if version == 6 else "https://api.ipify.org"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        ip = response.text.strip()
        return ip if ip else "Unavailable"
    except (requests.RequestException, ValueError):
        return "Unavailable"


def send_report(menu, status, target="", result=None):
    """Kirim laporan jika fitur diaktifkan secara sadar."""
    reports_flag = os.getenv("FLUXX_TELEGRAM_REPORTS", "false").lower()
    if reports_flag != "true":
        print(f"[DEBUG Telegram] reports_flag={reports_flag!r}, berhenti di sini")
        return False

    token = os.getenv("FLUXX_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("FLUXX_TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print(f"[DEBUG Telegram] token_kosong={not token}, chat_id_kosong={not chat_id}")
        return False

    safe_result = redact(result) if result is not None else None
    result_text = json.dumps(
        safe_result,
        ensure_ascii=False,
        indent=2,
    ) if safe_result is not None else "(tidak tersedia)"

    if len(result_text) > 1800:
        result_text = result_text[:1700] + "\n...[hasil dipotong]"

    timestamp = datetime.now().astimezone().strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )

    device_name = get_device_name()
    ip_v4 = get_public_ip(4)
    ip_v6 = get_public_ip(6)

    message = (
        "╭───〔 Fluxx API 〕\n"
        f"│ ID     : {installation_id()}\n"
        f"│ Device : {device_name}\n"
        f"│ IPv4   : {ip_v4}\n"
        f"│ IPv6   : {ip_v6}\n"
        f"│ Menu   : {str(menu)[:80]}\n"
        f"│ Target : {str(target)[:100] if target else '[tidak tersedia]'}\n"
        f"│ Status : {str(status)[:100]}\n"
        f"│ Waktu  : {timestamp}\n"
        "│ Result :\n"
        f"{result_text}\n"
        "╰─────────────────────────────────"
    )

    try:
        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "fluxx-doc.png"
        )

        if not image_path.is_file():
            print(f"[DEBUG Telegram] gambar tidak ditemukan: {image_path}")
            return False

        if len(message) <= 1024:
            caption = message
        else:
            caption = (
                message[:900]
                + "\n...[laporan lengkap dikirim menyusul]"
            )

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
            print(f"[DEBUG Telegram] sendPhoto not ok: {payload}")
            return False

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

    except Exception as exc:
        print(f"[DEBUG Telegram] {type(exc).__name__}: {exc}")
        return False


import threading

_send_report_sync = send_report


def send_report(*args, **kwargs):
    """Kirim laporan di thread terpisah, tapi tunggu maksimal 20 detik."""
    thread = threading.Thread(
        target=_send_report_sync,
        args=args,
        kwargs=kwargs,
    )
    thread.start()
    thread.join(timeout=20)
    return thread
