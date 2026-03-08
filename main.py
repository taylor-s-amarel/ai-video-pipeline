"""CLI entry point for the AI Video Content Pipeline."""

import os
import sys
from pathlib import Path

# Fix Windows console encoding for Rich unicode output
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console

console = Console(force_terminal=True)


@click.group()
def cli():
    """AI Video Content Pipeline — Transform source videos into monetizable content."""
    pass


@cli.command()
@click.argument("url")
@click.option("--platform", "-p", default="youtube",
              type=click.Choice(["youtube", "shorts", "tiktok", "reels", "twitter"]),
              help="Target platform for export format.")
@click.option("--name", "-n", default=None, help="Output project name.")
@click.option("--no-thumbnail", is_flag=True, help="Skip thumbnail generation.")
@click.option("--upload", is_flag=True, help="Prepare upload package.")
@click.option("--music", "-m", default=None, help="Path to background music file.")
@click.option("--captions", "-c", default="word_highlight",
              type=click.Choice(["word_highlight", "karaoke", "sentence"]),
              help="Caption style.")
def generate(url, platform, name, no_thumbnail, upload, music, captions):
    """Generate a commentary video from a source URL.

    Example: python main.py generate "https://youtube.com/watch?v=..."
    """
    from src.pipeline import run_pipeline

    result = run_pipeline(
        source_url=url,
        platform=platform,
        output_name=name,
        skip_thumbnail=no_thumbnail,
        skip_upload=not upload,
        background_music_path=music,
        caption_mode=captions,
    )

    if result.errors:
        console.print(f"\n[yellow]Completed with {len(result.errors)} error(s)[/]")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--output", "-o", default="./output/downloads", help="Output directory.")
def download(url, output):
    """Download a video without processing."""
    from src.acquisition.downloader import download_video
    result = download_video(url, output)
    console.print(f"Downloaded: {result.title}")
    console.print(f"File: {result.file_path}")
    console.print(f"Duration: {result.duration:.1f}s")


@cli.command()
@click.argument("file_path")
@click.option("--model", "-m", default="base",
              type=click.Choice(["tiny", "base", "small", "medium", "large"]),
              help="Whisper model size.")
@click.option("--output", "-o", default=None, help="Output JSON path.")
def transcribe(file_path, model, output):
    """Transcribe a video or audio file."""
    from src.analysis.transcriber import transcribe as do_transcribe
    result = do_transcribe(file_path, model_size=model)
    console.print(f"Language: {result.language}")
    console.print(f"Duration: {result.duration:.1f}s")
    console.print(f"Segments: {len(result.segments)}")
    console.print(f"\n{result.text[:500]}...")

    if output:
        result.save(output)
        console.print(f"\nSaved to: {output}")


@cli.command()
@click.argument("text")
@click.option("--output", "-o", default="./output/tts_output.mp3", help="Output path.")
@click.option("--provider", default=None,
              type=click.Choice(["edge-tts", "elevenlabs"]),
              help="TTS provider.")
def speak(text, output, provider):
    """Generate speech from text."""
    from src.transformation.tts import generate_speech
    result = generate_speech(text, output, provider)
    console.print(f"Audio: {result.audio_path}")
    console.print(f"Duration: {result.duration:.1f}s")


@cli.command()
@click.argument("file_path")
@click.option("--model", "-m", default="base", help="Whisper model size.")
@click.option("--style", default="word_highlight",
              type=click.Choice(["word_highlight", "karaoke", "sentence"]),
              help="Caption style.")
@click.option("--output", "-o", default=None, help="Output ASS file path.")
def captions(file_path, model, style, output):
    """Generate captions for a video or audio file."""
    from src.analysis.transcriber import transcribe as do_transcribe
    from src.transformation.captions import generate_captions_ass

    transcript = do_transcribe(file_path, model_size=model)
    output = output or str(Path(file_path).with_suffix(".ass"))
    generate_captions_ass(transcript, output, mode=style)
    console.print(f"Captions saved to: {output}")


@cli.command()
@click.argument("file_path")
@click.option("--start", "-s", type=float, required=True, help="Start time in seconds.")
@click.option("--end", "-e", type=float, required=True, help="End time in seconds.")
@click.option("--output", "-o", default=None, help="Output file path.")
def clip(file_path, start, end, output):
    """Extract a clip from a video."""
    from src.utils.ffmpeg_utils import clip_video
    output = output or f"clip_{start:.0f}_{end:.0f}.mp4"
    result = clip_video(file_path, output, start, end)
    console.print(f"Clip saved to: {result}")


@cli.command()
def check_deps():
    """Check that all required dependencies are available."""
    import shutil

    deps = {
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "yt-dlp": shutil.which("yt-dlp"),
    }

    for name, path in deps.items():
        if path:
            console.print(f"  [green]OK[/] {name}: {path}")
        else:
            console.print(f"  [red]MISSING[/] {name}")

    # Check Python packages
    packages = [
        "faster_whisper", "anthropic", "openai", "edge_tts",
        "elevenlabs", "pysubs2", "rich", "click", "pydantic",
    ]

    for pkg in packages:
        try:
            __import__(pkg)
            console.print(f"  [green]OK[/] {pkg}")
        except ImportError:
            console.print(f"  [red]MISSING[/] {pkg} — pip install {pkg}")


@cli.command()
def providers():
    """List all available AI and image generation providers."""
    from src.utils.ai_client import list_providers
    from src.utils.image_gen import list_image_providers
    from config.settings import settings

    console.print("\n[bold]LLM Providers:[/]")
    console.print(f"  Active: [cyan]{settings.ai_provider}[/] (model: {settings.ai_model})")
    for name, available in list_providers().items():
        status = "[green]ready[/]" if available else "[dim]no key[/]"
        console.print(f"  {status}  {name}")

    console.print(f"\n[bold]Image Providers:[/]")
    console.print(f"  Active: [cyan]{settings.image_provider}[/]")
    for name, available in list_image_providers().items():
        status = "[green]ready[/]" if available else "[dim]no key[/]"
        console.print(f"  {status}  {name}")

    console.print(f"\n[dim]Change with AI_PROVIDER= and IMAGE_PROVIDER= in .env[/]")


@cli.command()
def init():
    """Initialize the project — create directories and .env file."""
    from config.settings import settings

    dirs = [
        settings.output_dir / "videos",
        settings.output_dir / "thumbnails",
        settings.output_dir / "metadata",
        settings.output_dir / "projects",
        settings.assets_dir / "fonts",
        settings.assets_dir / "sounds",
        settings.assets_dir / "music",
        settings.temp_dir,
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        console.print(f"  Created: {d}")

    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        example = Path(__file__).parent / ".env.example"
        if example.exists():
            import shutil
            shutil.copy2(example, env_file)
            console.print(f"  Created .env from .env.example — edit with your API keys")
        else:
            console.print(f"  [yellow].env.example not found[/]")

    console.print("\n[green]Project initialized![/] Edit .env with your API keys.")


if __name__ == "__main__":
    cli()
