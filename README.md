# pdf-redaction-helper

Config-driven PDF line redaction helper for repetitive document cleanup workflows.

pdf-redaction-helper is a practical batch utility for removing whole text lines from PDF files based on reusable keyword rules.

It is designed for situations where the same kinds of lines need to be removed from many documents repeatedly. Instead of opening files one by one and editing them manually, this tool applies rule-based cleanup driven by `config.ini` and writes sanitized copies to a separate output folder.

## Overview

The tool scans extracted text lines in PDF pages and removes a whole line only when:

- the line matches at least one **include** rule
- and the line does **not** match any **exclude** rule

This makes it suitable for stable, repeatable document patterns where literal keywords or regular expressions can describe the cleanup target.

## What this tool is for

Use this tool when you need to:

- process many PDF files with the same cleanup rules
- keep the original files untouched
- reuse the same matching logic later
- turn a repetitive manual task into a configurable batch workflow

It should be understood as a workflow utility, not a general-purpose PDF editor.

## Core behavior

- reads `config.ini` from the same directory as the script or packaged exe
- scans each text line in each PDF page
- removes the whole line when include rules match and exclude rules do not match
- writes sanitized PDFs to `output_dir`
- supports both literal keyword rules and regex keyword rules
- supports `minimal` or `verbose` terminal logging
- continues processing even if individual files fail

## Rule logic

A line is removed only when all of the following are true:

1. it matches at least one include rule
2. it does not match any exclude rule

Supported rule groups:

- `literal_keywords`
- `regex_keywords`
- `exclude_literal_keywords`
- `exclude_regex_keywords`

Notes:

- regex matching is case-insensitive by default
- `\s+` means one or more spaces
- `\s*` means optional spaces

## Typical workflow

1. Put source PDF files into `input_dir`.
2. Edit `config.ini` to define input/output paths and matching rules.
3. Run the script or packaged exe.
4. Review the generated sanitized PDFs in `output_dir`.
5. Refine the rules if needed and run again.

This makes the tool useful for repeated internal cleanup tasks where rules may gradually improve over time.

## Quick Start (Python)

```powershell
pip install -r requirements.txt
python pdf_redaction_helper.py
```

## Config

Edit `config.ini`:

- `input_dir`: input PDF folder
- `output_dir`: output PDF folder; must be different from input
- `prefix`: output filename prefix; can be empty
- `log_mode`: `minimal` or `verbose`
- `pause_on_exit`: `never`, `error`, or `always`
- `error_log`: error log path
- `literal_keywords`: plain-text include rules
- `regex_keywords`: regex include rules
- `exclude_literal_keywords`: plain-text exclude rules
- `exclude_regex_keywords`: regex exclude rules

### Example config

```ini
[settings]
input_dir=origin
output_dir=sanitized_output
prefix=sanitized_
log_mode=minimal
pause_on_exit=error
error_log=error.log

literal_keywords=
  Brand A
  Brand B
regex_keywords=
  Company\s+Name
  Document\s+Code
exclude_literal_keywords=
  Keep This Line
exclude_regex_keywords=
  Reference\s+Only
```

Notes:

- relative paths are resolved relative to `config.ini`
- output is written to a separate folder
- filename prefixes can help distinguish sanitized copies from originals

## Example run

```text
[START] config=config.ini
[START] input=origin | output=sanitized_origin | prefix=sanitized_
[START] files=564 | include(literal=4, regex=3) | exclude(literal=0, regex=0) | log_mode=minimal
[PROGRESS] 100.0% 564/564 | ok 564 skip 0 err 0 | 29.3 files/s
[DONE] files=564 | ok=564 skip=0 err=0 | removed_lines=5694 | elapsed=19.27s
```

## Build Onedir EXE

```powershell
python -m PyInstaller --noconfirm --clean --onedir --name pdf_redaction pdf_redaction_helper.py
Copy-Item -Force config.ini dist\pdf_redaction\config.ini
```

Run:

```powershell
.\dist\pdf_redaction\pdf_redaction.exe
```

## Safety defaults

- `input_dir == output_dir` is blocked
- per-file failures do not stop the full batch
- in `minimal` mode, the terminal shows startup summary, one-line progress, and final summary

## Limitations

- this tool works on extracted PDF text lines; it is not a full visual redaction editor
- results depend on whether the target PDF text is extractable and consistently structured
- poorly chosen keywords or regex patterns may remove too much or too little

For that reason, it is best used on known document patterns with reviewable output.

## Repository scope

This repository is intentionally lightweight. Its value is not a complex algorithm, but the ability to turn repetitive PDF cleanup into a reusable and configurable batch process.

## Recommended repo hygiene

- do not commit business PDFs such as `origin/` or generated output folders
- do not commit build artifacts such as `build/`, `dist/`, or `__pycache__/`
- keep the repository focused on source code, config templates, and docs
