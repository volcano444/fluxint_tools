import os
import platform
import re
import socket
import uuid
from pathlib import Path

from rich import box
import requests
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from .client import APIClientError, request_api
from .config import load_settings
from .formatter import save_json, show_json
from .telegram_reporter import send_report

console = Console()

MENU = [
    ("1", "ai_chat"),
    ("2", "weather"),
    ("3", "earthquake_bmkg"),
    ("4", "nik_detail"),
    ("5", "telegram_spy"),
    ("6", "tiktok_spy"),
    ("7", "tiktok_downloader"),
    ("8", "instagram_downloader"),
    ("9", "play_tera"),
    ("10", "find_lyrics"),
    ("11", "spotify_dl"),
    ("12", "ngl_spammer"),
    ("13", "find_npsn"),
    ("14", "get_contact"),
    ("15", "find_ff"),
    ("16", "find_ml"),
    ("17", "find_roblox"),
    ("18", "react_saluran"),
    ("19", "tempmail_create"),
    ("20", "find_nopol"),
    ("21", "find_locate"),
    ("22", "find_airport"),
]



INPUT_HINTS = {
    "ai_chat": ("Masukkan pertanyaan untuk AI", "Jelaskan apa itu Python?"),
    "weather": ("Masukkan nama kota atau daerah", "Jakarta"),
    "earthquake_bmkg": ("Tidak memerlukan input", "Jakarta"),
    "nik_detail": ("Masukkan NIK", "320XXXXXXXXXXXXX"),
    "telegram_spy": ("Masukkan username Telegram", "@username"),
    "tiktok_spy": ("Masukkan username TikTok", "username"),
    "tiktok_downloader": ("Masukkan URL video TikTok", "https://vt.tiktok.com/xxxx"),
    "instagram_downloader": ("Masukkan URL postingan Instagram", "https://instagram.com/p/xxxx"),
    "play_tera": ("Input Url Terabox", "https://terabox.com/xxxx"),
    "find_lyrics": ("Masukkan judul lagu", "Sempurna"),
    "spotify_dl": ("Masukkan URL Spotify atau judul lagu", "https://open.spotify.com/track/xxxx"),
    "ngl_spammer": ("Fitur tidak menyediakan input umum", "-"),
    "find_npsn": ("Masukkan nama sekolah", "SMAN 1 Mojang"),
    "get_contact": ("Masukkan nomor telepon", "081234567890"),
    "find_ff": ("Masukkan UID Free Fire", "123456789"),
    "find_ml": ("Masukkan ID dan Zone, pisahkan dengan |", "12345678|1234"),
    "find_roblox": ("Masukkan username Roblox", "BLTOREO"),
    "react_saluran": ("Masukkan URL saluran WhatsApp", "https://whatsapp.com/channel/0029VbDsPB4C1FuJcFjbgV1t"),
    "tempmail_create": ("Membuat email sementara", ""),
    "find_nopol": ("Masukkan plat nomor kendaraan", "B 1234 XYZ"),
    "find_locate": ("Masukkan alamat atau koordinat", "Monas, Jakarta / -6.1754,106.8272"),
    "find_airport": ("Masukkan nama bandara atau kode IATA", "Juanda atau SUB"),
}

def get_installation_id():
    """Buat ID instalasi lokal dan gunakan kembali pada sesi berikutnya."""
    config_dir = Path.home() / ".config" / "fluxx-api"
    id_file = config_dir / "install_id"

    try:
        config_dir.mkdir(parents=True, exist_ok=True)

        if id_file.exists():
            saved_id = id_file.read_text(encoding="utf-8").strip()
            if saved_id:
                return saved_id

        new_id = str(uuid.uuid4())
        id_file.write_text(new_id, encoding="utf-8")

        try:
            id_file.chmod(0o600)
        except OSError:
            pass

        return new_id

    except OSError:
        # Tetap bisa menampilkan ID jika penyimpanan gagal.
        return "TEMP-" + uuid.uuid4().hex[:12].upper()


def get_local_ip():
    """Deteksi IP lokal dari interface jaringan yang digunakan."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "Unavailable"
    finally:
        sock.close()


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

# ASCII art FLUXXINT dengan gradasi biru -> cyan per baris.
BANNER_ART = [
    "███████╗██╗     ██╗   ██╗██╗  ██╗██╗  ██╗██╗███╗   ██╗████████╗",
    "██╔════╝██║     ██║   ██║╚██╗██╔╝╚██╗██╔╝██║████╗  ██║╚══██╔══╝",
    "█████╗  ██║     ██║   ██║ ╚███╔╝  ╚███╔╝ ██║██╔██╗ ██║   ██║",
    "██╔══╝  ██║     ██║   ██║ ██╔██╗  ██╔██╗ ██║██║╚██╗██║   ██║",
    "██║     ███████╗╚██████╔╝██╔╝ ██╗██╔╝ ██╗██║██║ ╚████║   ██║",
    "╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝   ╚═╝",
]

BANNER_GRADIENT = [
    "rgb(0,110,255)",
    "rgb(0,145,255)",
    "rgb(0,180,255)",
    "rgb(0,210,255)",
    "rgb(0,235,255)",
    "rgb(0,255,255)",
]


def build_banner_art(width):
    """Art besar kalau muat; kalau layar sempit pakai versi ringkas."""
    art = Text()

    if width >= len(BANNER_ART[0]) + 4:
        for index, (style, line) in enumerate(zip(BANNER_GRADIENT, BANNER_ART)):
            art.append(line, style=f"bold {style}")
            if index < len(BANNER_ART) - 1:
                art.append("\n")
    else:
        letters = "FLUXXINT"
        last = len(BANNER_GRADIENT) - 1
        for index, letter in enumerate(letters):
            style = BANNER_GRADIENT[round(index * last / (len(letters) - 1))]
            if index:
                art.append(" ")
            art.append(letter, style=f"bold {style}")

    return art


def banner():
    console.print()
    console.print(
        Align.center(
            build_banner_art(console.width)
        )
    )
    console.print(
        Align.center(
            Text(
                "OPEN SOURCE TOOL API | OSINT",
                style="bold bright_cyan",
            )
        )
    )
    console.print()


def draw_device_info():
    """Tampilkan informasi instalasi dan perangkat secara terpisah."""
    device_id = get_installation_id()
    local_ip = get_local_ip()
    device_name = get_device_name()

    table = Table(
        title="[bold bright_cyan]DEVICE INFORMATION[/]",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold bright_cyan",
        show_header=True,
        show_lines=True,
        expand=True,
    )

    table.add_column("PROPERTY", style="bright_cyan", width=10)
    table.add_column("INFORMATION", style="white", overflow="fold")

    table.add_row("ID", device_id)
    table.add_row("IP", local_ip)
    table.add_row("DEVICE", device_name)

    console.print(
        Panel(
            table,
            border_style="bright_blue",
            padding=(0, 1),
        )
    )


def draw_menu(settings):
    table = Table(
        title="[bold bright_cyan]FLUXXINT / MAIN MENU[/]",
        box=box.DOUBLE,
        border_style="bright_blue",
        header_style="bold bright_cyan",
        show_lines=True,
        expand=True,
    )

    table.add_column("#", style="bright_cyan", width=4, justify="center")
    table.add_column("TOOL", style="white", overflow="fold")
    table.add_column("STATUS", width=12, justify="center")

    for number, key in MENU:
        endpoint = settings["endpoints"].get(key, {})
        label = endpoint.get("label", key)

        status = (
            "[green]READY[/]"
            if endpoint.get("enabled") and endpoint.get("url")
            else "[red]Maintenance[/]"
        )

        table.add_row(number, label, status)

    table.add_row("0", "Exit", "[dim]QUIT[/]")

    console.print(
        Panel(
            table,
            border_style="bright_blue",
            padding=(1, 1),
        )
    )


def build_auth_headers(endpoint, settings):
    """Bangun header sesuai konfigurasi auth di endpoints.json."""
    headers = {"Accept": "application/json"}

    if endpoint.get("auth") == "api_key":
        key_name = endpoint.get("api_key_setting", "api_key")
        key = settings.get(key_name, "")

        if not key:
            raise APIClientError(
                f"Key '{key_name}' belum tersedia di GitHub remote config."
            )

        headers[endpoint.get("auth_header", "X-API-Key")] = key

    return headers

def find_npsn(endpoint, query, settings):
    """Cari sekolah, pilih NPSN, lalu ambil detail sekolah."""
    search_url = endpoint["url"]
    detail_url = endpoint["detail_url"]
    timeout = settings["timeout"]

    try:
        headers = build_auth_headers(endpoint, settings)
    except APIClientError as exc:
        console.print(f"[red]{exc}[/]")
        return

    try:
        response = requests.get(
            search_url,
            params={"q": query},
            headers=headers,
            timeout=timeout,
        )

        if response.status_code == 429:
            console.print(
                "[yellow]API sedang membatasi permintaan. "
                "Tunggu sebentar sebelum mencoba lagi.[/]"
            )
            return

        response.raise_for_status()
        payload = response.json()

    except (requests.RequestException, ValueError) as exc:
        console.print(f"[red]Pencarian sekolah gagal:[/] {exc}")

        send_report(
            menu="Find NPSN",
            status="Search Error",
            target="N/A",
            result={
                "ok": False,
                "error": "Pencarian sekolah gagal.",
            },
        )
        return

    schools = payload

    if isinstance(payload, dict):
        for key in ("data", "results", "result", "schools"):
            if key in payload:
                schools = payload[key]
                break

    if isinstance(schools, dict):
        for key in ("data", "results", "result", "schools"):
            if isinstance(schools.get(key), list):
                schools = schools[key]
                break
        else:
            schools = [schools]

    if not isinstance(schools, list) or not schools:
        console.print("[yellow]Sekolah tidak ditemukan.[/]")
        return

    valid_schools = [
        school
        for school in schools
        if isinstance(school, dict) and school.get("npsn")
    ]

    if not valid_schools:
        console.print(
            "[yellow]Hasil API tidak berisi field NPSN yang dikenali.[/]"
        )
        show_json(payload, "SEARCH RESPONSE")
        return

    table = Table(
        title="HASIL PENCARIAN SEKOLAH",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("No.", justify="right")
    table.add_column("Nama Sekolah")
    table.add_column("NPSN")

    for index, school in enumerate(valid_schools, start=1):
        name = (
            school.get("nama")
            or school.get("name")
            or school.get("nama_sekolah")
            or "Nama tidak tersedia"
        )

        table.add_row(
            str(index),
            str(name),
            str(school["npsn"]),
        )

    console.print(table)

    choice = Prompt.ask(
        "Pilih nomor sekolah",
        choices=[
            str(i)
            for i in range(1, len(valid_schools) + 1)
        ],
    )

    selected_school = valid_schools[int(choice) - 1]
    npsn = str(selected_school["npsn"])

    try:
        response = requests.get(
            detail_url,
            params={"npsn": npsn},
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        detail = response.json()

    except (requests.RequestException, ValueError) as exc:
        console.print(f"[red]Gagal mengambil detail sekolah:[/] {exc}")
        return

    show_json(detail, f"DETAIL SEKOLAH — NPSN {npsn}")

    send_report(
        menu="Find NPSN",
        status="Successfully",
        target="NPSN terpilih",
        result={
            "ok": True,
            "http_status": response.status_code,
            "detail": detail,
        },
    )

    if Prompt.ask(
        "Simpan JSON ke output/?",
        choices=["y", "n"],
        default="n",
    ) == "y":
        path = save_json(detail, "find_npsn")
        console.print(
            f"[green]JSON tersimpan:[/] "
            f"{path.relative_to(path.parents[1])}"
        )

def find_spotify(endpoint, settings):
    """Cari lagu Spotify, pilih hasil, lalu ambil link download."""
    base_url = endpoint["url"]
    timeout = settings["timeout"]

    try:
        headers = build_auth_headers(endpoint, settings)
    except APIClientError as exc:
        console.print(f"[red]{exc}[/]")
        return

    console.print("[bold bright_cyan]➤ Judul lagu[/]")
    console.print("[dim]  Contoh: shape of you[/]")
    query = Prompt.ask(
        "[bold bright_cyan]ㅤㅤ╰›[/]",
        default="",
        show_default=False,
    ).strip()

    if not query:
        console.print("[yellow]⚠ Input kosong, dibatalkan.[/]")
        return

    try:
        response = requests.get(
            base_url,
            params={"action": "search", "q": query},
            headers=headers,
            timeout=timeout,
        )

        if response.status_code in (401, 403):
            console.print("[red]API key ditolak. Periksa spotify_api_key pada remote config.[/]")
            return

        response.raise_for_status()
        payload = response.json()

    except (requests.RequestException, ValueError) as exc:
        console.print(f"[red]Pencarian gagal:[/] {exc}")
        send_report(
            menu="Spotify Downloader",
            status="Search Error",
            target=query,
            result={"ok": False, "error": "Pencarian gagal."},
        )
        return

    tracks = payload
    if isinstance(payload, dict):
        for key in ("data", "results", "result", "tracks"):
            if key in payload:
                tracks = payload[key]
                break

    if not isinstance(tracks, list) or not tracks:
        console.print("[yellow]Lagu tidak ditemukan.[/]")
        show_json(payload, "SEARCH RESPONSE")
        return

    valid_tracks = [
        t for t in tracks
        if isinstance(t, dict) and (t.get("url") or t.get("link") or t.get("track_url"))
    ]

    if not valid_tracks:
        console.print("[yellow]Hasil API tidak berisi URL track yang dikenali.[/]")
        show_json(payload, "SEARCH RESPONSE")
        return

    table = Table(title="HASIL PENCARIAN SPOTIFY", box=box.ROUNDED, show_lines=True)
    table.add_column("No.", justify="right")
    table.add_column("Judul")
    table.add_column("Artis")

    for index, t in enumerate(valid_tracks, start=1):
        title = t.get("title") or t.get("name") or "Tidak diketahui"
        artist = t.get("artist") or t.get("artists") or "-"
        table.add_row(str(index), str(title), str(artist))

    console.print(table)

    choice = Prompt.ask(
        "Pilih nomor lagu",
        choices=[str(i) for i in range(1, len(valid_tracks) + 1)],
    )

    selected_track = valid_tracks[int(choice) - 1]
    track_url = (
        selected_track.get("url")
        or selected_track.get("link")
        or selected_track.get("track_url")
    )
    title = selected_track.get("title") or selected_track.get("name") or query

    try:
        response = requests.get(
            base_url,
            params={"action": "download", "url": track_url},
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        detail = response.json()

    except (requests.RequestException, ValueError) as exc:
        console.print(f"[red]Gagal mengambil link download:[/] {exc}")
        send_report(
            menu="Spotify Downloader",
            status="Download Error",
            target=title,
            result={"ok": False, "error": str(exc)},
        )
        return

    show_json(detail, f"DOWNLOAD — {title}")

    send_report(
        menu="Spotify Downloader",
        status="Successfully",
        target=title,
        result={"ok": True, "http_status": response.status_code, "detail": detail},
    )

    if Prompt.ask(
        "Simpan JSON ke output/?",
        choices=["y", "n"],
        default="n",
    ) == "y":
        path = save_json(detail, "spotify_dl")
        console.print(
            f"[green]JSON tersimpan:[/] {path.relative_to(path.parents[1])}"
        )

def send_ngl(endpoint, settings):
    """Kirim satu pesan NGL ke username target lewat API."""
    url = endpoint.get("url")

    if not url:
        console.print(
            "[red]URL ngl_spammer belum diisi di endpoints.json.[/]"
        )
        return

    try:
        headers = build_auth_headers(endpoint, settings)
    except APIClientError as exc:
        console.print(f"[red]{exc}[/]")
        return

    console.print("[bold bright_cyan]➤ Username NGL target[/]")
    username = Prompt.ask(
        "[bold bright_cyan]ㅤㅤ╰›[/]",
        default="",
        show_default=False,
    ).strip()

    console.print("[bold bright_cyan]➤ Pesan[/]")
    text = Prompt.ask(
        "[bold bright_cyan]ㅤㅤ╰›[/]",
        default="",
        show_default=False,
    ).strip()

    if not username or not text:
        console.print("[yellow]⚠ Input kosong, dibatalkan.[/]")
        return

    label = endpoint.get("label", "NGL")

    try:
        response = requests.get(
            url,
            params={"usr": username, "text": text},
            headers=headers,
            timeout=(5, 15),
        )

        try:
            body = response.json()
        except ValueError:
            body = response.text

        result = {
            "ok": response.ok,
            "http_status": response.status_code,
            "response": body,
        }

        console.print(f"[bright_cyan]HTTP:[/] {response.status_code}")
        show_json(result, label)

        send_report(
            menu=label,
            status="Successfully" if response.ok else "API Error",
            target=username,
            result=result,
        )

    except requests.exceptions.Timeout:
        error = "API timeout: server tidak merespons."
    except requests.exceptions.ConnectionError:
        error = "Gagal terhubung ke server API."
    except requests.exceptions.RequestException as exc:
        error = f"Request error: {exc}"
    else:
        return

    error_result = {"ok": False, "error": error}
    show_json(error_result, "FLUXX ERROR")
    send_report(
        menu=label,
        status="API Error",
        target=username,
        result=error_result,
    )


def render_template(value, variables):
    """Ganti {nama} di string / dict / list dengan nilai input pengguna."""
    if isinstance(value, str):
        for name, text in variables.items():
            value = value.replace("{" + name + "}", text)
        return value

    if isinstance(value, dict):
        return {k: render_template(v, variables) for k, v in value.items()}

    if isinstance(value, list):
        return [render_template(item, variables) for item in value]

    return value


def extract_reply(body):
    """Cari teks jawaban AI di dalam respons JSON; None jika tidak ketemu."""
    if isinstance(body, str):
        return body.strip() or None

    if isinstance(body, dict):
        for key in (
            "result", "response", "reply", "answer",
            "message", "text", "content", "output", "data",
        ):
            if key in body:
                found = extract_reply(body[key])
                if found:
                    return found

    return None


def send_ai_chat(endpoint, settings):
    """Pilih model AI, kirim pertanyaan, lalu tampilkan jawabannya."""
    modes = endpoint.get("modes", {})

    if not modes:
        console.print("[red]Daftar model AI belum diisi di endpoints.json.[/]")
        return

    try:
        headers = build_auth_headers(endpoint, settings)
    except APIClientError as exc:
        console.print(f"[red]{exc}[/]")
        return

    for num, m in modes.items():
        console.print(f"[bright_cyan]{num}[/] {m['label']}")

    mode_choice = Prompt.ask(
        "[bold bright_cyan]Pilih model[/]",
        choices=list(modes),
        default="1",
    )
    mode = modes[mode_choice]

    values = {}
    for var, hint, example in mode["inputs"]:
        console.print(f"[bold bright_cyan]➤ {hint}[/]")
        console.print(f"[dim]  Contoh: {example}[/]")
        values[var] = Prompt.ask(
            "[bold bright_cyan]ㅤㅤ╰›[/]",
            default="",
            show_default=False,
        ).strip()

    if not all(values.values()):
        console.print("[yellow]⚠ Input kosong, dibatalkan.[/]")
        return

    label = f"{endpoint.get('label', 'AI CHAT')} / {mode['label']}"
    method = mode.get("method", "GET").upper()
    params = render_template(mode.get("params", {}), values)
    body = render_template(mode.get("body"), values)

    try:
        with console.status("[bright_cyan]Menunggu jawaban...[/]"):
            if method == "POST":
                response = requests.post(
                    mode["url"],
                    params=params or None,
                    json=body,
                    headers=headers,
                    timeout=(5, 60),
                )
            else:
                response = requests.get(
                    mode["url"],
                    params=params,
                    headers=headers,
                    timeout=(5, 60),
                )

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        result = {
            "ok": response.ok,
            "http_status": response.status_code,
            "response": payload,
        }

    except requests.exceptions.Timeout:
        error = "API timeout: server tidak merespons."
    except requests.exceptions.ConnectionError:
        error = "Gagal terhubung ke server API."
    except requests.exceptions.RequestException as exc:
        error = f"Request error: {exc}"
    else:
        error = None

    if error:
        error_result = {"ok": False, "error": error}
        show_json(error_result, "FLUXX ERROR")
        send_report(
            menu=label,
            status="API Error",
            target=mode["label"],
            result=error_result,
        )
        return

    console.print(f"[bright_cyan]HTTP:[/] {response.status_code}")

    reply = extract_reply(payload) if response.ok else None

    if reply:
        console.print(
            Panel(
                Text(reply),
                title=f"[bold cyan]{mode['label']}[/]",
                border_style="bright_blue",
            )
        )
    else:
        show_json(result, label)

    # Isi percakapan tidak ikut dilaporkan; hanya status dan model.
    send_report(
        menu=label,
        status="Successfully" if response.ok else "API Error",
        target=mode["label"],
        result={"ok": response.ok, "http_status": response.status_code},
    )

    if Prompt.ask(
        "Simpan JSON ke output/? (y/n)",
        choices=["y", "n"],
        default="n",
    ) == "y":
        path = save_json(result, "ai_chat")
        console.print(
            f"[green]JSON tersimpan:[/] "
            f"{path.relative_to(path.parents[1])}"
        )

def extract_temp_mail_data(payload):
    """Cari alamat email dan token dari respons API secara rekursif."""
    result = {
        "email": None,
        "token": None,
    }

    email_keys = {"email", "mail", "address", "email_address"}
    token_keys = {"token", "mail_token", "access_token"}

    def scan(value):
        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = str(key).lower()

                if isinstance(item, (str, int)):
                    if normalized_key in email_keys and not result["email"]:
                        result["email"] = str(item)

                    elif normalized_key in token_keys and not result["token"]:
                        result["token"] = str(item)

                if isinstance(item, (dict, list)):
                    scan(item)

        elif isinstance(value, list):
            for item in value:
                scan(item)

    scan(payload)
    return result


def run_temp_mail(settings):
    """Buat email sementara dan sediakan pilihan untuk memeriksa inbox."""
    endpoints = settings["endpoints"]
    create_endpoint = endpoints.get("tempmail_create", {})
    inbox_endpoint = endpoints.get("tempmail_inbox", {})
    timeout = settings.get("timeout", 20)
    api_key = settings.get("tempmail_api_key", "").strip()

    if not api_key:
        console.print(
            "[red]TEMPMAIL API Key tidak ditemukan di remote config GitHub.[/]"
        )
        return

    if not create_endpoint.get("enabled") or not create_endpoint.get("url"):
        console.print("[red]Endpoint Temp Mail Create belum tersedia.[/]")
        return

    if not inbox_endpoint.get("enabled") or not inbox_endpoint.get("url"):
        console.print("[red]Endpoint Temp Mail Inbox belum tersedia.[/]")
        return

    create_headers = {
        "Accept": "application/json",
        str(create_endpoint.get("auth_header", "X-API-Key")): api_key,
    }

    inbox_headers = {
        "Accept": "application/json",
        str(inbox_endpoint.get("auth_header", "X-API-Key")): api_key,
    }

    console.print("[bold bright_cyan]➤ Membuat email sementara...[/]")

    try:
        response = requests.get(
            create_endpoint["url"],
            headers=create_headers,
            timeout=timeout,
            allow_redirects=False,
        )

        if 300 <= response.status_code < 400:
            console.print("[red]Redirect ditolak untuk keamanan.[/]")
            return

        response.raise_for_status()

        try:
            payload = response.json()
        except ValueError:
            console.print("[red]Respons API bukan JSON yang valid.[/]")
            console.print(response.text[:2000])
            return

    except requests.exceptions.Timeout:
        console.print("[red]API timeout: server tidak merespons.[/]")
        return
    except requests.exceptions.ConnectionError:
        console.print("[red]Gagal terhubung ke server API.[/]")
        return
    except requests.exceptions.RequestException as exc:
        console.print(f"[red]Gagal membuat email: {exc}[/]")
        return

    mail_data = extract_temp_mail_data(payload)
    email = mail_data["email"]
    token = mail_data["token"]

    console.print(f"[bright_cyan]HTTP:[/] {response.status_code}")
    show_json(payload, "TEMP MAIL — CREATE")

    if not email:
        console.print(
            "[yellow]Alamat email tidak ditemukan otomatis dalam respons API.[/]"
        )
        email = Prompt.ask("Masukkan alamat email dari respons API").strip()

    if not token:
        console.print(
            "[yellow]Token tidak ditemukan otomatis dalam respons API.[/]"
        )
        token = Prompt.ask("Masukkan token dari respons API").strip()

    if not email or not token:
        console.print("[red]Email dan token wajib tersedia untuk cek inbox.[/]")
        return

    console.print()
    console.print("[bold bright_cyan]TEMP MAIL ACCOUNT[/]")
    console.print(f"[cyan]Email:[/] {email}")
    console.print(f"[cyan]Token:[/] {token}")

    check = Prompt.ask(
        "Periksa inbox sekarang?",
        choices=["y", "n"],
        default="y",
    )

    if check != "y":
        return

    try:
        with console.status("[bright_cyan]Memeriksa inbox...[/]"):
            response = requests.get(
                inbox_endpoint["url"],
                params={
                    "email": email,
                    "token": token,
                },
                headers=inbox_headers,
                timeout=timeout,
                allow_redirects=False,
            )

        if 300 <= response.status_code < 400:
            console.print("[red]Redirect ditolak untuk keamanan.[/]")
            return

        try:
            inbox_payload = response.json()
        except ValueError:
            inbox_payload = {"response": response.text[:5000]}

        result = {
            "ok": response.ok,
            "http_status": response.status_code,
            "email": email,
            "inbox": inbox_payload,
        }

        console.print(f"[bright_cyan]HTTP:[/] {response.status_code}")
        show_json(result, "TEMP MAIL — INBOX")

    except requests.exceptions.Timeout:
        console.print("[red]Inbox timeout: server tidak merespons.[/]")
    except requests.exceptions.ConnectionError:
        console.print("[red]Gagal terhubung ke server inbox.[/]")
    except requests.exceptions.RequestException as exc:
        console.print(f"[red]Gagal memeriksa inbox: {exc}[/]")


def main():
    try:
        settings = load_settings()
    except (RuntimeError, ValueError) as exc:
        console.print(f"[bold red]Config error:[/] {exc}")
        return

    while True:
        console.clear()
        banner()
        draw_device_info()
        draw_menu(settings)

        choice = Prompt.ask(
            "[bold bright_cyan]Pilih menu[/]",
            default="0",
        ).strip()

        if choice == "0":
            console.print("[bright_blue]Fluxx API closed.[/]")
            return

        selected = dict(MENU).get(choice)

        if not selected:
            console.print("[red]Pilihan tidak valid.[/]")
            Prompt.ask("Enter untuk kembali", default="")
            continue

        endpoint = settings["endpoints"].get(selected, {})

        console.print(
            Panel(
                endpoint.get("description", "API endpoint"),
                title=f"[bold cyan]{endpoint.get('label', selected)}[/]",
                border_style="bright_blue",
            )
        )

        if selected == "ngl_spammer":
            send_ngl(endpoint, settings)
            Prompt.ask("Enter untuk kembali ke menu", default="")
            continue

        if selected == "tempmail_create":
            run_temp_mail(settings)
            Prompt.ask("Enter untuk kembali ke menu", default="")
            continue

        if selected == "spotify_dl":
            find_spotify(endpoint, settings)
            Prompt.ask("Enter untuk kembali ke menu", default="")
            continue

        if selected == "ai_chat":
            send_ai_chat(endpoint, settings)
            Prompt.ask("Enter untuk kembali ke menu", default="")
            continue

        extra_variables = {}

        if selected == "react_saluran":
            key_value = Prompt.ask("Key").strip()
            channel_url = Prompt.ask("URL saluran").strip()
            reaction = Prompt.ask("Satu emoji reaksi").strip()

            if not key_value or not channel_url or not reaction:
                console.print("[red]Semua input wajib diisi.[/]")
                Prompt.ask("Enter untuk kembali", default="")
                continue

            if not channel_url.startswith("https://"):
                console.print(
                    "[red]URL saluran harus menggunakan HTTPS.[/]"
                )
                Prompt.ask("Enter untuk kembali", default="")
                continue

            extra_variables = {
                "key": key_value,
                "url": channel_url,
                "reaction": reaction,
            }
            query = ""

        elif selected == "find_airport":
            modes = endpoint.get("modes", {})

            for num, m in modes.items():
                console.print(f"[bright_cyan]{num}[/] {m['label']}")

            mode_choice = Prompt.ask(
                "[bold bright_cyan]Pilih jenis[/]",
                choices=list(modes),
                default="1",
            )
            mode = modes[mode_choice]

            values = {}
            for var, hint, example in mode["inputs"]:
                console.print(f"[bold bright_cyan]➤ {hint}[/]")
                console.print(f"[dim]  Contoh: {example}[/]")
                values[var] = Prompt.ask(
                    "[bold bright_cyan]╰›[/]",
                    default="",
                    show_default=False,
                ).strip()

            if not all(values.values()):
                console.print("[yellow]⚠ Input kosong, dibatalkan.[/]")
                Prompt.ask("[dim]Enter untuk kembali[/]", default="", show_default=False)
                continue

            endpoint = dict(endpoint)
            endpoint["url"] = mode["url"]
            endpoint["params"] = mode["params"]
            extra_variables = values
            query = " ".join(values.values())

        else:
            if endpoint.get("needs_input", True) is False:
                query = ""
            else:
                hint_data = INPUT_HINTS.get(selected)
                if isinstance(hint_data, (tuple, list)) and len(hint_data) >= 2:
                    hint, example = hint_data[0], hint_data[1]
                else:
                    hint, example = "Masukkan input sesuai API", ""
                hint = endpoint.get("input_hint", hint)
                example = endpoint.get("example", example)

                console.print(f"[bold bright_cyan]➤ {hint}[/]")
                if example:
                    console.print(f"[dim]  Contoh: {example}[/]")

                query = Prompt.ask(
                    "[bold bright_cyan]ㅤㅤ╰›[/]",
                    default="",
                    show_default=False,
                ).strip()

                if not query:
                    console.print("[yellow]⚠ Input kosong, dibatalkan.[/]")
                    Prompt.ask("[dim]Enter untuk kembali[/]", default="", show_default=False)
                    continue


        # Data NIK bersifat sensitif; konfirmasi izin tetap diwajibkan.
        if selected == "nik_detail":
            consent = Prompt.ask(
                "Lanjut? (yes/no)",
                choices=["yes", "no"],
                default="no",
            )

            if consent != "yes":
                console.print("[yellow]Dibatalkan.[/]")
                Prompt.ask("Enter untuk kembali", default="")
                continue


        if selected == "spotify_dl":
            find_spotify(endpoint, settings)
            Prompt.ask("Enter untuk kembali ke menu", default="")
            continue

        # Koordinat lat,lon memakai endpoint reverse geocoding (jika ada).
        if selected == "find_locate" and endpoint.get("reverse_url"):
            if re.fullmatch(r"-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?", query):
                endpoint = dict(endpoint)
                endpoint["url"] = endpoint["reverse_url"]
                query = query.replace(" ", "")

        try:
            result = request_api(
                endpoint,
                query,
                settings,
                extra_variables=extra_variables,
            )

            show_json(result, endpoint.get("label", "API RESULT"))

            # Laporan mengikuti konfigurasi yang ada di .env.
            send_report(
                menu=endpoint.get("label", selected),
                status="Successfully",
                target=query,
                result=result,
            )

            if Prompt.ask(
                "Simpan JSON ke output/? (y/n)",
                choices=["y", "n"],
                default="n",
            ) == "y":
                path = save_json(result, selected)
                console.print(
                    f"[green]JSON tersimpan:[/] "
                    f"{path.relative_to(path.parents[1])}"
                )

        except APIClientError as exc:
            error_result = {
                "ok": False,
                "error": str(exc),
            }

            show_json(error_result, "FLUXX ERROR")

            send_report(
                menu=endpoint.get("label", selected),
                status="API Error",
                target=query,
                result=error_result,
            )

        except KeyboardInterrupt:
            console.print("\n[yellow]Dibatalkan.[/]")

        Prompt.ask("Enter untuk kembali ke menu", default="")


if __name__ == "__main__":
    main()
