#!/usr/bin/env python3
"""Auto-approve simple curl commands whose URLs are explicitly in active scopes."""

from __future__ import annotations

import json
import os
import posixpath
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import SplitResult, unquote, urlsplit


NO_ARG_LONG = {
    "--compressed",
    "--fail",
    "--fail-with-body",
    "--globoff",
    "--head",
    "--http1.0",
    "--http1.1",
    "--http2",
    "--http2-prior-knowledge",
    "--include",
    "--insecure",
    "--ipv4",
    "--ipv6",
    "--no-buffer",
    "--path-as-is",
    "--remote-name",
    "--show-error",
    "--silent",
    "--verbose",
}

ARG_LONG = {
    "--connect-timeout",
    "--cookie",
    "--cookie-jar",
    "--data",
    "--data-ascii",
    "--data-binary",
    "--data-raw",
    "--data-urlencode",
    "--form",
    "--form-string",
    "--header",
    "--json",
    "--max-time",
    "--output",
    "--request",
    "--retry",
    "--retry-delay",
    "--retry-max-time",
    "--upload-file",
    "--url",
    "--user",
    "--user-agent",
}

NO_ARG_SHORT = set("sSivkfgNO46I")
ARG_SHORT = set("XHdo mubcFTAm".replace(" ", ""))
UNSAFE_LONG = {
    "--cookie-jar",
    "--data",
    "--data-ascii",
    "--data-binary",
    "--data-raw",
    "--data-urlencode",
    "--form",
    "--form-string",
    "--header",
    "--json",
    "--output",
    "--remote-name",
    "--upload-file",
}
UNSAFE_SHORT = set("cdFHoT")


def project_dir() -> Path:
    configured = os.environ.get("CLAUDE_PROJECT_DIR")
    if configured:
        return Path(configured).resolve()
    return Path(__file__).resolve().parents[2]


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)", text
    )
    return match.group(1).strip() if match else ""


def active_scope_urls(root: Path) -> list[SplitResult]:
    approved: list[SplitResult] = []
    for scope_path in sorted((root / "cases").glob("*/SCOPE.md")):
        if scope_path.parent.name == "TEMPLATE":
            continue
        text = scope_path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"(?im)^\*\*Status:\*\*\s*ACTIVE\s*$", text):
            continue
        if not re.search(
            r"(?im)^\s*-\s*\[[xX]\]\s+Interactive analysis of the live application\s*$",
            text,
        ):
            continue
        authorization = section(text, "Authorization")
        if not authorization or "if this section is empty" in authorization.lower():
            continue
        for raw_url in re.findall(r"`(https?://[^`\s]+)`", section(text, "In scope")):
            parsed = urlsplit(raw_url.rstrip(".,;"))
            if parsed.scheme in {"http", "https"} and parsed.hostname:
                approved.append(parsed)
    return approved


def shell_words(command: str) -> list[str] | None:
    if "\n" in command or "\r" in command or "`" in command or "$(" in command:
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        words = list(lexer)
    except ValueError:
        return None
    if not words or any(word in {";", "&", "&&", "|", "||", "<", ">", "(", ")"} for word in words):
        return None
    if any("$" in word for word in words):
        return None
    return words


def curl_urls(command: str) -> list[str] | None:
    words = shell_words(command)
    if not words or Path(words[0]).name != "curl":
        return None

    urls: list[str] = []
    index = 1
    positional_only = False
    while index < len(words):
        word = words[index]
        if positional_only:
            urls.append(word)
            index += 1
            continue
        if word == "--":
            positional_only = True
            index += 1
            continue
        if word.startswith("--"):
            name, separator, attached = word.partition("=")
            if name in NO_ARG_LONG and not separator:
                if name in UNSAFE_LONG:
                    return None
                index += 1
                continue
            if name not in ARG_LONG:
                return None
            if separator:
                value = attached
            else:
                index += 1
                if index >= len(words):
                    return None
                value = words[index]
            if name in UNSAFE_LONG:
                return None
            if name == "--request" and value.upper() not in {"GET", "HEAD"}:
                return None
            if name == "--url":
                urls.append(value)
            index += 1
            continue
        if word.startswith("-") and word != "-":
            chars = word[1:]
            offset = 0
            while offset < len(chars):
                option = chars[offset]
                if option in NO_ARG_SHORT:
                    if option in UNSAFE_SHORT or option == "O":
                        return None
                    offset += 1
                    continue
                if option not in ARG_SHORT:
                    return None
                if offset + 1 < len(chars):
                    value = chars[offset + 1 :]
                else:
                    index += 1
                    if index >= len(words):
                        return None
                    value = words[index]
                if option in UNSAFE_SHORT:
                    return None
                if option == "X" and value.upper() not in {"GET", "HEAD"}:
                    return None
                offset = len(chars)
                # Curl's short options do not include a safe URL-bearing equivalent
                # of --url, so the consumed value is deliberately ignored here.
                _ = value
            index += 1
            continue
        urls.append(word)
        index += 1
    return urls or None


def effective_port(url: SplitResult) -> int:
    if url.port is not None:
        return url.port
    return 443 if url.scheme == "https" else 80


def normalized_path(path: str) -> str | None:
    decoded = unquote(path or "/")
    if "\\" in decoded or "\x00" in decoded:
        return None
    normalized = posixpath.normpath(decoded)
    if decoded.endswith("/") and normalized != "/":
        normalized += "/"
    return normalized


def url_is_within(candidate: str, approved: list[SplitResult]) -> bool:
    if any(character in candidate for character in "{}"):
        return False
    try:
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        candidate_port = effective_port(parsed)
        candidate_path = normalized_path(parsed.path)
        if candidate_path is None:
            return False
    except ValueError:
        return False

    for allowed in approved:
        try:
            same_origin = (
                parsed.scheme == allowed.scheme
                and parsed.hostname.lower() == allowed.hostname.lower()
                and candidate_port == effective_port(allowed)
            )
        except ValueError:
            continue
        base_path = normalized_path(allowed.path)
        if base_path is None:
            continue
        path_matches = (
            base_path == "/"
            or candidate_path == base_path
            or candidate_path.startswith(base_path.rstrip("/") + "/")
        )
        if same_origin and path_matches:
            return True
    return False


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    command = event.get("tool_input", {}).get("command")
    if not isinstance(command, str):
        return 0

    urls = curl_urls(command)
    approved = active_scope_urls(project_dir())
    if urls and approved and all(url_is_within(url, approved) for url in urls):
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "allow"},
                }
            },
            sys.stdout,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
