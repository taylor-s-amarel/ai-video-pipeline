"""Main pipeline orchestrator — coordinates all stages from URL to final video."""

import json
import shutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import settings
from src.utils.fair_use import FairUseCheck, check_video_fair_use

console = Console()


@dataclass
class PipelineResult:
    video_path: Path | None = None
    thumbnail_path: Path | None = None
    metadata_path: Path | None = None
    title: str = ""
    duration: float = 0.0
    fair_use_score: int = 0
    platform: str = ""
    errors: list[str] = field(default_factory=list)
    stages_completed: list[str] = field(default_factory=list)


def run_pipeline(
    source_url: str,
    platform: str = "youtube",
    output_name: str | None = None,
    skip_thumbnail: bool = False,
    skip_upload: bool = True,
    background_music_path: str | None = None,
    caption_mode: str = "word_highlight",
) -> PipelineResult:
    """Run the full video pipeline from source URL to finished video.

    Stages:
    1. Download source
    2. Transcribe
    3. Analyze content (AI)
    4. Extract clips
    5. Generate commentary script (AI)
    6. Generate TTS narration
    7. Transcribe narration for captions
    8. Generate captions
    9. Compose final video
    10. Generate thumbnail
    11. Generate metadata
    12. Fair use compliance check
    13. Upload (optional)
    """
    result = PipelineResult(platform=platform)

    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = output_name or timestamp
    project_dir = Path(settings.output_dir) / "projects" / output_name
    project_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = project_dir / "temp"
    temp_dir.mkdir(exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # ── Stage 1: Download ──
        task = progress.add_task("Downloading source video...", total=None)
        try:
            from src.acquisition.downloader import download_video
            dl = download_video(source_url, temp_dir / "source")
            console.print(f"  Downloaded: [cyan]{dl.title}[/] ({dl.duration:.0f}s)")
            result.stages_completed.append("download")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"Download failed: {e}")
            console.print(f"[red]Download failed: {e}[/]")
            return result

        # ── Stage 2: Transcribe ──
        task = progress.add_task("Transcribing audio...", total=None)
        try:
            from src.analysis.transcriber import transcribe
            transcript = transcribe(dl.file_path, model_size=settings.whisper_model)
            transcript.save(project_dir / "transcript.json")
            console.print(f"  Transcribed: {len(transcript.segments)} segments, "
                         f"language={transcript.language}")
            result.stages_completed.append("transcribe")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"Transcription failed: {e}")
            console.print(f"[red]Transcription failed: {e}[/]")
            return result

        # ── Stage 3: Analyze ──
        task = progress.add_task("Analyzing content with AI...", total=None)
        try:
            from src.analysis.content_analyzer import analyze_content
            analysis = analyze_content(transcript, title=dl.title, creator=dl.uploader)
            console.print(f"  Found {len(analysis.clip_suggestions)} clip candidates")
            console.print(f"  Topics: {', '.join(analysis.topics[:5])}")
            result.stages_completed.append("analyze")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"Analysis failed: {e}")
            console.print(f"[red]Analysis failed: {e}[/]")
            return result

        # ── Stage 4: Extract Clips ──
        task = progress.add_task("Extracting clips...", total=None)
        try:
            from src.clipping.clipper import extract_clips
            clips = extract_clips(
                dl.file_path, analysis.clip_suggestions,
                temp_dir / "clips", max_clips=5,
            )
            console.print(f"  Extracted {len(clips)} clips")
            result.stages_completed.append("clip")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"Clipping failed: {e}")
            console.print(f"[red]Clipping failed: {e}[/]")
            return result

        # ── Stage 5: Generate Commentary ──
        task = progress.add_task("Generating commentary script...", total=None)
        try:
            from src.transformation.commentary import generate_commentary
            used_suggestions = analysis.clip_suggestions[:len(clips)]
            script = generate_commentary(analysis, used_suggestions)
            result.title = script.title
            console.print(f"  Script: \"{script.title}\"")
            console.print(f"  Commentary duration: ~{script.total_commentary_duration:.0f}s")
            result.stages_completed.append("commentary")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"Commentary generation failed: {e}")
            console.print(f"[red]Commentary failed: {e}[/]")
            return result

        # ── Stage 6: Generate TTS ──
        task = progress.add_task("Generating voiceover...", total=None)
        try:
            from src.transformation.tts import generate_speech
            tts_dir = temp_dir / "tts"
            tts_dir.mkdir(exist_ok=True)

            # Generate hook
            tts_segments = []
            hook_tts = generate_speech(script.hook, tts_dir / "hook.mp3")
            tts_segments.append(hook_tts)

            # Generate each commentary segment
            for i, seg in enumerate(script.segments):
                seg_tts = generate_speech(seg.text, tts_dir / f"segment_{i:03d}.mp3")
                tts_segments.append(seg_tts)

            # Generate outro
            outro_tts = generate_speech(script.outro, tts_dir / "outro.mp3")
            tts_segments.append(outro_tts)

            total_tts_duration = sum(t.duration for t in tts_segments)
            console.print(f"  Generated {len(tts_segments)} audio segments "
                         f"({total_tts_duration:.1f}s total)")
            result.stages_completed.append("tts")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"TTS failed: {e}")
            console.print(f"[red]TTS failed: {e}[/]")
            return result

        # ── Stage 7: Generate captions from TTS text ──
        task = progress.add_task("Generating captions...", total=None)
        try:
            from src.transformation.captions import generate_captions_ass
            from src.transformation.tts import tts_to_transcript

            # Build transcript from TTS results (no re-transcription needed)
            narration_transcript = tts_to_transcript(tts_segments)

            # Generate ASS captions
            caption_file = project_dir / "captions.ass"
            generate_captions_ass(
                narration_transcript, caption_file, mode=caption_mode
            )
            console.print(f"  Captions generated: {caption_mode} mode")
            result.stages_completed.append("captions")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"Caption generation failed: {e}")
            console.print(f"[yellow]Captions failed (continuing): {e}[/]")
            caption_file = None

        # ── Stage 8: Compose Final Video ──
        task = progress.add_task("Composing final video...", total=None)
        try:
            from src.assembly.composer import compose_commentary_video

            final_video_path = project_dir / f"final_{platform}.mp4"

            music_path = Path(background_music_path) if background_music_path else None

            video = compose_commentary_video(
                commentary_audio_segments=[t.audio_path for t in tts_segments],
                source_clips=[c.file_path for c in clips],
                caption_file=caption_file,
                background_music=music_path,
                output_path=final_video_path,
                platform=platform,
            )

            result.video_path = video.file_path
            result.duration = video.duration
            console.print(f"  Final video: {video.duration:.1f}s, "
                         f"{video.width}x{video.height}")
            result.stages_completed.append("compose")
            progress.update(task, completed=True)
        except Exception as e:
            stderr = getattr(e, 'stderr', '') or ''
            msg = f"Composition failed: {e}"
            if stderr:
                msg += f"\nffmpeg stderr: {stderr[:500]}"
            result.errors.append(msg)
            console.print(f"[red]{msg}[/]")
            return result

        # ── Stage 9: Generate Thumbnail ──
        if not skip_thumbnail:
            task = progress.add_task("Generating thumbnail...", total=None)
            try:
                from src.assembly.thumbnail import generate_thumbnail
                thumb = generate_thumbnail(
                    title=script.title,
                    prompt=f"{', '.join(analysis.topics[:3])} content",
                    output_dir=project_dir / "thumbnails",
                    subtitle=dl.uploader,
                )
                result.thumbnail_path = thumb.file_path
                console.print(f"  Thumbnail: {thumb.width}x{thumb.height}")
                result.stages_completed.append("thumbnail")
                progress.update(task, completed=True)
            except Exception as e:
                result.errors.append(f"Thumbnail failed: {e}")
                console.print(f"[yellow]Thumbnail failed (continuing): {e}[/]")
        else:
            console.print("  [dim]Skipping thumbnail generation[/]")

        # ── Stage 10: Generate Metadata ──
        task = progress.add_task("Generating metadata...", total=None)
        try:
            from src.assembly.metadata import generate_metadata
            metadata = generate_metadata(
                title=script.title,
                summary=analysis.summary,
                topics=analysis.topics,
                source_creators=[{"creator": dl.uploader, "url": source_url}],
            )
            metadata_path = project_dir / "metadata.json"
            metadata.save(metadata_path)
            result.metadata_path = metadata_path
            console.print(f"  Metadata saved: {metadata.title}")
            result.stages_completed.append("metadata")
            progress.update(task, completed=True)
        except Exception as e:
            result.errors.append(f"Metadata generation failed: {e}")
            console.print(f"[yellow]Metadata failed (continuing): {e}[/]")

        # ── Stage 11: Fair Use Check ──
        task = progress.add_task("Running fair use compliance check...", total=None)
        total_clip_duration = sum(c.end - c.start for c in clips)
        fu_checks = [
            FairUseCheck(
                source_path=str(dl.file_path),
                clip_start=c.start,
                clip_end=c.end,
                has_commentary=True,
                has_visual_transform=caption_file is not None,
                has_attribution=True,
                commentary_duration=script.total_commentary_duration / max(len(clips), 1),
                source_purpose="entertainment",
                output_purpose="commentary and analysis",
            )
            for c in clips
        ]
        fu_result = check_video_fair_use(fu_checks)
        result.fair_use_score = fu_result.score

        if fu_result.passed:
            console.print(f"  [green]Fair use check PASSED[/] (score: {fu_result.score}/100)")
        else:
            console.print(f"  [red]Fair use check FAILED[/] (score: {fu_result.score}/100)")
            for issue in fu_result.issues:
                console.print(f"    [red]- {issue}[/]")
        for warn in fu_result.warnings:
            console.print(f"    [yellow]- {warn}[/]")

        result.stages_completed.append("fair_use_check")
        progress.update(task, completed=True)

        # ── Stage 12: Upload (optional) ──
        if not skip_upload and result.video_path:
            task = progress.add_task("Preparing for upload...", total=None)
            try:
                from src.distribution.uploader import save_for_manual_upload
                if metadata:
                    upload_dir = save_for_manual_upload(
                        result.video_path, metadata, platform,
                        project_dir / "upload_ready",
                    )
                    console.print(f"  Upload package saved to: {upload_dir}")
                result.stages_completed.append("upload_prep")
                progress.update(task, completed=True)
            except Exception as e:
                result.errors.append(f"Upload prep failed: {e}")

    # ── Cleanup temp files ──
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

    # ── Summary ──
    console.print()
    console.print(Panel.fit(
        f"[bold green]Pipeline Complete![/]\n\n"
        f"Title: {result.title}\n"
        f"Video: {result.video_path}\n"
        f"Duration: {result.duration:.1f}s\n"
        f"Fair Use Score: {result.fair_use_score}/100\n"
        f"Stages: {len(result.stages_completed)}/{12}\n"
        f"Errors: {len(result.errors)}",
        title="Pipeline Result",
    ))

    return result
