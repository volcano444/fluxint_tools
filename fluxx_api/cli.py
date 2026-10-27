import os
import platform
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
    ("1", "url_mirroring"),
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
]


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

def banner():
    art = r"""
███████╗██╗     ██╗   ██╗██╗  ██╗██╗  ██╗██╗███╗   ██╗████████╗
██╔════╝██║     ██║   ██║╚██╗██╔╝╚██╗██╔╝██║████╗  ██║╚══██╔══╝
█████╗  ██║     ██║   ██║ ╚███╔╝  ╚███╔╝ ██║██╔██╗ ██║   ██║
██╔══╝  ██║     ██║   ██║ ██╔██╗  ██╔██╗ ██║██║╚██╗██║   ██║
██║     ███████╗╚██████╔╝██╔╝ ██╗██╔╝ ██╗██║██║ ╚████║   ██║
╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝   ╚═╝
"""
    console.print(
        Align.center(
            Text(art, style="bold bright_blue")
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


def find_npsn(endpoint, query, settings):
    """Cari sekolah, pilih NPSN, lalu ambil detail sekolah."""
    search_url = endpoint["url"]
    detail_url = endpoint["detail_url"]
    timeout = settings["timeout"]

    try:
        response = requests.get(
            search_url,
            params={"q": query},
            headers={"Accept": "application/json"},
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
            headers={"Accept": "application/json"},
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
            usr = endpoint["usr"]
            text = endpoint["text"]
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

        else:
            query = Prompt.ask(
                "Input (URL/kota/kata kunci sesuai API)",
                default="",
            ).strip()

            if not query:
                console.print(
                    "[yellow]Input kosong, dibatalkan.[/]"
                )
                Prompt.ask("Enter untuk kembali", default="")
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
