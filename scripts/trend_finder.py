"""Find trending topics and videos to create content about."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.table import Table

console = Console()


def search_trending_videos(query: str, max_results: int = 10) -> list[dict]:
    """Search for trending videos on a topic using yt-dlp."""
    from src.acquisition.downloader import search_videos
    results = search_videos(query, max_results)
    return results


def _get_ai_suggestions(topic: str, num_ideas: int = 5) -> list[dict]:
    """Use AI to generate content ideas for a topic."""
    from src.utils.ai_client import ai_chat, parse_json_response

    prompt = f"""Generate {num_ideas} video content ideas for the topic: "{topic}"

Each idea should work as a commentary/analysis video. Return JSON:
{{
    "ideas": [
        {{
            "title": "Engaging video title",
            "angle": "Commentary angle — what unique perspective to take",
            "search_query": "YouTube search query to find source material",
            "estimated_appeal": "high|medium|low",
            "target_audience": "who this appeals to"
        }}
    ]
}}

Focus on:
- Controversy or debate potential
- Educational value
- Emotional engagement
- Trending relevance"""

    raw = ai_chat(prompt, max_tokens=2048, json_mode=True)
    data = parse_json_response(raw)
    return data.get("ideas", [])


@click.command()
@click.argument("topic")
@click.option("--ideas", "-n", default=5, help="Number of content ideas to generate.")
@click.option("--search/--no-search", default=True, help="Also search for source videos.")
@click.option("--output", "-o", default=None, help="Save results to JSON file.")
def find_trends(topic, ideas, search, output):
    """Find trending content and generate video ideas for a topic.

    Example: python scripts/trend_finder.py "artificial intelligence"
    """
    console.print(f"\n[bold]Researching: {topic}[/]\n")

    # Generate AI content ideas
    console.print("[dim]Generating content ideas...[/]")
    content_ideas = _get_ai_suggestions(topic, ideas)

    table = Table(title="Content Ideas")
    table.add_column("#", width=3)
    table.add_column("Title", max_width=50)
    table.add_column("Angle", max_width=40)
    table.add_column("Appeal")

    for i, idea in enumerate(content_ideas, 1):
        table.add_row(
            str(i),
            idea.get("title", ""),
            idea.get("angle", ""),
            idea.get("estimated_appeal", ""),
        )

    console.print(table)

    # Search for source videos
    source_videos = []
    if search:
        console.print("\n[dim]Searching for source videos...[/]")
        for idea in content_ideas[:3]:
            query = idea.get("search_query", topic)
            try:
                videos = search_trending_videos(query, max_results=3)
                source_videos.extend(videos)
            except Exception as e:
                console.print(f"[yellow]Search failed for '{query}': {e}[/]")

        if source_videos:
            vid_table = Table(title="Source Videos Found")
            vid_table.add_column("Title", max_width=60)
            vid_table.add_column("Duration")
            vid_table.add_column("URL", max_width=50)

            for v in source_videos[:10]:
                vid_table.add_row(
                    v.get("title", "")[:60],
                    str(v.get("duration", "N/A")),
                    v.get("url", v.get("webpage_url", "")),
                )
            console.print(vid_table)

    # Save results
    if output:
        results = {
            "topic": topic,
            "content_ideas": content_ideas,
            "source_videos": source_videos[:10],
        }
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\nSaved to: {output}")

    # Generate batch input file
    if source_videos:
        batch_entries = []
        for v in source_videos[:5]:
            url = v.get("url", v.get("webpage_url", ""))
            if url:
                batch_entries.append({
                    "url": url,
                    "name": v.get("title", "untitled")[:50].replace(" ", "_"),
                })

        batch_file = Path("output") / "batch_urls.json"
        batch_file.parent.mkdir(exist_ok=True)
        with open(batch_file, "w") as f:
            json.dump(batch_entries, f, indent=2)
        console.print(f"\nBatch file saved to: {batch_file}")
        console.print(f"Run: python scripts/batch_process.py {batch_file}")


if __name__ == "__main__":
    find_trends()
