# pdf-redaction-helper

Config-driven PDF line redaction helper for repetitive compliance workflows.

pdf-redaction-helper is a practical batch utility for removing whole text lines from PDF files based on keyword rules.  
It is intended for repetitive cleanup tasks where the same kinds of lines must be identified and removed across many documents.

Rather than editing files manually one by one, this tool applies a rule-based workflow driven by `config.ini` and writes sanitized copies to a separate output folder.

## Overview

This project scans text lines in PDF pages and removes a whole line when:

- the line matches at least one **include** rule
- and the line does **not** match any **exclude** rule

It is designed for scenarios where the target content is consistent enough to be captured by literal keywords or regular expressions, and where batch processing is more useful than manual document cleanup.

## What this tool is for

This tool is useful when you need to:

- process many PDF files with the same cleanup rules
- keep the original files untouched
- maintain reusable matching rules in a config file
- run the same workflow again later with minimal manual effort

It is best understood as a workflow utility rather than a general-purpose PDF editor.

## What it does

- reads `config.ini` from the same directory as the script or packaged exe
- scans each text line in each PDF page
- removes the whole line when include rules match and exclude rules do not match
- writes sanitized PDFs to `output_dir`
- supports both literal keyword rules and regex keyword rules
- supports minimal or verbose terminal logging
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

1. Put the source PDF files into `input_dir`.
2. Edit `config.ini` to define input/output paths and matching rules.
3. Run the script or packaged exe.
4. Review the generated sanitized PDFs in `output_dir`.
5. Refine the rules if needed and run again.

This makes the tool suitable for repeated internal cleanup workflows where the matching logic may evolve over time.

## Quick Start (Python)

```powershell
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
input_dir=origin
output_dir=sanitized_output
prefix=sanitized_
log_mode=minimal
pause_on_exit=error
error_log=error.log

literal_keywords=Brand A|Brand B
regex_keywords=Company\s+Name|Document\s+Code
exclude_literal_keywords=Keep This Line
exclude_regex_keywords=Reference\s+Only
```

Notes:

- relative paths are resolved relative to `config.ini`
- the tool writes output files to a separate folder
- output file names can be prefixed to distinguish sanitized copies from originals

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
- the removal result depends on whether the target PDF text is extractable and consistently structured
- rule quality matters: poorly chosen keywords or regex patterns may remove too much or too little

For that reason, it is best used on known document patterns with reviewable output.

## Recommended repo hygiene

- do not commit business PDFs such as `origin/` or generated output folders
- do not commit build artifacts such as `build/`, `dist/`, or `__pycache__/`
- keep the repository focused on source code, config template, and docs

## Current status

This repository is currently positioned as a lightweight internal workflow tool.  
Its main value is not a complex algorithm, but the ability to turn repetitive PDF cleanup into a reusable and configurable batch process.
