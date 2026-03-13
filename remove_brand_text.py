#!/usr/bin/env python
from __future__ import annotations

import configparser
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterator, cast

import fitz

DEFAULT_CONFIG_NAME = "config.ini"
DEFAULT_ERROR_LOG_NAME = "last_run_errors.log"
LOG_MODES = {"minimal", "verbose"}
PAUSE_MODES = {"never", "error", "always"}


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else str(value)


def _iter_target_line_rects(
    page: fitz.Page,
    line_pattern: re.Pattern[str],
    exclude_pattern: re.Pattern[str] | None,
) -> Iterator[fitz.Rect]:
    text_dict = cast(dict[str, Any], page.get_text("dict"))
    blocks = text_dict.get("blocks", [])
    if not isinstance(blocks, list):
        return

    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != 0:
            continue

        lines = block.get("lines", [])
        if not isinstance(lines, list):
            continue

        for line in lines:
            if not isinstance(line, dict):
                continue

            spans = line.get("spans", [])
            if not isinstance(spans, list):
                continue

            line_text = "".join(
                _as_str(span.get("text", ""))
                for span in spans
                if isinstance(span, dict)
            )
            if not line_pattern.search(line_text):
                continue
            if exclude_pattern is not None and exclude_pattern.search(line_text):
                continue

            bbox = line.get("bbox")
            if bbox is None:
                continue
            try:
                yield fitz.Rect(bbox)
            except Exception:
                continue


def sanitize_pdf(
    src_path: Path,
    out_path: Path,
    line_pattern: re.Pattern[str],
    exclude_pattern: re.Pattern[str] | None,
) -> int:
    removed_lines = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with fitz.open(src_path) as doc:
        for page in doc:
            for rect in _iter_target_line_rects(page, line_pattern, exclude_pattern):
                page.add_redact_annot(rect, fill=None)
                removed_lines += 1
            page.apply_redactions(images=0, graphics=0, text=0)
        doc.save(out_path, garbage=4, clean=True, deflate=True)

    return removed_lines


def _literal_keyword_pattern(keyword: str) -> str:
    escaped = re.escape(keyword).replace(r"\ ", r"\s+")
    prefix = r"\b" if keyword and keyword[0].isalnum() else ""
    suffix = r"\b" if keyword and keyword[-1].isalnum() else ""
    return f"{prefix}{escaped}{suffix}"


def _parse_multiline_list(value: str) -> list[str]:
    items: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        items.append(line)
    return list(dict.fromkeys(items))


def _resolve_from_base(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _pause_if_needed(pause_mode: str, had_error: bool) -> None:
    if pause_mode == "always" or (pause_mode == "error" and had_error):
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass


def _load_config(config_file: Path) -> dict[str, Any] | None:
    if not config_file.exists():
        print(f"[ERROR] config file not found: {config_file}")
        return None

    parser = configparser.ConfigParser(interpolation=None)

    def _keep_option_case(optionstr: str) -> str:
        return optionstr

    parser.optionxform = _keep_option_case
    parser.read(config_file, encoding="utf-8")

    if "settings" not in parser:
        print("[ERROR] missing [settings] section in config file")
        return None

    settings = parser["settings"]
    input_dir_raw = settings.get("input_dir", "").strip()
    output_dir_raw = settings.get("output_dir", "").strip()
    prefix = settings.get("prefix", "").strip()
    literal_keywords_raw = settings.get("literal_keywords", "").strip()
    regex_keywords_raw = settings.get("regex_keywords", "").strip()
    exclude_literal_keywords_raw = settings.get("exclude_literal_keywords", "").strip()
    exclude_regex_keywords_raw = settings.get("exclude_regex_keywords", "").strip()
    legacy_keywords_raw = settings.get("keywords", "").strip()
    log_mode = settings.get("log_mode", "minimal").strip().lower()
    error_log_raw = settings.get("error_log", DEFAULT_ERROR_LOG_NAME).strip()
    pause_on_exit = settings.get("pause_on_exit", "error").strip().lower()

    if not input_dir_raw:
        print("[ERROR] 'input_dir' is empty in [settings]")
        return None
    if not output_dir_raw:
        print("[ERROR] 'output_dir' is empty in [settings]")
        return None
    literal_keywords = _parse_multiline_list(literal_keywords_raw)
    regex_keywords = _parse_multiline_list(regex_keywords_raw)

    # Backward compatibility with old combined `keywords` config.
    if not literal_keywords and not regex_keywords and legacy_keywords_raw:
        for keyword in _parse_multiline_list(legacy_keywords_raw):
            if keyword.lower().startswith("re:"):
                regex_body = keyword[3:].strip()
                if regex_body:
                    regex_keywords.append(regex_body)
            else:
                literal_keywords.append(keyword)

    if not literal_keywords and not regex_keywords:
        print(
            "[ERROR] both 'literal_keywords' and 'regex_keywords' are empty in [settings]"
        )
        return None

    exclude_literal_keywords = _parse_multiline_list(exclude_literal_keywords_raw)
    exclude_regex_keywords = _parse_multiline_list(exclude_regex_keywords_raw)

    if log_mode not in LOG_MODES:
        print("[ERROR] 'log_mode' must be 'minimal' or 'verbose' in [settings]")
        return None
    if pause_on_exit not in PAUSE_MODES:
        print(
            "[ERROR] 'pause_on_exit' must be 'never', 'error', or 'always' in [settings]"
        )
        return None
    if not error_log_raw:
        print("[ERROR] 'error_log' is empty in [settings]")
        return None

    base_dir = config_file.parent
    return {
        "input_dir": _resolve_from_base(input_dir_raw, base_dir),
        "output_dir": _resolve_from_base(output_dir_raw, base_dir),
        "prefix": prefix,
        "literal_keywords": list(dict.fromkeys(literal_keywords)),
        "regex_keywords": list(dict.fromkeys(regex_keywords)),
        "exclude_literal_keywords": list(dict.fromkeys(exclude_literal_keywords)),
        "exclude_regex_keywords": list(dict.fromkeys(exclude_regex_keywords)),
        "log_mode": log_mode,
        "error_log": _resolve_from_base(error_log_raw, base_dir),
        "pause_on_exit": pause_on_exit,
    }


def _validate_regex_rules(regex_rules: list[str], label: str) -> None:
    for idx, rule in enumerate(regex_rules, start=1):
        try:
            re.compile(rule, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"invalid {label} regex #{idx}: {rule!r} ({exc})") from exc


def _compile_pattern(
    literal_keywords: list[str], regex_keywords: list[str]
) -> re.Pattern[str]:
    parts: list[str] = []
    for keyword in literal_keywords:
        parts.append(_literal_keyword_pattern(keyword))
    for regex_body in regex_keywords:
        if regex_body:
            parts.append(f"(?:{regex_body})")

    if not parts:
        raise ValueError("rule list is empty")

    return re.compile("(?i)(?:" + "|".join(parts) + ")")


def main() -> int:
    pause_on_exit = "error"

    def _finish(code: int, had_error: bool) -> int:
        _pause_if_needed(pause_on_exit, had_error)
        return code

    config_file = _app_dir() / DEFAULT_CONFIG_NAME
    config = _load_config(config_file)
    if config is None:
        return _finish(1, True)

    input_dir = cast(Path, config["input_dir"])
    output_dir = cast(Path, config["output_dir"])
    prefix = cast(str, config["prefix"])
    literal_keywords = cast(list[str], config["literal_keywords"])
    regex_keywords = cast(list[str], config["regex_keywords"])
    exclude_literal_keywords = cast(list[str], config["exclude_literal_keywords"])
    exclude_regex_keywords = cast(list[str], config["exclude_regex_keywords"])
    log_mode = cast(str, config["log_mode"])
    error_log = cast(Path, config["error_log"])
    pause_on_exit = cast(str, config["pause_on_exit"])

    try:
        _validate_regex_rules(regex_keywords, "include")
        _validate_regex_rules(exclude_regex_keywords, "exclude")
        line_pattern = _compile_pattern(literal_keywords, regex_keywords)
        exclude_pattern = (
            _compile_pattern(exclude_literal_keywords, exclude_regex_keywords)
            if exclude_literal_keywords or exclude_regex_keywords
            else None
        )
    except ValueError as exc:
        print(f"[ERROR] {config_file}: {exc}")
        return _finish(1, True)
    except re.error as exc:
        print(f"[ERROR] failed to compile pattern: {exc}")
        return _finish(1, True)

    if not input_dir.exists():
        print(f"[ERROR] input directory not found: {input_dir}")
        return _finish(1, True)
    if not input_dir.is_dir():
        print(f"[ERROR] input path is not a directory: {input_dir}")
        return _finish(1, True)
    if output_dir.exists() and not output_dir.is_dir():
        print(f"[ERROR] output path is not a directory: {output_dir}")
        return _finish(1, True)
    if input_dir.resolve() == output_dir.resolve():
        print(f"[ERROR] input_dir and output_dir must be different: {input_dir}")
        return _finish(1, True)

    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"[ERROR] no PDF inputs found in: {input_dir}")
        return _finish(1, True)

    print(f"[START] config={config_file}")
    print(f"[START] input={input_dir} | output={output_dir} | prefix='{prefix}'")
    print(
        f"[START] files={len(pdfs)} | include(literal={len(literal_keywords)}, "
        f"regex={len(regex_keywords)}) | exclude(literal={len(exclude_literal_keywords)}, "
        f"regex={len(exclude_regex_keywords)}) | log_mode={log_mode}"
    )

    start = time.perf_counter()
    processed = 0
    ok_count = 0
    skip_count = 0
    err_count = 0
    total_removed_lines = 0
    error_lines: list[str] = []
    progress_len = 0

    def _render_progress() -> None:
        nonlocal progress_len
        elapsed = max(time.perf_counter() - start, 1e-9)
        rate = processed / elapsed
        percent = (processed / len(pdfs)) * 100
        msg = (
            f"[PROGRESS] {percent:5.1f}% {processed}/{len(pdfs)} | "
            f"ok {ok_count} skip {skip_count} err {err_count} | {rate:.1f} files/s"
        )
        print("\r" + msg.ljust(progress_len), end="", flush=True)
        progress_len = len(msg)

    for src in pdfs:
        processed += 1
        if prefix and src.name.startswith(prefix):
            skip_count += 1
            if log_mode == "verbose":
                print(f"[SKIP] {src.name} (already has prefix '{prefix}')")
            else:
                _render_progress()
            continue

        out_name = f"{prefix}{src.name}"
        out_path = output_dir / out_name
        try:
            removed_lines = sanitize_pdf(src, out_path, line_pattern, exclude_pattern)
        except Exception as exc:
            err_count += 1
            error_lines.append(f"{src.name}: {exc}")
            if log_mode == "verbose":
                print(f"[ERROR] {src.name} failed: {exc}")
            else:
                _render_progress()
            continue

        ok_count += 1
        total_removed_lines += removed_lines
        if log_mode == "verbose":
            print(f"[OK] {src.name} -> {out_name} | removed_lines={removed_lines}")
        else:
            _render_progress()

    if log_mode == "minimal":
        print()

    elapsed_total = time.perf_counter() - start

    if error_lines:
        error_log.parent.mkdir(parents=True, exist_ok=True)
        error_log.write_text("\n".join(error_lines) + "\n", encoding="utf-8")
    elif error_log.exists():
        try:
            error_log.unlink()
        except OSError:
            pass

    print(
        f"[DONE] files={len(pdfs)} | ok={ok_count} skip={skip_count} err={err_count} | "
        f"removed_lines={total_removed_lines} | elapsed={elapsed_total:.2f}s"
    )
    if error_lines:
        print(f"[DONE] error_log={error_log}")

    return _finish(0, err_count > 0)


if __name__ == "__main__":
    raise SystemExit(main())
