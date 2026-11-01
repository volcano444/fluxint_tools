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
    ("11", "ngl_spammer"),
    ("12", "find_npsn"),
    ("13", "get_contact"),
    ("14", "find_ff"),
    ("15", "find_ml"),
    ("16", "find_roblox"),
    ("17", "react_saluran"),
    ("18", "find_idol"),
    ("19", "find_nopol"),
    ("20", "find_locate"),
    ("21", "find_airport"),
]



INPUT_HINTS = {
    "weather": ("Masukkan nama kota atau daerah", "Jakarta"),
    "tiktok_spy": ("Masukkan username TikTok", "username"),
    "tiktok_downloader": ("Masukkan URL video TikTok", "https://vt.tiktok.com/xxxx"),
    "instagram_downloader": ("Masukkan URL postingan Instagram", "https://instagram.com/p/xxxx"),
    "find_lyrics": ("Masukkan judul lagu", "Sempurna"),
    "find_npsn": ("Masukkan nama sekolah", "SMAN 1 Mojang"),
    "find_ml": ("Masukkan ID dan Zone, pisahkan dengan |", "12345678|1234"),
    "find_idol": ("Masukkan nama artis atau tokoh", "Mrs. Brew"),
    "find_samsat": ("Masukkan plat nomor", "B 1234 XYZ"),
    "find_locate": ("Masukkan alamat, atau koordinat lat,lon", "Monas, Jakarta  atau  -6.1754,106.8272"),
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
                f"Key '{key_name}' belum diisi di file .env."
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

        if selected == "find_npsn":
            find_npsn(endpoint, query, settings)
            Prompt.ask("Enter untuk kembali ke menu", default="")
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
