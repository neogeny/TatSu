# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .config import CLIConfig, CLIError
from .fmt import colorize_output


def output_results(cfg: CLIConfig, results: list[tuple[str, Any]]) -> None:
    out_path = Path(cfg.output) if cfg.output else None
    if not results:
        return

    # Directory output: each input gets its own .json file
    if out_path and (
        str(cfg.output).rstrip().endswith((os.sep, "/")) or out_path.is_dir()
    ):
        out_path.mkdir(parents=True, exist_ok=True)
        ext = _output_ext(cfg)
        for input_path, single_payload in results:
            name = Path(input_path).stem
            out = (out_path / name).with_suffix(ext)
            _show(single_payload, out)
        return

    # JSONL for multiple input files (JSON is the default format)
    # Skip JSONL when output is to a TTY — use indented JSON instead.
    if cfg.json_lines or (
        (not cfg.model or cfg.json)
        and len(results) > 1
        and not (not cfg.output and sys.stdout.isatty())
    ):
        import json

        jsonl = "\n".join(
            json.dumps(
                {"input": input_path, "result": json.loads(outcome)},
                separators=(",", ":"),
            )
            for input_path, outcome in results
        )
        _show(jsonl, _output_path(cfg))
        return

    # Single result or model output: write sequentially
    single_out = _output_path(cfg)
    should_colorize = (
        not cfg.json_lines
        and not cfg.railroads
        and cfg.usecolor()
        and single_out is None
    )

    language = "json"
    if cfg.model:
        language = "python"
    elif cfg.pretty:
        language = "ebnf"

    payloads = [payload for _, payload in results]
    if should_colorize:
        payloads = [
            colorize_output(payload, language, cfg.style) for payload in payloads
        ]

    single_payload = "\n".join(payloads)
    if single_out is None:
        print(single_payload)
    else:
        _make_output_dir(single_out).write_text(single_payload)


def _output_ext(cfg: CLIConfig) -> str:
    """Return file extension for the current output format."""
    if cfg.model:
        return ".py"
    if cfg.railroads:
        return ".railroads.txt"
    if cfg.pretty:
        return ".ebnf"
    return ".json"


def _output_path(cfg: CLIConfig, *, name: str | None = None) -> Path | None:
    """Return output path, or None for stdout.

    If cfg.output is a directory, appends *name* (with format extension).
    Otherwise returns the file path.
    """
    if not cfg.output:
        return None
    out = Path(cfg.output)
    if out.is_dir():
        if name is None:
            return None
        return out / (name + _output_ext(cfg))
    return out


def _make_output_dir(path: Path | str) -> Path:
    """Ensure the output directory exists and return the path."""
    path = Path(path)
    dir = path.parent
    if dir.exists() and not dir.is_dir():
        raise CLIError(f"Output path exists but it's not a directory: {dir!s}")
    try:
        dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise CLIError(f"Failed to create output directory: {e!s}") from e
    return path


def _show(payload: str, output: Path | None) -> None:
    """Write payload to a file or stdout."""
    if output is None:
        print(payload)
    else:
        _make_output_dir(output).write_text(payload)
