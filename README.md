# pdf-redaction-helper

A simple internal tool to remove whole text lines in PDF files based on keyword rules.

## What It Does

- Reads `config.ini` from the same directory as script/exe.
- Scans each text line in each PDF page.
- Removes the whole line when:
  - It matches include rules (`literal_keywords` or `regex_keywords`), and
  - It does NOT match exclude rules (`exclude_literal_keywords` or `exclude_regex_keywords`).
- Writes sanitized PDFs to `output_dir`.

## Quick Start (Python)

```powershell
python remove_brand_text.py
```

## Config

Edit [config.ini](./config.ini):

- `input_dir`: input PDF folder
- `output_dir`: output PDF folder (must be different from input)
- `prefix`: output filename prefix (can be empty)
- `log_mode`: `minimal` or `verbose`
- `pause_on_exit`: `never`, `error`, or `always`
- `error_log`: error log path
- `literal_keywords`: plain text include rules
- `regex_keywords`: regex include rules
- `exclude_literal_keywords`: plain text exclude rules
- `exclude_regex_keywords`: regex exclude rules

Notes:

- Relative paths are resolved relative to `config.ini`.
- Regex is case-insensitive by default.
- `\s+` means one or more spaces; `\s*` means optional spaces.

## Build Onedir EXE

```powershell
python -m PyInstaller --noconfirm --clean --onedir --name pdf_sanitizer --add-data "config.ini;." remove_brand_text.py
Copy-Item -Force config.ini dist\pdf_sanitizer\config.ini
```

Run:

```powershell
.\dist\pdf_sanitizer\pdf_sanitizer.exe
```

## Safety Defaults

- `input_dir == output_dir` is blocked.
- Per-file failures do not stop the full batch.
- In `minimal` mode, terminal shows startup summary + one-line progress + final summary.

## Recommended Repo Hygiene

- Do not commit business PDFs (`origin/`, output folders).
- Do not commit build artifacts (`build/`, `dist/`, `__pycache__/`).
- Keep only source code, config template, and docs.
