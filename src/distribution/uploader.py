"""Upload videos to YouTube, TikTok, and other platforms."""

import json
from pathlib import Path
from dataclasses import dataclass

from config.settings import settings
from src.assembly.metadata import VideoMetadata


@dataclass
class UploadResult:
    platform: str
    video_id: str
    url: str
    status: str


def upload_to_youtube(video_path: str | Path, metadata: VideoMetadata,
                       privacy: str = "private",
                       schedule_time: str | None = None) -> UploadResult:
    """Upload video to YouTube using the Data API v3.

    Requires OAuth2 credentials. Set privacy to 'private' for review before publishing.
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    # Load credentials (assumes OAuth flow has been completed)
    creds_path = Path(settings.output_dir) / ".youtube_credentials.json"
    if not creds_path.exists():
        raise FileNotFoundError(
            f"YouTube credentials not found at {creds_path}. "
            "Run 'python scripts/youtube_auth.py' to authenticate."
        )

    with open(creds_path) as f:
        creds_data = json.load(f)

    credentials = Credentials.from_authorized_user_info(creds_data)
    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": metadata.title[:100],
            "description": metadata.youtube_description()[:5000],
            "tags": metadata.tags[:500],
            "categoryId": _get_category_id(metadata.category),
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    if schedule_time and privacy == "private":
        body["status"]["publishAt"] = schedule_time

    media = MediaFileUpload(
        str(video_path), mimetype="video/mp4", resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = request.execute()
    video_id = response["id"]

    return UploadResult(
        platform="youtube",
        video_id=video_id,
        url=f"https://youtube.com/watch?v={video_id}",
        status=privacy,
    )


def _get_category_id(category: str) -> str:
    categories = {
        "Education": "27",
        "Science & Technology": "28",
        "Entertainment": "24",
        "News & Politics": "25",
        "People & Blogs": "22",
        "Comedy": "23",
        "Howto & Style": "26",
        "Gaming": "20",
    }
    return categories.get(category, "22")


def upload_to_tiktok(video_path: str | Path, metadata: VideoMetadata) -> UploadResult:
    """Upload video to TikTok using the Content Posting API.

    Requires TikTok API app credentials and OAuth access token.
    """
    import httpx

    # Step 1: Initialize upload
    init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
    headers = {
        "Authorization": f"Bearer {settings.tiktok_session_id if hasattr(settings, 'tiktok_session_id') else ''}",
        "Content-Type": "application/json",
    }

    init_body = {
        "post_info": {
            "title": metadata.tiktok_description(),
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": Path(video_path).stat().st_size,
        },
    }

    resp = httpx.post(init_url, json=init_body, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    upload_url = data["data"]["upload_url"]
    publish_id = data["data"]["publish_id"]

    # Step 2: Upload video file
    with open(video_path, "rb") as f:
        upload_resp = httpx.put(
            upload_url,
            content=f.read(),
            headers={"Content-Type": "video/mp4"},
        )
        upload_resp.raise_for_status()

    return UploadResult(
        platform="tiktok",
        video_id=publish_id,
        url=f"https://tiktok.com/@user/video/{publish_id}",
        status="published",
    )


def save_for_manual_upload(video_path: str | Path, metadata: VideoMetadata,
                            platform: str, output_dir: str | Path) -> Path:
    """Save video and metadata for manual upload."""
    output_dir = Path(output_dir) / platform
    output_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    # Copy video
    dest_video = output_dir / Path(video_path).name
    shutil.copy2(video_path, dest_video)

    # Save metadata
    metadata.save(output_dir / "metadata.json")

    # Save description as text file for easy copy-paste
    desc_file = output_dir / "description.txt"
    if platform == "youtube":
        desc_file.write_text(metadata.youtube_description(), encoding="utf-8")
    elif platform == "tiktok":
        desc_file.write_text(metadata.tiktok_description(), encoding="utf-8")
    else:
        desc_file.write_text(metadata.description, encoding="utf-8")

    return output_dir
