"""Batch processing — generate videos from a list of URLs or topics."""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.table import Table

from src.pipeline import run_pipeline

console = Console()


@click.command()
@click.argument("input_file")
@click.option("--platform", "-p", default="youtube",
              type=click.Choice(["youtube", "shorts", "tiktok", "reels"]))
@click.option("--delay", "-d", default=30, help="Delay between videos in seconds.")
@click.option("--max-videos", "-n", default=None, type=int, help="Max videos to process.")
@click.option("--captions", "-c", default="word_highlight",
              type=click.Choice(["word_highlight", "karaoke", "sentence"]))
def batch(input_file, platform, delay, max_videos, captions):
    """Process multiple videos from a JSON file.

    Input file format (urls.json):
    [
        {"url": "https://...", "name": "optional_name"},
        {"url": "https://...", "name": "video_2"}
    ]
    """
    with open(input_file) as f:
        entries = json.load(f)

    if max_videos:
        entries = entries[:max_videos]

    results = []
    total = len(entries)

    for i, entry in enumerate(entries, 1):
        url = entry["url"]
        name = entry.get("name", f"batch_{i:03d}")

        console.print(f"\n[bold]═══ Video {i}/{total}: {name} ═══[/]")

        try:
            result = run_pipeline(
                source_url=url,
                platform=platform,
                output_name=name,
                skip_thumbnail=False,
                skip_upload=True,
                caption_mode=captions,
            )
            results.append({
                "name": name,
                "url": url,
                "status": "success" if not result.errors else "partial",
                "video": str(result.video_path) if result.video_path else None,
                "duration": result.duration,
                "fair_use_score": result.fair_use_score,
                "errors": result.errors,
            })
        except Exception as e:
            results.append({
                "name": name,
                "url": url,
                "status": "failed",
                "error": str(e),
            })

        if i < total:
            console.print(f"[dim]Waiting {delay}s before next video...[/]")
            time.sleep(delay)

    # Summary table
    console.print("\n[bold]═══ Batch Summary ═══[/]")
    table = Table()
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Duration")
    table.add_column("Fair Use")

    for r in results:
        status_color = "green" if r["status"] == "success" else "yellow" if r["status"] == "partial" else "red"
        table.add_row(
            r["name"],
            f"[{status_color}]{r['status']}[/]",
            f"{r.get('duration', 0):.1f}s",
            str(r.get("fair_use_score", "N/A")),
        )

    console.print(table)

    # Save results
    results_path = Path("output") / "batch_results.json"
    results_path.parent.mkdir(exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    batch()
