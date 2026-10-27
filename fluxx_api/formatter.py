import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def show_json(data, title="API RESULT"):
    rendered = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    syntax = Syntax(rendered, "json", theme="monokai", line_numbers=True, word_wrap=True)
    console.print(Panel(syntax, title=f"[bold cyan]{title}[/]", border_style="bright_blue"))
    return rendered


def save_json(data, slug="result"):
    output_dir = Path(__file__).resolve().parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{slug}_{stamp}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
