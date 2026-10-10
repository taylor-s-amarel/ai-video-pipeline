import mp4_qa_probe as m


def info(duration=64.0, w=1080, h=1920, audio=True):
    streams = [{"codec_type": "video", "width": w, "height": h, "codec_name": "h264", "pix_fmt": "yuv420p"}]
    if audio:
        streams.append({"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000"})
    return {"streams": streams, "format": {"duration": str(duration), "format_name": "mov,mp4,m4a,3gp,3g2,mj2"}}


def test_full_length_vertical_video_passes():
    assert all(c.passed for c in m.evaluate(info()))


def test_short_preview_fails_duration():
    checks = {c.name: c for c in m.evaluate(info(duration=6.0))}
    assert not checks["duration"].passed


def test_missing_audio_fails():
    checks = {c.name: c for c in m.evaluate(info(audio=False))}
    assert not checks["audio_stream"].passed


def test_wrong_resolution_fails():
    checks = {c.name: c for c in m.evaluate(info(w=1920, h=1080))}
    assert not checks["resolution"].passed
