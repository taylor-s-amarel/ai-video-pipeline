import xml.etree.ElementTree as ET

import pytest

from ssml_builder import brk, emphasis, phoneme, prosody, say_as, speak, strip_ssml, sub


def test_document_is_wellformed():
    doc = speak(["In ", say_as("1970", "date", format="y"), ", ", emphasis("five"), " scientists & divers",
                 brk("400ms"), prosody("lived <underwater>.", rate="90%", pitch="-2st", volume="+3dB"),
                 sub("NOAA", "Noah"), phoneme("tomato", "təˈmeɪtoʊ")])
    root = ET.fromstring(doc)
    assert root.tag.endswith("speak") and root.get("version") == "1.1"
    assert "&amp; divers" in doc and "&lt;underwater&gt;" in doc


def test_strip():
    doc = speak(["Hi", brk(strength="strong"), sub("NOAA", "Noah"), " & bye"])
    assert strip_ssml(doc) == "Hi Noah & bye"


@pytest.mark.parametrize("call", [lambda: brk("5 sec"), lambda: brk(strength="huge"), lambda: prosody("x", rate="-5%"),
                                  lambda: prosody("x", pitch="up"), lambda: prosody("x", volume="3dB"),
                                  lambda: emphasis("x", "max"), lambda: phoneme("x", "y", "arpabet"),
                                  lambda: speak("x", lang="english"), lambda: say_as("x", "Date")])
def test_validation(call):
    with pytest.raises(ValueError):
        call()
