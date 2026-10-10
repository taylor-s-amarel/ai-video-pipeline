import numpy as np

from flash_risk_screen import flash_events, relative_luminance, screen_frames, transitions


def strobe(fps, seconds, hz, size=(48, 64)):
    n = int(fps * seconds)
    frames = np.zeros((n, *size, 3), np.uint8)
    period = fps / hz
    for i in range(n):
        if (i % period) < period / 2:
            frames[i] = 255
    return frames


def test_luminance():
    assert relative_luminance(np.array([[[255, 255, 255]]], np.uint8))[0, 0] == 1.0


def test_fast_strobe_flagged():
    r = screen_frames(strobe(30, 2, 6), fps=30)
    assert r["risk"] and r["max_flashes_per_s"] >= 4


def test_slow_strobe_ok():
    r = screen_frames(strobe(30, 3, 1), fps=30)
    assert not r["risk"]


def test_small_changes_and_bright_flicker_ignored():
    s = np.array([0.5, 0.55, 0.5, 0.55, 0.5, 0.55])
    assert flash_events(s) == []
    bright = np.array([0.85, 1.0, 0.85, 1.0, 0.85, 1.0])  # darker state above 0.80
    assert flash_events(bright) == []
    assert transitions(np.array([0.0, 1.0, 0.0, 1.0, 0.0])) == [1, 2, 3, 4]
    assert len(flash_events(np.array([0.0, 1.0, 0.0, 1.0, 0.0]))) == 2
    # a slow ramp is one transition, not a flash
    assert len(transitions(np.linspace(0, 1, 30))) == 1
