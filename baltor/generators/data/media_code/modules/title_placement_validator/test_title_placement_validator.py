from title_placement_validator import check, suggest_title_box

FRAME = (1080, 1920)
PHOTO = (54, 220, 972, 1300)


def rules(f):
    return {x["rule"] for x in f}


def test_compliant_layout_passes():
    assert check(FRAME, (90, 300, 900, 260), PHOTO, reference_photo=PHOTO) == []


def test_title_too_low():
    # the earlier mistake: title centre at 65% of the height
    assert "title_upper" in rules(check(FRAME, (90, 1118, 900, 260), PHOTO))


def test_shrunk_photo_and_not_over_photo():
    small = (240, 900, 600, 800)
    r = rules(check(FRAME, (90, 300, 900, 260), small, reference_photo=PHOTO))
    assert {"title_over_photo", "photo_width", "photo_not_shrunk"} <= r


def test_margins_and_size():
    r = rules(check(FRAME, (0, 10, 1080, 40), PHOTO))
    assert {"title_margins", "title_size"} <= r


def test_suggestion_is_compliant():
    box = suggest_title_box(FRAME, PHOTO, (900, 260))
    assert check(FRAME, box, PHOTO, reference_photo=PHOTO) == []
