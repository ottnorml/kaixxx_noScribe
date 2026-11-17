# Getting started (macOS, Apple Silicon)

How to set up and run this noScribe fork locally on macOS. Tested on macOS 26
/ Apple M1 Pro with Python 3.14 (uv). For general user-facing documentation
see <https://noscribe.de>; this guide covers the local setup of the macOS
port.

## Requirements

- macOS on Apple Silicon (M1 or newer); tested with 16 GB RAM
- ~10 GB free disk space (environment ~3 GB, models ~3.5 GB)
- [uv](https://docs.astral.sh/uv/) (`brew install uv`)

## 1. Create the environment

Use a **uv-managed Python** (3.14). Do not use Homebrew's Python: it does not
ship `_tkinter`, so the GUI cannot start.

```bash
cd noScribe
uv python install 3.14
rm -rf .venv            # only if a stale venv exists
uv venv --python 3.14
# The fastapi/uvicorn lines are only needed for server mode; skip them for a
# minimal desktop setup:
grep -vE '^(fastapi|uvicorn)' environments/requirements_macOS_arm64.txt | uv pip install -r -
```

Verify:

```bash
.venv/bin/python -c "import tkinter; print('Tcl/Tk', tkinter.TkVersion)"
.venv/bin/python -c "import ctranslate2, faster_whisper, pyannote.audio; print('core OK')"
```

## 2. Models

- `precise` (Whisper large-v3-turbo, ~1.6 GB) is included in `models/precise/`
  and works out of the box — it is the default model.
- `fast` (int8 quantized, ~30 % faster on CPU) is optional. Its five files
  must lie **flat** in `models/fast/` (see `models/fast/NOSCRIBE_README.txt`).
  If the directory still contains the `faster-whisper-large-v3-turbo-int8/`
  subfolder, move the files up one level (see Troubleshooting).

noScribe registers a model only if its directory contains a `model.bin` file;
anything else is ignored with a "Missing model.bin" warning.

## 3. Run

GUI:

```bash
.venv/bin/python -m noScribe
```

Headless (no window), e.g. the first 10 minutes of a file with speaker
identification:

```bash
.venv/bin/python -m noScribe interview.m4a interview.html \
    --stop 0:10:00 --speaker-detection auto --language de
```

Common options: `--start HH:MM:SS`, `--stop HH:MM:SS`, `--language de` (or
auto-detect), `--speaker-detection none|auto|N`, `--timestamps` /
`--no-timestamps`, `--disfluencies` / `--no-disfluencies`, `--pause`,
`--model local-whisper:precise`, `--no-gui` (force headless). Output formats:
`.html`, `.txt`, `.vtt`.

## 4. Harmless warnings

- `torchcodec is not installed correctly ... FFmpeg` (pyannote): not a
  problem. noScribe feeds pyannote an in-memory waveform, so torchcodec's
  optional FFmpeg backend is never used.
- `SyntaxWarning: invalid escape sequence` from `AdvancedHTMLParser`:
  cosmetic, from a third-party package.

## 5. Troubleshooting

- **App segfaults (exit 139) during a job** — cross-thread Tk access. Fixed
  in this fork (thread guard in `update_queue_controls`). To verify that no
  other code path touches Tk from a background thread, start with
  `NOSCRIBE_TK_THREAD_CHECK=1 .venv/bin/python -m noScribe` (use `=strict` to
  raise instead of log).
- **`Missing model.bin in model dir: .../models/fast`** — the `fast` model
  files are not laid out flat. Move
  `models/fast/faster-whisper-large-v3-turbo-int8/{config.json,model.bin,preprocessor_config.json,tokenizer.json,vocabulary.json}`
  up one level (or download them per `models/fast/NOSCRIBE_README.txt`).
- **`ModuleNotFoundError: No module named '_tkinter'`** — you are using a
  Python without Tcl/Tk (e.g. Homebrew's). Recreate the venv with `uv`.
- **No Whisper models found** — see Models above; `models/precise/model.bin`
  must exist.
