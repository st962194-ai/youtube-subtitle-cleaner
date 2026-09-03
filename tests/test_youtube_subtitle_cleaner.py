import pytest

from youtube_subtitle_cleaner import (
    clean_subtitle_plain_text,
    finalize_srt_machine_readable,
    normalize_text_for_dedupe,
    parse_srt_entries,
    srt_ts_to_seconds,
)


def test_clean_subtitle_plain_text_removes_vtt_tags_and_position_noise():
    raw = """
    <c.colorCCCCCC>Hello</c> <00:00:01.200>world
    align:start position:0%
    [music]
    """

    assert clean_subtitle_plain_text(raw, bracket_sound_policy="remove") == "Hello world"


def test_clean_subtitle_plain_text_can_keep_bracket_sound_labels():
    raw = "<c>Hello</c>\n[applause]"

    assert clean_subtitle_plain_text(raw, bracket_sound_policy="keep") == "Hello [applause]"


def test_parse_srt_entries_accepts_numbered_blocks_and_ignores_invalid_blocks():
    srt_text = """
1
00:00:01,000 --> 00:00:02,000
Hello

not a cue
ignored

2
00:00:03,000 --> 00:00:04,000
World
"""

    assert parse_srt_entries(srt_text) == [
        ("00:00:01,000", "00:00:02,000", "Hello"),
        ("00:00:03,000", "00:00:04,000", "World"),
    ]


def test_finalize_srt_machine_readable_removes_duplicate_and_too_short_cues():
    srt_text = """
1
00:00:01,000 --> 00:00:02,000
<c>Hello</c>

2
00:00:02,000 --> 00:00:03,000
Hello

3
00:00:03,000 --> 00:00:03,005
Too short

4
00:00:04,000 --> 00:00:05,000
[music] World
"""

    cleaned, segments = finalize_srt_machine_readable(
        srt_text,
        bracket_sound_policy="remove",
    )

    assert "Too short" not in cleaned
    assert cleaned == (
        "1\n"
        "00:00:01,000 --> 00:00:02,000\n"
        "Hello\n\n"
        "2\n"
        "00:00:04,000 --> 00:00:05,000\n"
        "World\n"
    )
    assert segments == [
        {
            "start": "00:00:01,000",
            "end": "00:00:02,000",
            "start_sec": 1.0,
            "end_sec": 2.0,
            "text": "Hello",
        },
        {
            "start": "00:00:04,000",
            "end": "00:00:05,000",
            "start_sec": 4.0,
            "end_sec": 5.0,
            "text": "World",
        },
    ]


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("00:00:00,000", 0.0),
        ("00:01:02,345", 62.345),
        ("01:00:00,000", 3600.0),
    ],
)
def test_srt_ts_to_seconds(timestamp, expected):
    assert srt_ts_to_seconds(timestamp) == expected


def test_normalize_text_for_dedupe_collapses_spaces():
    assert normalize_text_for_dedupe("  Hello   world  ") == "Hello world"
