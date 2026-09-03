# YouTube Subtitle Cleaner

Small Python utility functions for cleaning YouTube VTT/SRT subtitle text for downstream processing.

This package is intentionally narrow:

- Remove inline VTT timestamps and simple caption tags.
- Optionally remove bracketed sound labels such as `[music]`.
- Parse SRT cue blocks.
- Drop duplicate or too-short cues.
- Return cleaned SRT text and structured segment dictionaries.

It does not download YouTube videos, call external APIs, run ASR, read cookies, or require tokens.

## Install

```bash
python -m pip install -e .
```

## Usage

```python
from youtube_subtitle_cleaner import finalize_srt_machine_readable

srt_text = """
1
00:00:01,000 --> 00:00:02,000
<c>Hello</c>

2
00:00:02,000 --> 00:00:03,000
Hello

3
00:00:04,000 --> 00:00:05,000
[music] World
"""

cleaned_srt, segments = finalize_srt_machine_readable(
    srt_text,
    bracket_sound_policy="remove",
)

print(cleaned_srt)
print(segments)
```

## API

| Function | Purpose |
| --- | --- |
| `clean_subtitle_plain_text(text, bracket_sound_policy)` | Clean raw cue text. |
| `parse_srt_entries(srt_text)` | Parse numbered SRT cue blocks. |
| `finalize_srt_machine_readable(srt_text, bracket_sound_policy)` | Clean, dedupe, and return SRT plus segments. |
| `normalize_text_for_dedupe(text)` | Collapse whitespace before duplicate checks. |
| `srt_ts_to_seconds(timestamp)` | Convert `HH:MM:SS,mmm` to seconds. |

## Tests

```bash
python -m pytest
```

The tests use only dummy subtitle text. Do not add real YouTube subtitles, transcripts, downloaded media, cookies, logs, or tokens to this repository.

## Publication Notes

Keep this repository limited to code, tests, README, license, and dummy examples.

Do not include:

- Real YouTube subtitle files or transcripts.
- Downloaded video or audio.
- ASR, OCR, or HTML report outputs.
- `.env`, cookies, tokens, credentials, or logs.
- `__pycache__`, `.venv`, or AppleDouble `._*` files.
